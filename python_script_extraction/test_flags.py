import os
import csv
import requests
from urllib.parse import quote

OWNER = "antoinemrn8"
REPO = "iut_sd2_webscraping_UBB_MAURIN_SANZ"
BRANCH = "main"
PATH_IN_REPO = "data/nationality"

# Where you want the CSV on your PC (change if needed)
OUT_CSV = r"C:\Users\rafae\OneDrive\Documents\web_scrapping\data\nationality_images.csv"

# If you hit rate limits, create a GitHub token and set it in an env var:
# setx GITHUB_TOKEN "xxxxx"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}

headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "UBB-webscraping-student/1.0",
}
if GITHUB_TOKEN:
    headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def is_image(filename: str) -> bool:
    return os.path.splitext(filename.lower())[1] in IMG_EXT


def raw_url(path: str) -> str:
    # raw.githubusercontent.com needs URL-encoded path parts
    # (quote keeps "/" but encodes spaces etc.)
    safe_path = quote(path)
    return f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/{safe_path}"


def list_contents(path: str, recursive: bool = True):
    """
    Returns a list of dict rows for all files under `path`.
    Uses GitHub Contents API:
    GET /repos/{owner}/{repo}/contents/{path}?ref={branch}
    """
    api_url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}?ref={BRANCH}"
    r = requests.get(api_url, headers=headers, timeout=30)
    r.raise_for_status()
    items = r.json()

    rows = []
    for it in items:
        if it["type"] == "file":
            rows.append(it)
        elif it["type"] == "dir" and recursive:
            rows.extend(list_contents(it["path"], recursive=True))
    return rows


def main():
    files = list_contents(PATH_IN_REPO, recursive=True)

    images = []
    for f in files:
        if is_image(f["name"]):
            images.append({
                "name": f["name"],
                "path": f["path"],
                "size_bytes": f.get("size"),
                "html_url": f.get("html_url"),
                # GitHub API provides a direct download_url for raw content:
                "download_url": f.get("download_url"),
                # And we also build the raw URL ourselves (equivalent):
                "raw_url": raw_url(f["path"]),
            })

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=images[0].keys() if images else
                                ["name","path","size_bytes","html_url","download_url","raw_url"])
        writer.writeheader()
        writer.writerows(images)

    print(f"✅ Saved {len(images)} image URLs to: {OUT_CSV}")


if __name__ == "__main__":
    main()
