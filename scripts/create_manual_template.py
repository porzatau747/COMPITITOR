from pathlib import Path
import csv

path = Path(__file__).resolve().parents[1] / "data" / "manual_import_template.csv"
path.parent.mkdir(exist_ok=True)
rows = [
    {
        "source_name": "ตัวอย่างเพจคู่แข่ง",
        "platform": "facebook",
        "source_url": "https://www.facebook.com/example",
        "source_type": "direct_competitor",
        "post_url": "https://www.facebook.com/example/posts/1",
        "post_text": "คอมช้า เปิดโปรแกรมนาน เพิ่ม RAM หรือ SSD ก่อนดี",
        "like_count": 120,
        "comment_count": 25,
        "share_count": 18,
        "view_count": 0,
    }
]
with path.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
print(path)
