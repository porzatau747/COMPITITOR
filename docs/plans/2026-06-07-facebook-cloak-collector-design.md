# Design: Facebook Page Scraper using CloakBrowser

This design document outlines the implementation of a dedicated collector for scraping public Facebook pages of competitors using CloakBrowser.

## Context & Requirements
- **Goal**: Fetch competitor content from public Facebook pages.
- **Constraints**: Avoid violating Facebook's Terms of Service (no credentials, no automated login, no captcha solving, no proxy rotation). Use CloakBrowser (playwright-based headless browser) to render the Javascript content of public pages.
- **Targets**:
  1. `https://www.facebook.com/AdvicePrachuapKhiriKhan`
  2. `https://www.facebook.com/AdvicePhichit`
  3. `https://www.facebook.com/comcraft.ds`
  4. `https://www.facebook.com/notebookspec`
  5. `https://www.facebook.com/overclockzonefanpage`
  6. `https://www.facebook.com/techhub.arip`
  7. `https://www.facebook.com/CPUCore2Duo`
  8. `https://www.facebook.com/itcityofficial`

## Architecture & Components

### 1. Configuration: `data/facebook_cloak_sources.json`
Stores the active list of public Facebook pages to scrape.

```json
{
  "sources": [
    {
      "name": "Advice Prachuap Khiri Khan",
      "url": "https://www.facebook.com/AdvicePrachuapKhiriKhan",
      "platform": "facebook_cloak",
      "source_type": "facebook_page_public",
      "category": "IT Retail",
      "location": "Prachuap Khiri Khan",
      "priority_score": 85,
      "limit_posts": 5,
      "active": true
    },
    ...
  ]
}
```

### 2. Collector: `app/collectors/facebook_cloak_collector.py`
A new collector class `FacebookCloakCollector` that:
- Reads `data/facebook_cloak_sources.json`.
- Launches `CloakBrowser` headlessly.
- Accesses each URL, scrolls down slightly using `window.scrollBy` to trigger dynamic rendering and dismiss basic popups.
- Parses the rendered HTML:
  - Selects all elements matching `div[role="article"]` (individual posts).
  - Extracts post URL: looks for anchors matching `/posts/`, `/permalink.php`, `/photos/`, `/videos/`, or `fbid=`.
  - Extracts post text: looks for `div[data-ad-preview="message"]` or `div[dir="auto"]` inside the article.
  - Extracts engagement metrics: parses numbers (like/comment/share counts, e.g. converting `2.4K` to `2400`) from text inside the article.
  - Extracts post date: uses relative text like "2 hrs ago" to approximate date.
- Limits extraction up to `limit_posts` per page.
- Saves new posts to the database.

### 3. Integration
- Connect the new collector inside [app/services/collector_service.py](file:///d:/por/project/COMPITITOR/advice-content-radar/app/services/collector_service.py) in the non-mock flow (`settings.mock_mode = False`).

## Error Handling
- Each source is scraped independently inside a `try-except` block. A single source failure will log a warning/error but won't crash the entire job.
- Clean resource management ensures the browser is closed after scraping finishes or on failure.

## Verification & Testing
- Unit tests in `tests/test_facebook_cloak_collector.py` will use mock HTML fragments containing standard Facebook page elements to verify the extraction of text, URLs, and engagement numbers.
