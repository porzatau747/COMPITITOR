from app.services.report_service import build_morning_brief


def test_morning_brief_contains_actionable_sections():
    report = build_morning_brief(
        report_date="2026-06-05",
        top_items=[{
            "number": 1,
            "title": "คอมช้าเพราะ RAM ไม่พอ",
            "source_name": "Mock IT Page",
            "score": 88.5,
            "why": ["แตะ pain point ที่เจอบ่อย", "ทำให้คนอยากถามราคา"],
            "local_adaptation": "ทำโพสต์เช็กอาการคอมช้าฟรีที่ Advice สามร้อยยอด",
            "risk": ["อย่าขายตรงเกินไป"],
            "hook": "คอมช้าอย่าเพิ่งซื้อใหม่"
        }],
        market_signals=["คอมช้า/RAM/SSD", "โน้ตบุ๊กทำงาน", "Printer สำนักงาน"],
        actions={"sales":"เช็กสเปกฟรี", "knowledge":"สอนดู RAM", "reels":"ถ่ายก่อนหลังอัป SSD"},
        hooks=["คอมช้าอย่าเพิ่งซื้อใหม่"]
    )
    assert "📡 Advice Content Radar" in report
    assert "/caption 1" in report
    assert "🎯 คอนเทนต์ที่ควรทำวันนี้" in report
