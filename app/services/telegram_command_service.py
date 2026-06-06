def parse_number_arg(text: str) -> int:
    parts=(text or "").strip().split()
    if len(parts) < 2: return 1
    try: return max(1, int(parts[1]))
    except ValueError: return 1

def render_caption_response(idea: dict) -> str:
    hook=idea.get("suggested_hook") or "ไม่แน่ใจว่าสเปกพอไหม?"
    bridge=idea.get("sales_bridge") or "ทักเพจให้แอดมินช่วยดูงบได้"
    cta=idea.get("cta") or "ทักเพจ Advice สามร้อยยอดได้เลย"
    return f"""แคปชั่นสั้น:\n{hook}\n{bridge}\n\nแคปชั่นสายขาย:\n{hook}\nกำลังหาอุปกรณ์ไอทีที่เหมาะกับงานจริง ส่งงบมาให้แอดช่วยดูได้ครับ\nพิกัด: Advice สามร้อยยอด\n\nแคปชั่นสายมีม:\nคอมช้าจนกาแฟเย็นแล้วงานยังไม่เสร็จ 😅\n{bridge}\n\nแคปชั่นสุภาพ:\n{hook}\nหากไม่แน่ใจว่าสเปกที่มีเพียงพอต่อการใช้งานหรือไม่ สามารถส่งรุ่น/งบประมาณมาให้แอดมินช่วยดูได้ครับ\n{cta}\n\nHashtags:\n#Adviceสามร้อยยอด #คอมพิวเตอร์ #โน้ตบุ๊ก #ร้านไอที #ประจวบคีรีขันธ์ #ไอทีน่ารู้ #โปรไอที"""

def render_carousel_response(idea: dict) -> str:
    hook=idea.get("suggested_hook") or "คอมช้าอย่าเพิ่งซื้อใหม่"
    return f"""Slide 1: Hook\n{hook}\n\nSlide 2: Problem\nหลายคนซื้ออุปกรณ์ผิด เพราะไม่รู้ว่าสเปกไหนพอกับงาน\n\nSlide 3: Explain\nงานเอกสาร / เรียนออนไลน์ / แต่งภาพ / เล่นเกม ใช้สเปกไม่เหมือนกัน\n\nSlide 4: Product / Service Bridge\n{idea.get('sales_bridge', 'ส่งงบหรือรุ่นมาให้แอดช่วยดูได้')}\n\nSlide 5: CTA\n{idea.get('cta', 'ทักเพจ Advice สามร้อยยอดได้เลย')}\nมีบริการ รับ-ส่ง สินค้าและเครื่องซ่อม"""

def render_reels_response(idea: dict) -> str:
    hook=idea.get("suggested_hook") or "คอมช้าอย่าเพิ่งซื้อใหม่"
    return f"""Hook 3 วินาทีแรก:\n{hook}\n\nShot List:\n1. ถือโน้ตบุ๊ก/อุปกรณ์ที่มีปัญหา\n2. ซูมอาการหรือเช็กลิสต์หน้าจอ\n3. แอดมินอธิบายทางเลือกสั้น ๆ\n4. โชว์หน้าร้าน/ทีมงาน\n5. ปิดด้วย CTA\n\nVoiceover:\nหลายคนเจอปัญหานี้แล้วรีบซื้อใหม่ ทั้งที่บางเคสอัปเกรดหรือเช็กสเปกก่อนช่วยประหยัดได้เยอะ ส่งรุ่นหรืออาการมาให้แอดดูได้ครับ\n\nText on Screen:\nคอมช้า? / สเปกพอไหม? / ส่งรุ่นให้แอดช่วยดู / Advice สามร้อยยอด\n\nCTA:\n{idea.get('cta', 'ทักเพจ Advice สามร้อยยอดได้เลย')}"""
