

"""
Collect all file links from GitHub repo folders (via GitHub Contents API)
and export to CSV at a specific Windows path.

pip install requests pandas
"""

import os
import sys
import time
from typing import Dict, List, Optional

import pandas as pd
import requests

OWNER = "antoinemrn8"
REPO = "iut_sd2_webscraping_UBB_MAURIN_SANZ"
BRANCH = "main"
ROOT_PATH = "data/Players"

API_BASE = "https://api.github.com"
SLEEP_SECONDS = 0.2

# ✅ Output path requested
OUTPUT_DIR = r"C:\Users\rafae\OneDrive\Documents\web_scrapping\data"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "players_github_links.csv")


def gh_get_json(url: str, token: Optional[str] = None) -> List[Dict]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "iut-sd2-webscraping-link-collector/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise RuntimeError(
            "GitHub API rate limit exceeded. Add a token via GITHUB_TOKEN env var."
        )
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else [data]


def contents_url(path: str) -> str:
    return f"{API_BASE}/repos/{OWNER}/{REPO}/contents/{path}?ref={BRANCH}"


def list_subfolders(token: Optional[str]) -> List[Dict]:
    items = gh_get_json(contents_url(ROOT_PATH), token=token)
    return [it for it in items if it.get("type") == "dir"]


def list_files_in_folder(folder_path: str, token: Optional[str]) -> List[Dict]:
    items = gh_get_json(contents_url(folder_path), token=token)
    return [it for it in items if it.get("type") == "file"]


def main():
    token = os.getenv("GITHUB_TOKEN")  # optional

    rows = []
    folders = list_subfolders(token)

    if not folders:
        print("No subfolders found. Check ROOT_PATH/BRANCH/REPO.")
        sys.exit(1)

    for f in folders:
        group = f.get("name")
        folder_path = f.get("path")
        print(f"Folder: {group} ({folder_path})")

        time.sleep(SLEEP_SECONDS)
        files = list_files_in_folder(folder_path, token)

        for file_item in files:
            rows.append(
                {
                    "group": group,
                    "file_name": file_item.get("name"),
                    "file_path": file_item.get("path"),
                    "html_url": file_item.get("html_url"),
                    "raw_download_url": file_item.get("download_url"),
                    "size_bytes": file_item.get("size"),
                }
            )

    df = pd.DataFrame(rows).sort_values(["group", "file_name"]).reset_index(drop=True)

    # ✅ Ensure folder exists, then export
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"\n✅ Export done: {OUTPUT_CSV}")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
