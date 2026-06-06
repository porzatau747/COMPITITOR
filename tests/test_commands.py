from app.services.telegram_command_service import parse_number_arg, render_caption_response, render_carousel_response, render_reels_response


def sample_idea():
    return {
        "suggested_hook": "งบ 15,000 ซื้อโน้ตบุ๊กทำงานได้ไหม?",
        "caption_draft": "ส่งงบมาให้แอดช่วยดูได้",
        "local_angle": "ลูกค้าสามร้อยยอดเลือกโน้ตบุ๊กทำงาน",
        "creative_direction": "ภาพโน้ตบุ๊ก + เช็กลิสต์",
        "sales_bridge": "ไม่แน่ใจว่าสเปกพอไหม ทักมาได้",
        "cta": "ทักเพจ Advice สามร้อยยอด"
    }


def test_parse_number_arg_defaults_to_one():
    assert parse_number_arg("/caption") == 1
    assert parse_number_arg("/caption 3") == 3


def test_caption_response_has_four_styles_and_hashtags():
    text = render_caption_response(sample_idea())
    assert "แคปชั่นสั้น" in text
    assert "แคปชั่นสายขาย" in text
    assert "#Adviceสามร้อยยอด" in text


def test_carousel_and_reels_have_required_sections():
    assert "Slide 1" in render_carousel_response(sample_idea())
    reels = render_reels_response(sample_idea())
    assert "Hook 3 วินาทีแรก" in reels
    assert "Shot List" in reels
