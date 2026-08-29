"""
Part D -- Cross-sell propensity model (next-best-product).

Uses the Santander Product Recommendation dataset: ~13M customer-month rows,
Jan 2015 - May 2016, 24 financial-product ownership flags per customer per
month. Olist's own customers are 97% one-time buyers, so they can't support
a product-holding transition model; this is a second dataset chosen for that
specific gap.

Task: for a customer active in month t who does not yet own product X,
predict whether they add product X by month t+1. Trained per product on an
out-of-time split -- earlier months train, later months test, never a random
split on a time-ordered panel.
"""
import glob
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from config import SANTANDER, FINAL, TABLES

PRODUCT_COLS = [
    "ind_ahor_fin_ult1", "ind_aval_fin_ult1", "ind_cco_fin_ult1", "ind_cder_fin_ult1",
    "ind_cno_fin_ult1", "ind_ctju_fin_ult1", "ind_ctma_fin_ult1", "ind_ctop_fin_ult1",
    "ind_ctpp_fin_ult1", "ind_deco_fin_ult1", "ind_deme_fin_ult1", "ind_dela_fin_ult1",
    "ind_ecue_fin_ult1", "ind_fond_fin_ult1", "ind_hip_fin_ult1", "ind_plan_fin_ult1",
    "ind_pres_fin_ult1", "ind_reca_fin_ult1", "ind_tjcr_fin_ult1", "ind_valo_fin_ult1",
    "ind_viv_fin_ult1", "ind_nomina_ult1", "ind_nom_pens_ult1", "ind_recibo_ult1",
]

KEEP_COLS = ["fecha_dato", "ncodpers", "age", "antiguedad", "renta",
             "ind_actividad_cliente", "canal_entrada", "segmento", "sexo"] + PRODUCT_COLS

TRAIN_END = "2016-02-28"   # train on transitions up to here
TEST_START = "2016-03-28"  # evaluate on transitions from here onward (out-of-time)

N_CUSTOMERS_SAMPLE = 120_000  # scope decision: full panel is ~950k customers;
                               # 120k random customers keeps this laptop-tractable
                               # while preserving month-level transition rates.


def load_panel():
    files = sorted(glob.glob(str(SANTANDER / "parquet_files" / "*.parquet")))
    parts = []
    for f in files:
        d = pd.read_parquet(f, columns=KEEP_COLS)
        parts.append(d)
    panel = pd.concat(parts, ignore_index=True)

    for c in PRODUCT_COLS:
        panel[c] = pd.to_numeric(panel[c], errors="coerce").fillna(0).astype("int8")
    panel["ncodpers"] = pd.to_numeric(panel["ncodpers"], errors="coerce")
    panel = panel.dropna(subset=["ncodpers"])
    panel["ncodpers"] = panel["ncodpers"].astype("int64")
    panel["fecha_dato"] = pd.to_datetime(panel["fecha_dato"])

    rng = np.random.default_rng(42)
    all_ids = panel["ncodpers"].unique()
    if len(all_ids) > N_CUSTOMERS_SAMPLE:
        sample_ids = rng.choice(all_ids, size=N_CUSTOMERS_SAMPLE, replace=False)
        panel = panel[panel["ncodpers"].isin(sample_ids)]

    panel = panel.sort_values(["ncodpers", "fecha_dato"])
    panel.to_parquet(FINAL / "santander_panel_sample.parquet", index=False)
    return panel


def build_transitions(panel):
    """One row per (customer, month_t, product): 1 if customer added that
    product by month_t+1, given they didn't have it at month_t. Only rows
    where a customer has a valid *next* month (t and t+1 both observed) are
    kept -- this is the actual transition modelling population."""
    panel = panel.copy()
    panel["month_idx"] = panel.groupby("ncodpers")["fecha_dato"].rank(method="dense").astype(int)
    nxt = panel[["ncodpers", "fecha_dato"] + PRODUCT_COLS].copy()
    nxt["fecha_dato"] = nxt["fecha_dato"] - pd.DateOffset(months=1)
    nxt = nxt.rename(columns={c: f"{c}_next" for c in PRODUCT_COLS})

    merged = panel.merge(nxt, on=["ncodpers", "fecha_dato"], how="inner")
    return merged


def train_and_score(merged):
    merged["canal_entrada"] = merged["canal_entrada"].fillna("UNK").astype("category").cat.codes
    merged["segmento"] = merged["segmento"].fillna("UNK").astype("category").cat.codes
    merged["sexo"] = merged["sexo"].fillna("UNK").astype("category").cat.codes
    def clean_numeric(series, default=0.0):
        s = pd.to_numeric(series, errors="coerce")
        fill_val = s.median() if s.notna().any() else default
        return s.fillna(fill_val)

    merged["renta"] = clean_numeric(merged["renta"])
    merged["age"] = clean_numeric(merged["age"], default=40)
    merged["antiguedad"] = clean_numeric(merged["antiguedad"])
    merged["ind_actividad_cliente"] = clean_numeric(merged["ind_actividad_cliente"])

    feature_cols = ["age", "antiguedad", "renta", "ind_actividad_cliente",
                     "canal_entrada", "segmento", "sexo"] + PRODUCT_COLS

    train = merged[merged.fecha_dato <= TRAIN_END]
    test = merged[merged.fecha_dato >= TEST_START]

    results = []
    all_test_scores = []
    for prod in PRODUCT_COLS:
        target_col = f"{prod}_next"
        # eligible = doesn't already own the product this month
        tr = train[train[prod] == 0]
        te = test[test[prod] == 0]
        if tr[target_col].sum() < 30 or te[target_col].sum() < 5:
            continue  # too rare to model reliably -- skip, don't fabricate a score

        X_tr, y_tr = tr[feature_cols].values, tr[target_col].values
        X_te, y_te = te[feature_cols].values, te[target_col].values

        scaler = StandardScaler()
        X_tr_s = scaler.fit_transform(X_tr)
        X_te_s = scaler.transform(X_te)

        clf = LogisticRegression(max_iter=500, class_weight="balanced")
        clf.fit(X_tr_s, y_tr)
        proba_te = clf.predict_proba(X_te_s)[:, 1]

        auc = roc_auc_score(y_te, proba_te)
        results.append({
            "product": prod, "train_positives": int(y_tr.sum()), "train_n": len(y_tr),
            "test_positives": int(y_te.sum()), "test_n": len(y_te), "test_auc": auc,
        })

        scored = te[["ncodpers", "fecha_dato"]].copy()
        scored["product"] = prod
        scored["propensity"] = proba_te
        all_test_scores.append(scored)

    results_df = pd.DataFrame(results).sort_values("test_auc", ascending=False)
    results_df.round(4).to_csv(TABLES / "propensity_model_performance.csv", index=False)

    scores_df = pd.concat(all_test_scores, ignore_index=True)
    # ranked cross-sell list: top-3 next-best-product per customer, latest test month
    latest = scores_df[scores_df.fecha_dato == scores_df.fecha_dato.max()]
    ranked = (latest.sort_values(["ncodpers", "propensity"], ascending=[True, False])
                      .groupby("ncodpers").head(3))
    # Full ranked list -> data/final (gitignored, reproducible by re-running this
    # script). A genuine small sample -> outputs/tables (committed).
    ranked.to_parquet(FINAL / "cross_sell_ranked_list_full.parquet", index=False)
    sample_ids = ranked["ncodpers"].drop_duplicates().sample(
        n=min(300, ranked["ncodpers"].nunique()), random_state=42)
    ranked[ranked["ncodpers"].isin(sample_ids)].to_csv(
        TABLES / "cross_sell_ranked_list_sample.csv", index=False)

    return results_df, ranked


if __name__ == "__main__":
    print("Loading panel (this samples 120k of ~950k customers, all 17 months)...")
    panel = load_panel()
    print(f"Panel shape: {panel.shape}")
    merged = build_transitions(panel)
    print(f"Transition rows: {merged.shape}")
    results_df, ranked = train_and_score(merged)
    print(results_df)
    print()
    print(f"Ranked cross-sell list sample rows: {len(ranked)}")
