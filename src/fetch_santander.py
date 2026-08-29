"""One-time fetch of the Santander product-holding panel via the Kaggle API.
Requires a free Kaggle account and API token (~/.kaggle/kaggle.json) -- see
https://www.kaggle.com/settings/api. Run this once before propensity.py."""
import subprocess
import zipfile
from pathlib import Path
from config import SANTANDER

DATASET = "padmanabhanporaiyar/santander-product-recommendation-parquet-data"


def fetch():
    SANTANDER.mkdir(parents=True, exist_ok=True)
    zip_path = SANTANDER / "santander-product-recommendation-parquet-data.zip"
    if not (SANTANDER / "parquet_files").exists():
        subprocess.run(
            ["kaggle", "datasets", "download", "-d", DATASET, "-p", str(SANTANDER)],
            check=True,
        )
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(SANTANDER)
        # the uploader's zip has a typo'd folder name ("paraquet files")
        typo_dir = SANTANDER / "paraquet files"
        if typo_dir.exists():
            typo_dir.rename(SANTANDER / "parquet_files")
        print("Santander data fetched to", SANTANDER / "parquet_files")
    else:
        print("Already present at", SANTANDER / "parquet_files")


if __name__ == "__main__":
    fetch()
