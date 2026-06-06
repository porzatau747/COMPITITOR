from app.collectors.web_agent_collector import WebAgentCollector, WebSourceConfig


def test_web_agent_extracts_it_links_and_text():
    html = """
    <html><head>
      <title>ข่าวไอทีวันนี้</title>
      <meta name="description" content="รวมข่าว Notebook SSD RAM และ WiFi">
      <meta property="og:image" content="/cover.jpg">
    </head>
    <body>
      <main>
        <article>
          <h1>โน้ตบุ๊กทำงาน งบ 15000 เลือก RAM หรือ SSD ก่อนดี</h1>
          <p>หลายคนเปิด Chrome แล้วค้าง ควรเช็ก RAM, SSD และ Windows ก่อนซื้อเครื่องใหม่</p>
        </article>
        <a href="/news/notebook-ssd-ram">วิธีเลือก Notebook SSD RAM สำหรับงานออฟฟิศ</a>
        <a href="/about">เกี่ยวกับเรา</a>
      </main>
    </body></html>
    """
    collector = WebAgentCollector(check_robots=False)
    cfg = WebSourceConfig(name="Test", url="https://example.com/news", max_links=5)

    text = collector.extract_post_text(html, cfg.url)
    links = collector.extract_candidate_links(html, cfg.url, cfg)
    image = collector.extract_image_url(html, cfg.url)

    assert "โน้ตบุ๊กทำงาน" in text
    assert "RAM" in text
    assert links == ["https://example.com/news/notebook-ssd-ram"]
    assert image == "https://example.com/cover.jpg"
