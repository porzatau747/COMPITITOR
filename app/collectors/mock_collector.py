from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Source, Post

MOCK_POSTS = [
 {"source":"Advice Competitor HuaHin", "cat":"Notebook", "text":"งบ 15,000 เลือกโน้ตบุ๊กทำงานยังไงไม่ให้พลาด RAM 16GB ยังจำเป็นไหม", "likes":420,"comments":88,"shares":55,"views":5000},
 {"source":"IT Tips Thailand", "cat":"RAM", "text":"คอมช้า เปิด Chrome แล้วค้าง เพิ่ม RAM หรือเปลี่ยน SSD ก่อนดี", "likes":650,"comments":120,"shares":90,"views":8000},
 {"source":"Printer Pro", "cat":"Printer", "text":"ปริ้นเตอร์สำนักงาน หมึกแท้งค์กับเลเซอร์ เลือกผิดต้นทุนบาน", "likes":230,"comments":40,"shares":35,"views":2400},
 {"source":"Monitor Club", "cat":"Monitor", "text":"จอ 24 นิ้ว 100Hz ทำงานก็ได้ เล่นเกมก็ดี จริงไหม", "likes":180,"comments":30,"shares":18,"views":1500},
 {"source":"Router Guru", "cat":"Router", "text":"WiFi บ้านชั้นสองหลุดบ่อย Router หรือ Mesh WiFi ช่วยได้", "likes":310,"comments":70,"shares":60,"views":3200},
 {"source":"CCTV Local", "cat":"CCTV", "text":"กล้องวงจรปิดร้านค้า ดูผ่านมือถือได้ แจ้งเตือนตอนกลางคืน", "likes":150,"comments":44,"shares":42,"views":2100},
 {"source":"Gaming Gear Page", "cat":"Gaming Gear", "text":"คีย์บอร์ดเมาส์เกมมิ่ง งบไม่แรง ใช้ทำงานด้วยได้ไหม", "likes":270,"comments":65,"shares":30,"views":4100},
 {"source":"UPS Safety", "cat":"UPS", "text":"ไฟตกบ่อย คอมดับ เสี่ยงข้อมูลหาย UPS จำเป็นกว่าที่คิด", "likes":380,"comments":75,"shares":82,"views":3600},
 {"source":"Repair Shop", "cat":"Repair Service", "text":"โน้ตบุ๊กเปิดไม่ติด อย่าเพิ่งทิ้ง เช็ก 5 อาการก่อนส่งซ่อม", "likes":520,"comments":140,"shares":110,"views":7000},
 {"source":"Meme IT", "cat":"Meme IT", "text":"มีมมือถือแบตหมด ดราม่าแบรนด์ คนแชร์ขำๆ แต่ขายของต่อยาก", "likes":900,"comments":200,"shares":180,"views":20000},
]

def ensure_mock_sources(db: Session):
    for row in MOCK_POSTS:
        src=db.query(Source).filter(Source.name==row["source"]).first()
        if not src:
            src=Source(name=row["source"], platform="mock", source_url=f"https://example.com/{row['source'].replace(' ','-')}", source_type="it_news_page", category=row["cat"], active=True)
            db.add(src)
    db.commit()

class MockCollector:
    def collect(self, db: Session, hours: int = 24) -> list[Post]:
        ensure_mock_sources(db)
        created=[]
        now=datetime.utcnow()
        for i,row in enumerate(MOCK_POSTS, start=1):
            src=db.query(Source).filter(Source.name==row["source"]).first()
            url=f"mock://post/{i}"
            post=db.query(Post).filter(Post.post_url==url).first()
            if not post:
                post=Post(source_id=src.id, post_url=url, post_text=row["text"], media_url=None, posted_at=now-timedelta(hours=i), like_count=row["likes"], comment_count=row["comments"], share_count=row["shares"], view_count=row["views"])
                db.add(post); created.append(post)
        db.commit()
        return created
