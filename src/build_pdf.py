"""
Markdown -> PDF renderer for reports/*.md, using reportlab Platypus.

Covers only the markdown subset these reports use: headings, tables,
bold/italic, horizontal rules and bullet lists.

Usage: python -m src.build_pdf
"""
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reportlab import rl_config

# Reproducible build: without this reportlab stamps a wall-clock CreationDate
# and a random document ID into every PDF, so two builds of identical inputs
# differ in bytes and CI cannot check the committed reports against a rebuild.
rl_config.invariant = 1
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, KeepTogether)
from reportlab.pdfbase.pdfmetrics import stringWidth

from src.config import REPORTS

ACCENT = colors.HexColor("#1F6EA6")   # deep sky, matches the charts/dashboard
LGREY = colors.HexColor("#F2F2F2")
DGREY = colors.HexColor("#6B7280")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16,
                          textColor=ACCENT, spaceBefore=2, spaceAfter=6,
                          fontName="Helvetica-Bold", keepWithNext=1))
styles.add(ParagraphStyle("H1Sub", parent=styles["Normal"], fontSize=9.5,
                          textColor=DGREY, fontName="Helvetica-Oblique",
                          spaceAfter=10, keepWithNext=1))
styles.add(ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12.5,
                          textColor=ACCENT, spaceBefore=11, spaceAfter=5,
                          fontName="Helvetica-Bold", keepWithNext=1))
styles.add(ParagraphStyle("H3", parent=styles["Heading3"], fontSize=11,
                          textColor=ACCENT, spaceBefore=8, spaceAfter=4,
                          fontName="Helvetica-Bold", keepWithNext=1))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.3,
                          leading=12.4, spaceAfter=5, alignment=TA_LEFT,
                          allowWidows=0, allowOrphans=0))
styles.add(ParagraphStyle("BodyBold", parent=styles["Body"],
                          fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("BulletItem", parent=styles["Body"], leftIndent=14,
                          bulletIndent=4, spaceAfter=3))
styles.add(ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8.3,
                          leading=10.6, alignment=TA_LEFT))
styles.add(ParagraphStyle("CellHead", parent=styles["Cell"],
                          fontName="Helvetica-Bold", textColor=colors.white))
styles.add(ParagraphStyle("Small", parent=styles["Normal"], fontSize=8,
                          textColor=DGREY, fontName="Helvetica-Oblique",
                          spaceAfter=6, leading=11))
styles.add(ParagraphStyle("Quote", parent=styles["Body"], leftIndent=12,
                          textColor=DGREY, fontName="Helvetica-Oblique",
                          borderColor=DGREY, spaceAfter=8))


# Base Helvetica has no glyph for these and reportlab substitutes a
# lookalike instead of erroring, so map them to ASCII before rendering.
UNICODE_SAFE = {
    "→": "->",
    "≈": "~",
    "×": " x ",
    "–": "-",
    "—": " - ",
    "−": "-",
    "‑": "-",
    "’": "'", "‘": "'", '“': '"', '”': '"',
    "…": "...",
}


def inline(text):
    """Markdown inline -> reportlab mini-XML. Order matters: bold before italic."""
    # External links stay clickable; relative repo paths render as plain
    # text, since a standalone PDF can't resolve them.
    def _link_sub(m):
        label, href = m.group(1), m.group(2)
        if href.startswith(("http://", "https://")):
            return f"\x00LINKSTART\x00{href}\x00LINKMID\x00{label}\x00LINKEND\x00"
        return label
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link_sub, text)

    for bad, good in UNICODE_SAFE.items():
        text = text.replace(bad, good)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+?)`", r'<font face="Courier">\1</font>', text)
    text = re.sub(r"\s{2,}", " ", text)  # cleanup from " x " substitution

    def _restore_link(m):
        href, label = m.group(1), m.group(2)
        return f'<link href="{href}" color="#1F6EA6"><u>{label}</u></link>'
    text = re.sub(r"\x00LINKSTART\x00(.*?)\x00LINKMID\x00(.*?)\x00LINKEND\x00",
                  _restore_link, text)
    return text


def parse_table(lines, i):
    """Parse a GFM table starting at lines[i]. Returns (rows, next_index)."""
    rows = []
    header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
    rows.append(header)
    i += 2  # skip header + separator
    while i < len(lines) and lines[i].strip().startswith("|"):
        row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        rows.append(row)
        i += 1
    return rows, i


def make_table(rows, avail_width):
    # A blank or near-blank markdown header row would render as an empty
    # filled bar, so drop it and treat the rest as data.
    if rows and all(not c.strip() for c in rows[0]):
        rows = rows[1:]
        has_header = False
    elif rows and sum(1 for c in rows[0] if c.strip()) == 1 and len(rows[0]) > 1:
        has_header = False
    else:
        has_header = True
    if not rows:
        return Spacer(1, 0)

    ncols = len(rows[0])
    body_start = 1 if has_header else 0
    # Right-align columns whose header or majority of data cells look numeric.
    def is_numeric_col(c):
        vals = [rows[r][c] for r in range(body_start, len(rows)) if c < len(rows[r])]
        hits = sum(1 for v in vals if re.match(r"^[\$\-\(]?[\d,\.]+[%\)]?x?$|^[+\-]?[\d,\.]+%?$", v.replace(",", "").replace(" ", "")) or v in ("—", "-", ""))
        return hits >= max(1, len(vals) * 0.6)

    numeric_cols = [is_numeric_col(c) for c in range(ncols)]
    first_col_width = min(avail_width * 0.32, 2.5 * inch)
    remaining = avail_width - first_col_width
    other_width = remaining / max(1, ncols - 1)
    col_widths = [first_col_width] + [other_width] * (ncols - 1)

    data = []
    for r, row in enumerate(rows):
        cells = []
        for c in range(ncols):
            val = row[c] if c < len(row) else ""
            style = styles["CellHead"] if (has_header and r == 0) else styles["Cell"]
            p = Paragraph(inline(val), style)
            cells.append(p)
        data.append(cells)

    for row_paras in data:
        for p in row_paras:
            p.style.leading = p.style.fontSize + 1.6
    t = Table(data, colWidths=col_widths, repeatRows=1 if has_header else 0)
    ts = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if has_header:
        ts += [
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    first_body = 1 if has_header else 0
    for r in range(first_body, len(data)):
        if (r - first_body) % 2 == 1:
            ts.append(("BACKGROUND", (0, r), (-1, r), LGREY))
        # bold rows: a row whose first cell is bold-marked in source (**...**)
        if rows[r][0].strip().startswith("**"):
            ts.append(("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"))
    for c in range(ncols):
        if numeric_cols[c] and c > 0:
            ts.append(("ALIGN", (c, first_body), (c, -1), "RIGHT"))
    t.setStyle(TableStyle(ts))
    return t


def build_story(md_text, avail_width):
    lines = md_text.split("\n")
    story = []
    i = 0
    n = len(lines)
    first_h1_done = False

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("### "):
            story.append(Paragraph(inline(stripped[4:]), styles["H3"]))
            i += 1
            continue
        if stripped.startswith("## "):
            story.append(Paragraph(inline(stripped[3:]), styles["H2"]))
            i += 1
            continue
        if stripped.startswith("# "):
            story.append(Paragraph(inline(stripped[2:]), styles["H1"]))
            first_h1_done = True
            i += 1
            continue

        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            story.append(Paragraph(inline(" ".join(buf)), styles["Quote"]))
            story.append(Spacer(1, 4))
            continue

        if stripped.startswith("---") and set(stripped) <= {"-"}:
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=0.6,
                                    color=colors.HexColor("#D9D9D9")))
            story.append(Spacer(1, 8))
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < n and re.match(r"^\|?[\s:\-\|]+\|?$", lines[i + 1].strip()):
            rows, i = parse_table(lines, i)
            tbl = make_table(rows, avail_width)
            # Keep a table whole rather than letting it straddle a page break.
            story.append(Spacer(1, 2))
            story.append(KeepTogether([tbl]))
            story.append(Spacer(1, 6))
            continue

        if stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**") and stripped.count("*") == 2:
            story.append(Paragraph(inline(stripped[1:-1]), styles["Small"]))
            i += 1
            continue

        if re.match(r"^(\d+\.|[-*])\s+", stripped):
            marker = re.match(r"^(\d+\.|[-*])\s+", stripped).group(1)
            buf = [re.sub(r"^(\d+\.|[-*])\s+", "", stripped)]
            i += 1
            # Absorb continuation lines so a wrapped bullet stays one item.
            while i < n and lines[i].strip() and not (
                lines[i].strip().startswith(("#", "|"))
                or re.match(r"^(\d+\.|[-*])\s+", lines[i].strip())
            ):
                buf.append(lines[i].strip())
                i += 1
            bullet_text = " ".join(buf)
            # U+2022 has no glyph in base Helvetica; use an ASCII marker.
            bullet_char = marker if marker[0].isdigit() else "-"
            story.append(Paragraph(f"{bullet_char}&nbsp;&nbsp;{inline(bullet_text)}",
                                   styles["BulletItem"]))
            continue

        # Paragraph: accumulate to the next blank or structural line. The
        # trailing space in the list pattern matters -- it stops a line that
        # merely opens with "**bold**" from being read as a bullet.
        buf = [stripped]
        i += 1
        while i < n and lines[i].strip() and not (
            lines[i].strip().startswith(("#", "|"))
            or re.match(r"^(\d+\.|[-*])\s+", lines[i].strip())
        ):
            buf.append(lines[i].strip())
            i += 1
        text = " ".join(buf)
        story.append(Paragraph(inline(text), styles["Body"]))

    return story


HEADING_STYLES = {"H1", "H2", "H3", "H1Sub"}


def group_headings(story):
    """A heading must never be stranded as the last item on a page. Every
    heading style already sets keepWithNext=1, which tells reportlab's layout
    engine directly not to break the page immediately after that paragraph —
    if the next flowable doesn't fit in the remaining space, the heading
    itself moves down too. This is deliberately NOT implemented by wrapping
    heading+content in a manual KeepTogether: nesting a KeepTogether around a
    table that is already wrapped in its own KeepTogether (see build_story)
    made reportlab's height estimate for the outer group unreliable, which
    produced a near-empty page followed by everything else on the next one —
    exactly the defect this function exists to prevent. keepWithNext alone,
    with no nesting, is the correct fix and is a no-op pass-through here."""
    return story


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D9D9D9"))
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 0.45 * inch,
                LETTER[0] - doc.rightMargin, 0.45 * inch)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(DGREY)
    canvas.drawString(doc.leftMargin, 0.30 * inch, doc.title)
    canvas.drawRightString(LETTER[0] - doc.rightMargin, 0.30 * inch,
                           f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def _scale_styles(factor):
    """Uniformly scale every style's font size and leading. Used to fit the
    executive summary onto a single page without hand-tuning each style."""
    for name in ("H1", "H1Sub", "H2", "H3", "Body", "BodyBold", "BulletItem",
                 "Cell", "CellHead", "Small"):
        st = styles[name]
        st.fontSize = round(st.fontSize * factor, 2)
        st.leading = round(st.leading * factor, 2)
        for attr in ("spaceBefore", "spaceAfter"):
            setattr(st, attr, round(getattr(st, attr) * factor, 2))


def render(md_path, pdf_path, title, max_pages=None, min_scale=0.80):
    """Render markdown to PDF. If max_pages is set, progressively tighten
    typography (down to min_scale) to fit — the executive summary is meant to
    be a one-pager, and spilling four lines onto a near-empty second page
    looks worse than setting it slightly tighter."""
    text = Path(md_path).read_text()
    scale, applied = 1.0, 1.0

    while True:
        if scale != applied:                    # apply the delta since last pass
            _scale_styles(scale / applied)
            applied = scale
        doc = SimpleDocTemplate(
            str(pdf_path), pagesize=LETTER,
            topMargin=0.55 * inch, bottomMargin=0.62 * inch,
            leftMargin=0.7 * inch, rightMargin=0.7 * inch,
            title=title,
        )
        avail_width = LETTER[0] - doc.leftMargin - doc.rightMargin
        story = group_headings(build_story(text, avail_width))
        n_flowables = len(story)                # build() consumes the list
        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
        pages = doc.page

        if max_pages is None or pages <= max_pages or scale <= min_scale:
            break
        scale = round(max(min_scale, scale - 0.03), 2)

    _scale_styles(1.0 / applied)                # restore for the next document
    note = f", scaled to {applied:.2f}" if applied != 1.0 else ""
    print(f"Wrote {pdf_path}  ({n_flowables} flowables, {pages} page(s){note})")


def main():
    ROOT = REPORTS.parent
    # The exec summary is a one-pager by design; let it tighten to fit.
    render(REPORTS / "00_EXECUTIVE_SUMMARY.md", REPORTS / "00_EXECUTIVE_SUMMARY.pdf",
          "Unit Economics: CAC, LTV & Cross-Sell Propensity — Executive Summary", max_pages=1)
    # The memo runs as long as it needs to, at full size.
    render(REPORTS / "01_RECOMMENDATION_MEMO.md", REPORTS / "01_RECOMMENDATION_MEMO.pdf",
          "Unit Economics: CAC, LTV & Cross-Sell Propensity — Recommendation Memo")
    # README as a standalone project overview PDF.
    render(ROOT / "README.md", REPORTS / "README.pdf",
          "Unit Economics: CAC, LTV & Cross-Sell Propensity — Project Overview",
          max_pages=2)


if __name__ == "__main__":
    main()
