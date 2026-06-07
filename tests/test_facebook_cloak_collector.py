from app.collectors.facebook_cloak_collector import parse_facebook_post, parse_engagement_number

def test_parse_engagement_number():
    assert parse_engagement_number("12") == 12
    assert parse_engagement_number("1.2K") == 1200
    assert parse_engagement_number("3.5M") == 3500000
    assert parse_engagement_number("0") == 0
    assert parse_engagement_number(None) == 0

def test_parse_facebook_post_html():
    html_fragment = """
    <div role="article">
      <div data-ad-preview="message">โน้ตบุ๊กทำงานแรงสุดขีด RAM 32GB ราคาประหยัด</div>
      <a href="https://www.facebook.com/permalink.php?story_fbid=123&id=456">2 hrs</a>
      <div>
        <span>ถูกใจ 1.5K คน</span>
        <span>ความคิดเห็น 120 รายการ</span>
        <span>แชร์ 45 ครั้ง</span>
      </div>
    </div>
    """
    post = parse_facebook_post(html_fragment, "https://www.facebook.com")
    assert post is not None
    assert "โน้ตบุ๊กทำงานแรงสุดขีด" in post["text"]
    assert post["url"] == "https://www.facebook.com/permalink.php?story_fbid=123&id=456"
    assert post["likes"] == 1500
    assert post["comments"] == 120
    assert post["shares"] == 45
