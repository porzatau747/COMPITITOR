import ipaddress
import json
import logging
import re
import socket
import time
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse, urlunparse
from urllib import robotparser

import httpx
from lxml import html
from sqlalchemy.orm import Session

from app.models import Post, Source

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "AdviceContentRadarBot/1.0 (+local business trend monitoring; respectful public-page fetcher)"
IT_KEYWORDS = [
    "notebook", "โน้ตบุ๊ก", "laptop", "คอม", "computer", "pc", "gaming", "printer", "ปริ้น",
    "ssd", "ram", "router", "wifi", "wi-fi", "ups", "monitor", "จอ", "cctv", "กล้องวงจรปิด",
    "repair", "ซ่อม", "windows", "office", "ไอที", "it", "cpu", "gpu", "keyboard", "mouse",
]


@dataclass
class WebSourceConfig:
    name: str
    url: str
    platform: str = "web"
    source_type: str = "public_web_page"
    category: str | None = "IT"
    location: str | None = None
    priority_score: int = 50
    max_links: int = 8
    use_browser: bool = False
    allowed_domains: list[str] | None = None


@dataclass
class FetchedPage:
    url: str
    html_text: str
    fetcher: str


class RobotsCache:
    def __init__(self, user_agent: str = DEFAULT_USER_AGENT):
        self.user_agent = user_agent
        self._cache: dict[str, robotparser.RobotFileParser] = {}

    def can_fetch(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return False
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._cache:
            rp = robotparser.RobotFileParser()
            rp.set_url(urljoin(base, "/robots.txt"))
            try:
                rp.read()
            except Exception as exc:
                logger.warning("robots.txt read failed for %s: %s", base, exc)
            self._cache[base] = rp
        return self._cache[base].can_fetch(self.user_agent, url)


class WebAgentCollector:
    """Respectful public-web collector for Advice Content Radar.

    Uses Scrapling as the preferred HTML fetcher. CloakBrowser is available only as an explicit
    `use_browser=true` fallback for JavaScript-rendered public pages. It intentionally does not use
    proxy rotation, captcha solving, login automation, or anti-bot bypass settings.
    """

    def __init__(
        self,
        config_path: str | Path = "data/web_sources.json",
        user_agent: str = DEFAULT_USER_AGENT,
        delay_seconds: float = 2.0,
        check_robots: bool = True,
        max_response_chars: int = 2_000_000,
    ):
        self.config_path = Path(config_path)
        self.user_agent = user_agent
        self.delay_seconds = delay_seconds
        self.check_robots = check_robots
        self.max_response_chars = max_response_chars
        self.robots = RobotsCache(user_agent=user_agent)

    def collect(self, db: Session, hours: int = 24) -> list[Post]:
        del hours  # Web pages rarely expose reliable post times; scoring freshness handles missing dates.
        sources = self.load_sources()
        imported: list[Post] = []
        for source_cfg in sources:
            try:
                imported.extend(self.collect_source(db, source_cfg))
            except Exception:
                logger.exception("web agent source failed: %s", source_cfg.url)
        db.commit()
        return imported

    def collect_source(self, db: Session, source_cfg: WebSourceConfig) -> list[Post]:
        source = self._get_or_create_source(db, source_cfg)
        urls = self.discover_urls(source_cfg)
        imported: list[Post] = []
        seen_urls: set[str] = set()
        for idx, url in enumerate(urls):
            if url in seen_urls:
                continue
            seen_urls.add(url)
            if not _is_safe_public_url(url):
                logger.info("unsafe private/local url skipped %s", url)
                continue
            if self.check_robots and not self.robots.can_fetch(url):
                logger.info("robots.txt disallowed; skipped %s", url)
                continue
            if db.query(Post).filter(Post.post_url == url).first():
                continue
            if idx:
                time.sleep(self.delay_seconds)
            page = self.fetch(url, use_browser=source_cfg.use_browser)
            if page.url != url:
                if page.url in seen_urls:
                    continue
                seen_urls.add(page.url)
            if db.query(Post).filter(Post.post_url == page.url).first():
                continue
            post_text = self.extract_post_text(page.html_text, page.url)
            if not post_text or len(post_text) < 80:
                logger.info("too little text; skipped %s", url)
                continue
            post = Post(
                source_id=source.id,
                post_url=page.url,
                post_text=post_text[:6000],
                media_url=self.extract_image_url(page.html_text, page.url),
                posted_at=self.extract_posted_at(page.html_text),
                like_count=0,
                comment_count=0,
                share_count=0,
                view_count=0,
            )
            db.add(post)
            imported.append(post)
        db.commit()
        return imported

    def load_sources(self) -> list[WebSourceConfig]:
        if not self.config_path.exists():
            return []
        raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw = raw.get("sources", [])
        sources = []
        for item in raw:
            if item.get("active", True):
                sources.append(WebSourceConfig(**{k: v for k, v in item.items() if k != "active"}))
        return sources

    def discover_urls(self, source_cfg: WebSourceConfig) -> list[str]:
        if not _is_safe_public_url(source_cfg.url):
            logger.info("unsafe private/local source skipped %s", source_cfg.url)
            return []
        if self.check_robots and not self.robots.can_fetch(source_cfg.url):
            logger.info("robots.txt disallowed source index; skipped %s", source_cfg.url)
            return []
        page = self.fetch(source_cfg.url, use_browser=source_cfg.use_browser)
        links = self.extract_candidate_links(page.html_text, page.url, source_cfg)
        urls = [page.url]
        for link in links:
            if link not in urls:
                urls.append(link)
            if len(urls) >= source_cfg.max_links:
                break
        return urls

    def fetch(self, url: str, use_browser: bool = False) -> FetchedPage:
        if use_browser:
            try:
                return self._fetch_with_cloakbrowser(url)
            except Exception as exc:
                logger.warning("CloakBrowser fetch failed; falling back to Scrapling/httpx for %s: %s", url, exc)
        try:
            return self._fetch_with_scrapling(url)
        except Exception as exc:
            logger.warning("Scrapling fetch failed; falling back to httpx for %s: %s", url, exc)
            return self._fetch_with_httpx(url)

    def _fetch_with_scrapling(self, url: str) -> FetchedPage:
        from scrapling.fetchers import Fetcher

        response = Fetcher.get(url, headers={"User-Agent": self.user_agent}, timeout=30)
        html_text = str(getattr(response, "text", "") or "")
        if not html_text:
            raw_body = getattr(response, "body", b"") or b""
            if isinstance(raw_body, bytes):
                html_text = raw_body.decode(getattr(response, "encoding", None) or "utf-8", errors="replace")
            else:
                html_text = str(raw_body)
        if not html_text and getattr(response, "html_content", None):
            html_text = str(response.html_content)
        if len(html_text) > self.max_response_chars:
            raise ValueError(f"response too large for {url}")
        return FetchedPage(url=str(getattr(response, "url", url)), html_text=html_text, fetcher="scrapling")

    def _fetch_with_httpx(self, url: str) -> FetchedPage:
        with httpx.Client(follow_redirects=True, timeout=30, headers={"User-Agent": self.user_agent}) as client:
            response = client.get(url)
            response.raise_for_status()
            if not _is_safe_public_url(str(response.url)):
                raise ValueError(f"redirected to unsafe private/local url: {response.url}")
            if len(response.text) > self.max_response_chars:
                raise ValueError(f"response too large for {url}")
            return FetchedPage(url=str(response.url), html_text=response.text, fetcher="httpx")

    def _fetch_with_cloakbrowser(self, url: str) -> FetchedPage:
        # Optional JS renderer for public pages only. Avoids stealth/proxy/humanize settings by design.
        from cloakbrowser import launch

        browser = launch(headless=True)
        try:
            page = browser.new_page(user_agent=self.user_agent)
            page.goto(url, wait_until="networkidle", timeout=30000)
            page_url=page.url
            html_text=page.content()
            if not _is_safe_public_url(page_url):
                raise ValueError(f"redirected to unsafe private/local url: {page_url}")
            if len(html_text) > self.max_response_chars:
                raise ValueError(f"response too large for {url}")
            return FetchedPage(url=page_url, html_text=html_text, fetcher="cloakbrowser")
        finally:
            browser.close()

    def extract_candidate_links(self, html_text: str, base_url: str, source_cfg: WebSourceConfig) -> list[str]:
        doc = _parse_html(html_text)
        base_domain = urlparse(base_url).netloc.lower().removeprefix("www.")
        allowed = [d.lower().removeprefix("www.") for d in (source_cfg.allowed_domains or [base_domain])]
        candidates: list[tuple[int, str]] = []
        for a in doc.xpath("//a[@href]"):
            href = a.get("href") or ""
            text = _clean_text(" ".join(a.xpath(".//text()")))
            if not href or href.startswith(("mailto:", "tel:", "javascript:")):
                continue
            url = _canonical_url(urljoin(base_url, href))
            parsed = urlparse(url)
            domain = parsed.netloc.lower().removeprefix("www.")
            if not any(domain == d or domain.endswith("." + d) for d in allowed):
                continue
            if _looks_like_asset(parsed.path):
                continue
            score = _keyword_score(text + " " + url)
            if score <= 0 and not _looks_like_article_path(parsed.path):
                continue
            candidates.append((score + len(text) // 80, url))
        candidates.sort(key=lambda item: item[0], reverse=True)
        deduped = []
        for _, url in candidates:
            if url not in deduped:
                deduped.append(url)
        return deduped

    def extract_post_text(self, html_text: str, url: str) -> str:
        doc = _parse_html(html_text)
        title = _first_text(doc, ["//meta[@property='og:title']/@content", "//title/text()", "//h1//text()"])
        description = _first_text(doc, ["//meta[@name='description']/@content", "//meta[@property='og:description']/@content"])
        body_nodes = doc.xpath("//article//p//text() | //main//p//text() | //p//text() | //h1//text() | //h2//text()")
        body = _clean_text(" ".join(body_nodes))
        pieces = [p for p in [title, description, body] if p]
        text = _clean_text("\n".join(pieces))
        if not text:
            text = _clean_text(unescape(re.sub(r"<[^>]+>", " ", html_text)))
        return f"URL: {url}\n{text}"

    def extract_image_url(self, html_text: str, base_url: str) -> str | None:
        doc = _parse_html(html_text)
        img = _first_text(doc, ["//meta[@property='og:image']/@content", "//article//img/@src", "//main//img/@src"])
        return urljoin(base_url, img) if img else None

    def extract_posted_at(self, html_text: str):
        doc = _parse_html(html_text)
        value = _first_text(doc, ["//meta[@property='article:published_time']/@content", "//time/@datetime"])
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None

    def _get_or_create_source(self, db: Session, cfg: WebSourceConfig) -> Source:
        source = db.query(Source).filter(Source.source_url == cfg.url).first()
        if source:
            return source
        source = Source(
            name=cfg.name,
            platform=cfg.platform,
            source_url=cfg.url,
            source_type=cfg.source_type,
            category=cfg.category,
            location=cfg.location,
            priority_score=cfg.priority_score,
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source


def _parse_html(html_text: str):
    return html.fromstring(html_text or "<html></html>")


def _first_text(doc, xpaths: Iterable[str]) -> str | None:
    for xp in xpaths:
        values = doc.xpath(xp)
        if values:
            if isinstance(values[0], str):
                text = values[0]
            else:
                text = " ".join(values[0].xpath(".//text()"))
            text = _clean_text(text)
            if text:
                return text
    return None


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text or "")).strip()


def _canonical_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/") or "/", "", parsed.query, ""))


def _looks_like_asset(path: str) -> bool:
    return path.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".pdf", ".zip", ".mp4", ".mp3"))


def _looks_like_article_path(path: str) -> bool:
    path = path.lower()
    return any(token in path for token in ["/news", "/article", "/blog", "/review", "/how-to", "/content", "/technology"])


def _keyword_score(text: str) -> int:
    haystack = text.lower()
    return sum(1 for kw in IT_KEYWORDS if kw.lower() in haystack)


def _is_safe_public_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    host = parsed.hostname.lower().strip("[]")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return False
    try:
        ip = ipaddress.ip_address(host)
        return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved)
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return True
    for info in infos:
        address = info[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            return False
    return True
