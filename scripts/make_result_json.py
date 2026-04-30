import csv
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]

SOURCE_CSV = ROOT / "data" / "source.csv"
OUT_JSON = ROOT / "data" / "result.json"


items = []

with SOURCE_CSV.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        items.append({
            "menu": int(row["menu"]),
            "page": int(row["page"]),
            "article_number": str(row["article_number"]),
            "date": row["date"],
            "writer": row["writer"],
            "title": row["title"],
        })


updated_at = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

payload = {
    "updated_at": updated_at,
    "target": "2026-04",
    "count": len(items),
    "items": items,
}


with OUT_JSON.open("w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)


print(f"완료: {OUT_JSON}")
print(f"총 {len(items)}개 저장")