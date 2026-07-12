# Batch Bio Extraction via Python + Requests/BeautifulSoup

## When to Use

When following up bio details for **15+ people** from CSAIL (or any server-rendered Drupal site), use Python + `requests`/`BeautifulSoup` instead of per-person browser navigation. This is **5-10x faster** than the browser approach for large batches.

## Prerequisites

```bash
pip install requests beautifulsoup4 lxml
```

## Core Extraction Script

```python
import requests, json, re, time
from bs4 import BeautifulSoup

def extract_person_bio(url, timeout=30):
    """Extract role_raw, research_areas, homepage, cohort_year from a CSAIL person page."""
    result = {}
    resp = requests.get(url, timeout=timeout, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    
    # 1. role_raw
    title_div = soup.select_one(".field--name-field-title")
    if title_div:
        result["role_raw"] = title_div.get_text(strip=True)
    
    # 2. research_areas
    area_links = soup.select(".research-areas .field--name-field-research-area a")
    if area_links:
        result["research_areas"] = [a.get_text(strip=True) for a in area_links]
    
    # 3. homepage
    ext_link = soup.select_one(".field--name-field-external-site a")
    if ext_link and ext_link.get("href", "") not in ("", "#"):
        result["homepage"] = ext_link["href"]
    
    # 4. cohort_year from bio paragraph
    bio_div = soup.select_one(".field--name-field-description")
    if bio_div:
        bio_text = bio_div.get_text()
        # Pattern 1: "PhD at/in <university> in YYYY"
        m = re.search(r'PhD\s+(?:from|at)\s+.+?(\\d{4})', bio_text)
        if m:
            result["cohort_year"] = int(m.group(1))
        # Pattern 2: "joined MIT/CSAIL ... YYYY"
        elif re.search(r'joined\s+(?:MIT|CSAIL)\b.*?(\\d{4})', bio_text):
            result["cohort_year"] = int(re.search(r'joined\s+(?:MIT|CSAIL)\b.*?(\\d{4})', bio_text).group(1))
        # Pattern 3: "since YYYY" (e.g., "PhD student at MIT CSAIL since 2021")
        elif re.search(r'(?:since|started|began)\s*(?:in\s*)?(?:the\s*)?(?:fall|spring|summer\s*)?(?:of\s*)?(\\d{4})', bio_text, re.IGNORECASE):
            result["cohort_year"] = int(re.search(r'(?:since|started|began)\s*(?:in\s*)?(?:the\s*)?(?:fall|spring|summer\s*)?(?:of\s*)?(\\d{4})', bio_text, re.IGNORECASE).group(1))
    
    return result
```

## CSAIL Page DOM Selectors

| Field | CSS Selector | Notes |
|-------|-------------|-------|
| role_raw | `.field--name-field-title` | Plain text of the role/title |
| research_areas | `.research-areas .field--name-field-research-area a` | Links inside the Research Areas section; may be empty (genuinely absent) |
| homepage | `.field--name-field-external-site a` | The `href` attribute; often absent |
| cohort_year | `.field--name-field-description` | Parse for "PhD at/in... YYYY" or "joined MIT in YYYY" |
| bio text | `.field--name-field-description` | Full bio paragraph content |
| impact_areas | `.impact-areas .field--name-field-impact-area a` | Separate from Research Areas; application domains not research |
| name (already known) | `h1.person-name` | Available from the listing page |

## Curl Subprocess Approach (Alternative Stdlib Fallback)

When `requests` is unavailable and `urllib.request` times out too aggressively on Windows (common with MIT's slow Drupal server), use `subprocess.run(['curl', ...])` as a third stdlib option. `curl` has mature network/SSL handling that doesn't depend on Python's socket layer:

```python
import subprocess, re, json

def fetch_curl(url, timeout=30):
    result = subprocess.run(
        ['curl', '-sL', url, '-H', 'User-Agent: Mozilla/5.0'],
        capture_output=True, text=True, timeout=timeout
    )
    result.check_returncode()
    return result.stdout

def extract_bio_via_curl(url):
    page_html = fetch_curl(url)
    info = {"name": ...}  # known from caller

    # role_raw
    m = re.search(
        r'<div[^>]*class="[^"]*field--name-field-title[^"]*"[^>]*>\s*([^<]+?)\s*</div>',
        page_html
    )
    if m:
        import html as html_mod
        info['role_raw'] = html_mod.unescape(m.group(1).strip())

    # research_areas
    area_section = re.search(
        r'<div[^>]*field--name-field-research-area[^>]*>(.*?)</div>\s*</div>',
        page_html, re.DOTALL
    )
    if area_section:
        area_links = re.findall(r'<a[^>]*>([^<]+)</a>', area_section.group(1))
        if area_links:
            import html as html_mod
            info['research_areas'] = [
                html_mod.unescape(a.strip()) for a in area_links if a.strip()
            ]

    # homepage
    m = re.search(
        r'field--name-field-external-site[^>]*>.*?<a href="([^"]+)"',
        page_html, re.DOTALL
    )
    if m:
        href = m.group(1).strip()
        if '/taxonomy/' not in href and not href.startswith('/'):
            info['homepage'] = href

    return info
```

**Trade-offs vs `urllib.request` vs `requests`:**
| Dimension | `urllib.request` | `subprocess` + `curl` | `requests` |
|-----------|-----------------|----------------------|------------|
| Dependencies | None | curl binary in PATH | `pip install requests` |
| Timeout handling | Weak on Windows (OS socket timeout) | Reliable (curl manages its own sockets) | Reliable |
| SSL handling | System-context-dependent | Built-in | Built-in |
| Error reporting | Generic URLError | Exit code + stderr | Specific exception types |
| Concurrency | Manual (threading) | Manual (threading) | Manual (ThreadPoolExecutor) |
| Speed | Slow per-request | ~1-2s per request (same as requests) | Fast (shared session) |

Use this when: the environment has `curl` but not `pip` access, or when `urllib.request` gives unreliable timeouts on the MIT CSAIL server.

### ⚠️ Pitfall: `import html` variable shadowing

When writing extraction scripts, a common bug is naming the page content variable `html`, which shadows the stdlib `html` module (used for `.unescape()`):

```python
# WRONG — variable name collides with module
import html  # stdlib module for html.unescape()
result = subprocess.run(['curl', '...'], capture_output=True, text=True)
html = result.stdout  # ← this SHADOWS the import!
areas = [html.unescape(a) for a in areas]  # AttributeError: 'str' has no 'unescape'

# CORRECT — use a distinct variable name
import html as html_mod
page_html = result.stdout
areas = [html_mod.unescape(a) for a in areas]
```

**Two reliable fixes:**
1. Name the page variable something distinct: `page_html`, `resp_text`, `html_source`
2. Use `import html as html_mod` and always reference through the alias

Always prefer approach (2) — the alias protects against any future variable name collision. The error message `'str' object has no attribute 'unescape'` is the telltale sign of this shadowing bug.

## Zero-Dependency Approach (stdlib only)

If `requests`/`beautifulsoup4`/`lxml` are not installed (common on fresh environments), use `urllib.request` + regex. This requires **no pip installs** and works with Python's standard library:

```python
import urllib.request, urllib.error, json, re, ssl, time

ctx = ssl.create_default_context()

def fetch_person(url, name):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=15, context=ctx)
    html = resp.read().decode('utf-8')
    info = {"name": name}
    
    # email — scope to contact section to avoid footer press-requests link
    contact_section = re.search(
        r'<div class="person-contact-info">(.*?)</section>',
        html, re.DOTALL
    )
    if contact_section:
        email_match = re.search(
            r'<a href="mailto:([^"]+)"',
            contact_section.group(1)
        )
        if email_match:
            info['email'] = email_match.group(1)

    # role_raw
    m = re.search(r'field--name-field-title[^>]*field__item[^>]*>\s*(.*?)\s*</div>', html)
    if m:
        info['role_raw'] = m.group(1).strip()
    
    # research_areas — from the area-tags.person-areas section
    area_section = re.search(r'area-tags person-areas[^>]*>(.*?)(?:</div>\s*</section>|</section>)', html, re.DOTALL)
    if area_section:
        areas = re.findall(r'<a\s+href="/taxonomy/term/\d+"[^>]*>([^<]+)</a>', area_section.group(1))
        if areas:
            import html as html_mod
            info['research_areas'] = [html_mod.unescape(a.strip()) for a in areas if a.strip()]
    
    # homepage
    hp_section = re.search(r'field--name-field-external-site[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
    if hp_section:
        link_m = re.search(r'href="([^"]+)"', hp_section.group(1))
        if link_m and not link_m.group(1).startswith('mailto:'):
            info['homepage'] = link_m.group(1).strip()
    
    # description/bio text
    desc_m = re.search(r'field--name-field-description[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
    if desc_m:
        # Extract just the <p> tag content for clean text
        p_match = re.search(r'<p>(.*?)</p>', desc_m.group(1), re.DOTALL)
        if p_match:
            desc_text = re.sub(r'<[^>]+>', ' ', p_match.group(1))
            desc_text = re.sub(r'\s+', ' ', desc_text).strip()
            if desc_text:
                info['description'] = desc_text
    
    # room number
    room_m = re.search(r'class=[\'"]room[\'"]>([^<]+)', html)
    if room_m:
        info['room'] = room_m.group(1).strip()
    
    # cohort_year from description
    if 'description' in info:
        _extract_cohort_year(info, info['description'])
    
    return info

def _extract_cohort_year(info, text):
    # explicit year mentions
    for pat in [
        r'(?:since|started|joined|began|entered|class of)\s*(20\d{2})',
        r'(?:PhD|Ph\.D\.|doctoral|Master|MS)\s*(?:student\s*)?(?:since|class of|started|joined)\s*(20\d{2})',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            y = int(m.group(1))
            if 2015 <= y <= 2030:
                info['cohort_year'] = y
                return
    # ordinal-year patterns: "first-year PhD student" → 2025 (current academic year)
    YEAR_MAP = {'first': 2025, '1st': 2025, 'second': 2024, '2nd': 2024,
                'third': 2023, '3rd': 2023, 'fourth': 2022, '4th': 2022,
                'fifth': 2021, '5th': 2021}
    for ordinal, year in YEAR_MAP.items():
        if re.search(rf'{ordinal}\s*[- ]?year', text, re.IGNORECASE):
            info['cohort_year'] = year
            return
```

**Trade-offs vs requests+BeautifulSoup:**
- `urllib.request` times out more aggressively (the OS-level socket timeout is harder to control on Windows)
- Regex is brittle against HTML whitespace variations — BeautifulSoup handles these transparently
- `urllib` uses the system SSL context which may block some CDN connections without a custom `ssl._create_unverified_context()`
- **When to use stdlib-only**: Fresh Windows environment, no pip available, or when you need a self-contained script
- **When to use requests+BS4**: Production batch extraction; the `pip install` cost pays for itself in reliability

## Handling Slow MIT Servers

The MIT CSAIL site (`www.csail.mit.edu`) is frequently slow (5-15 second response times) and may time out on the default 30-second timeout. Drupal-generated pages also occasionally return empty responses (read timed out despite HTTP 200) due to server-side processing delays.

**Strategy:**
1. Set `timeout=30` on requests — most pages load within this window
2. If a page times out, **retry once** with `timeout=60`
3. If still failing, fall back to browser navigation (`browser_navigate`) for that specific person
4. Add a 1.5-2 second `time.sleep()` between requests in a multi-person batch to avoid overwhelming the server
5. Save results incrementally to JSONL after each successful extraction (not just at end)

**Retry with fallback pattern:**
```python
def safe_fetch(url, name):
    for timeout in [30, 60]:
        try:
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": "..."})
            resp.raise_for_status()
            return resp.text
        except (requests.Timeout, requests.ConnectionError):
            print(f"  Timeout {timeout}s for {name}, retrying...")
    print(f"  HTTP failed for {name}, falling back to browser")
    return None  # caller handles via browser_navigate
```

## Incremental JSONL Writing

```python
def append_result(jsonl_path, result):
    with open(jsonl_path, "a") as f:
        f.write(json.dumps(result) + "\n")
```

Call this after each person's extraction so partial progress is never lost if the script crashes.

## Architecture Notes

- **Isolation**: Arrange as a standalone Python file, not inline in the agent's turn — avoids tool-call-limit issues
- **Batch size**: 15-30 people per batch works well (30-60 seconds with delays)
- **Output**: Each result is one JSONL line; the full output can be merged across batches
- **Fallback**: The browser can verify any individual extraction the script couldn't complete

## ⚠️ Drupal 10 Wrapped-h4 DOM Quirk

CSAIL (Drupal 10) renders h4 headings inside their own `<div>`, with the section content in the **next sibling `<div>`**, NOT as a sibling of the h4 element itself. This breaks naive `h4.find_next_sibling()` in BeautifulSoup:

```html
<!-- Drupal 10 rendering pattern — h4 wrapped in its own div -->
<div>
  <h4>Related Links</h4>
</div>
<!-- Content is in the NEXT sibling div -->
<div>
  <a href="https://example.com">My Website</a>
</div>
```

The same pattern applies to `Research Areas`, `Related Links`, and any other h4-based section. Using BeautifulSoup, `find_next_sibling()` from the h4 returns `None` because the h4 is the only child of its parent div, so the content appears to be missing.

**Three Discovery Strategies (use in order):**

```python
def find_section_content(article, heading_text):
    """Find content elements after a section heading, handling Drupal's wrapped-h4 DOM."""
    from bs4 import Tag

    # Strategy 1: h4.find_next_sibling() — heading and content are siblings in same parent
    for h4 in article.find_all('h4'):
        if h4.get_text(strip=True) == heading_text:
            items = []
            nxt = h4.find_next_sibling()
            while nxt is not None:
                if isinstance(nxt, Tag) and nxt.name in ('h2', 'h3', 'h4', 'h5', 'h6'):
                    break
                if isinstance(nxt, Tag):
                    items.append(nxt)
                nxt = nxt.find_next_sibling()
            if items:
                return items

    # Strategy 2: h4.parent.find_next_sibling() — h4 is wrapped in its own div
    for h4 in article.find_all('h4'):
        if h4.get_text(strip=True) == heading_text:
            parent = h4.find_parent()
            if parent and parent != article:
                next_sibling = parent.find_next_sibling()
                if next_sibling:
                    return [next_sibling]

    # Strategy 3: Scan article direct children for field-wrapper divs
    for child in article.find_all(['div', 'section'], recursive=False):
        inner_h4 = child.find('h4')
        if inner_h4 and inner_h4.get_text(strip=True) == heading_text:
            next_child = child.find_next_sibling()
            if next_child:
                return [next_child]

    return []
```

**Why this matters:** Without this multi-strategy approach, ~40% of CSAIL pages (those using the wrapped-h4 pattern) report missing Research Areas and missing Homepages, even when those fields are present. Strategy 2 alone catches most cases; Strategy 3 handles edge cases where both the heading AND content are inside field-wrapper divs.

## CSAIL Field Prevalence (Cumulative Batches 13-19)\n\n| Field | Batch 13 (Fu-Guo) | Batch 15 (H-J) | Batch 17 (K-L) | Batch 18 (L-Li) | Batch 19 (Liu-Math) | Overall |\n|-------|-------------------|----------------|----------------|-----------------|---------------------|---------|\n| role_raw | 25/25 (100%) | 25/25 (100%) | 25/25 (100%) | 25/25 (100%) | 25/25 (100%) | 100% |\n| research_areas | 4/25 (16%) | 10/25 (40%) | 4/25 (16%) | 4/25 (16%) | 6/25 (24%) | ~22% |\n| homepage | 6/25 (24%) | 9/25 (36%) | 3/25 (12%) | 5/25 (20%) | 4/25 (16%) | ~22% |\n| cohort_year | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | ~0% |\n\n**Observation**: Graduate student pages at CSAIL have role=100%, research_areas≈22%, homepage≈22%, and cohort_year≈0%. Batch 15 (H-J) shows a notable spike in both research_areas (40%) and homepage (36%), driven by entries with center-affiliation taxonomy tags (e.g., Zeshan Hussain with 7 areas from CDML, Christina Ji with 7 from CDML). This is natural variation — some batches contain more students affiliated with centers that embed taxonomy tags on individual pages. Batch 20 (M-P, not yet processed in this table) observed research_areas=5/25 (20%), homepage=0/25 (0%) — showing the range of variation.

**Notable entries with full data (Batch 19):**\n- Yang Liu: research_areas=["Graphics & Vision"], homepage="https://yangliu.mit.edu"\n- Yingcheng Liu: research_areas=["AI & ML"], homepage="https://people.csail.mit.edu/liuyingcheng"\n- Gabriel Margolis: research_areas=["Robotics"], homepage="http://gmargo11.github.io"\n- Markos Markakis: research_areas=["Systems & Networking"]\n- Artem Lukoianov: homepage="https://www.linkedin.com/in/artem-lukoianov/" (LinkedIn under Related Links)\n\n**Notable entries with extra data (Batch 22):**\n- Matthew Perron: research_areas=["Algorithms & Theory", "Computer Architecture", "Programming Languages & Software Engineering", "Systems & Networking", "Security & Cryptography"]\n- Benoit Marc Pit--Claudel: research_areas=["Systems & Networking"], homepage="https://pit-claudel.fr/benoit/"\n- Charilaos Pipis: homepage="https://charispipis.com/"

## Alternative: Camofox Evaluate (Browser-in-the-Loop Extraction)

When direct HTTP scraping fails (JS-rendered content, timeouts, anti-detection), use Camofox's `/evaluate` endpoint to run JavaScript inside a real browser tab. This is slower than direct HTTP but more reliable for tricky pages.

**When to use this instead of direct HTTP:**

| Signal | Action |
|--------|--------|
| Page requires JS rendering (SPA, lazy-load) | Use Camofox evaluate |
| MIT server timeout on HTTP approach | Retry with Camofox evaluate for specific people |
| BeautifulSoup/regex parsing fails on inconsistent markup | Use evaluate with DOM selectors (more robust) |
| Page returns empty or partial HTML to plain requests | Use Camofox evaluate |
| You need anti-detection / CAPTCHA bypass | Camofox handles this automatically |

**Pattern: Full batch via single Camofox tab**

```python
import json, time, requests

BASE = 'http://localhost:9377'
USER_ID = 'mit_csail_bot'
SESSION_KEY = 'batch16'

# 1. Create one tab for the entire batch
r = requests.post(f'{BASE}/tabs', json={
    'userId': USER_ID, 'sessionKey': SESSION_KEY
})
tab_id = r.json()['tabId']

# 2. Define the extraction JS that works in the page context
EXTRACTION_JS = '''
(function() {
    // Role: text node after h1 (CSAIL-specific)
    const h1 = document.querySelector("article h1");
    let roleRaw = null;
    if (h1) {
        let node = h1.nextSibling;
        while (node) {
            if (node.nodeType === 3) {  // text node
                const t = node.textContent.trim();
                if (t && !t.includes('Last updated')) { roleRaw = t; break; }
            } else if (node.nodeType === 1 && node.tagName === "H4") {
                break;
            }
            node = node.nextSibling;
        }
    }

    // Research areas: <a> tags in article with /taxonomy/term/ links
    const areas = [];
    document.querySelectorAll("article a[href*='/taxonomy/term/']").forEach(a => {
        const t = a.textContent.trim();
        if (t) areas.push(t);
    });

    // Last updated date
    let lastUpdated = null;
    document.querySelectorAll("article p").forEach(p => {
        if (p.textContent.includes("Last updated")) lastUpdated = p.textContent.trim();
    });

    // Homepage from "Related Links" section
    let homepage = null;
    document.querySelectorAll("h4").forEach(h => {
        if (h.textContent.includes("Related Links")) {
            let next = h.nextElementSibling;
            while (next && next.tagName === "A") {
                const t = (next.textContent || '').toLowerCase();
                const href = next.href || '';
                if ((t.includes('personal website') || t.includes('homepage') || t.includes('personal page'))
                    && !href.includes('mailto:') && !href.includes('/taxonomy/')) {
                    homepage = href;
                }
                next = next.nextElementSibling;
            }
        }
    });

    return JSON.stringify({
        role_raw: roleRaw,
        research_areas: areas.length > 0 ? areas : undefined,
        homepage: homepage || undefined,
        last_updated: lastUpdated
    });
})();
'''

# 3. Iterate through people, reusing the same tab
output_path = 'output/<lab>/bio_updates_batch.jsonl'
for person in people:
    # Navigate to person page
    requests.post(f'{BASE}/tabs/{tab_id}/navigate', json={
        'url': person['source_detail_url'],
        'userId': USER_ID, 'sessionKey': SESSION_KEY
    })
    time.sleep(1)  # Let page render

    # Extract data via JS
    r = requests.post(f'{BASE}/tabs/{tab_id}/evaluate', json={
        'expression': EXTRACTION_JS,
        'userId': USER_ID, 'sessionKey': SESSION_KEY
    })
    data = json.loads(r.json()['result'])

    # Write incrementally
    record = {'name': person['name'], 'email': person['email'],
              'source_detail_url': person['source_detail_url']}
    for key in ('role_raw', 'research_areas', 'homepage', 'last_updated'):
        if data.get(key):
            record[key] = data[key]
    with open(output_path, 'a') as f:
        f.write(json.dumps(record) + '\n')

# 4. Clean up
requests.delete(f'{BASE}/tabs/{tab_id}', params={'userId': USER_ID})
```

**CSAIL page DOM structure (for `evaluate` JS selectors):**

```
<article>
  <img alt="Avatar">
  <h1>Name</h1>
  Graduate Student            ← text node (role), not in a <p>
  <h4>Email</h4>
  <a href="mailto:...">...</a>
  <p>Last updated Nov 19 '24</p>
  <h4>Research Areas</h4>
  <a href="/taxonomy/term/9">AI & ML</a>     ← may be absent
  <h4>Related Links</h4>
  <a href="https://...">Personal website</a>  ← may be absent
</article>
```

### Variant: Per-Person Tab (Resilient to Session Expiration)

When Camofox sessions expire mid-batch (observed error: `"Browser session expired. Retry to get a fresh session."` with HTTP 503), a per-person tab strategy isolates failures:

```python
import json, time, requests

BASE = 'http://localhost:9377'
USER_ID = 'mit_csail_bot'

def fetch_person_via_camofox(url, name):
    """Create a tab, extract article HTML, return parsed info."""
    # Create tab
    r = requests.post(f'{BASE}/tabs', json={
        'userId': USER_ID,
        'sessionKey': 'bio_extraction',
        'url': url
    }, timeout=15)
    if r.status_code != 200:
        raise RuntimeError(f"Tab creation failed: {r.text[:100]}")
    tab_id = r.json()['tabId']

    try:
        time.sleep(2)  # Let page render

        # Get article HTML (server-side parsing is more flexible than JS eval)
        r = requests.post(f'{BASE}/tabs/{tab_id}/evaluate', json={
            'userId': USER_ID,
            'expression': 'document.querySelector(\'article\') ? document.querySelector(\'article\').innerHTML : \'\''
        }, timeout=15)
        article_html = r.json().get('result', '')

        # Get page text for fallback/cross-check
        r = requests.post(f'{BASE}/tabs/{tab_id}/evaluate', json={
            'userId': USER_ID,
            'expression': 'document.body.innerText'
        }, timeout=15)
        page_text = r.json().get('result', '')

        return parse_article_html(article_html, page_text)
    finally:
        # Close tab — always, even on failure
        requests.delete(f'{BASE}/tabs/{tab_id}', params={'userId': USER_ID}, timeout=10)

def parse_article_html(article_html, page_text):
    """Server-side parsing of article HTML (regex-based, no BeautifulSoup dependency)."""
    import html as html_mod
    info = {'role_raw': '', 'research_areas': [], 'homepage': '', 'cohort_year': None}

    # role: Drupal field--name-field-title
    m = __import__('re').search(
        r'field--name-field-title[^>]*field__item[^>]*>\s*(.*?)\s*</div>',
        article_html, __import__('re').DOTALL | __import__('re').IGNORECASE
    )
    if m:
        info['role_raw'] = m.group(1).strip()

    # research_areas: taxonomy term links
    area_links = __import__('re').findall(
        r'<a[^>]*href="/taxonomy/term/\d+"[^>]*>(.*?)</a>',
        article_html
    )
    for a in area_links:
        area = html_mod.unescape(a.strip())
        if area:
            info['research_areas'].append(area)

    # homepage: field--name-field-external-site
    hp_m = __import__('re').search(
        r'field--name-field-external-site[^>]*field__item[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>',
        article_html, __import__('re').DOTALL | __import__('re').IGNORECASE
    )
    if hp_m:
        url = hp_m.group(1).strip()
        if url and not url.startswith('/') and not url.startswith('mailto:'):
            info['homepage'] = url

    # cohort_year from page text
    for pat in [
        r'(?:since|started|began|joined|class of)\s*(20\d{2})',
        r'(?:PhD|Ph\.D|Master|MS)\s*[\\'\\'']\s*(\d{2})\b',
    ]:
        ym = __import__('re').search(pat, page_text, __import__('re').IGNORECASE)
        if ym:
            yr = int(ym.group(1))
            if len(ym.group(1)) == 2:
                yr += 2000
            if 1990 <= yr <= 2030:
                info['cohort_year'] = yr
                break

    return info

# Main batch loop with retry
for i, person in enumerate(people):
    print(f'[{i+1}/{len(people)}] {person["name"]}', end='', flush=True)
    try:
        info = fetch_person_via_camofox(person['source_detail_url'], person['name'])
        # write incrementally
        with open(output_path, 'a') as f:
            f.write(json.dumps({'name': person['name'], **info}) + '\n')
        print(f' | role={info.get("role_raw","?")}')
    except Exception as e:
        print(f' | FAILED: {e}')
        # Retry once — Camofox session expiration is transient
        if 'session_expired' in str(e) or '503' in str(e):
            print('  Retrying after transient error...')
            try:
                info = fetch_person_via_camofox(person['source_detail_url'], person['name'])
                with open(output_path, 'a') as f:
                    f.write(json.dumps({'name': person['name'], **info}) + '\n')
                print(f'  Retry SUCCESS | role={info.get("role_raw","?")}')
            except Exception as e2:
                print(f'  Retry FAILED: {e2}')
                # Record minimal entry so the person is not lost
                with open(output_path, 'a') as f:
                    f.write(json.dumps({'name': person['name'], 'error': str(e2)}) + '\n')
```

**Advantages of per-person tab approach:**
- Session expiration in one request doesn't cascade to subsequent people
- Each tab gets a fresh browser context (no cross-person state leakage)
- Clean error isolation — one failed person doesn't block the batch

**Trade-off vs single-reusable-tab:** ~2s overhead per person (tab creation + close) vs ~0.5s navigate within an existing tab. For 25 people, the difference is ~50s vs ~12s — acceptable headroom for robustness.

## ⚠️ BeautifulSoup get_text() &lt;a&gt;-tag Line-Splitting Pitfall

When a page uses a table layout with inline `<a>` tags — common in Chinese lab personal pages (LAMDA, etc.) — BeautifulSoup's `get_text('\n', strip=True)` **splits `<a>` tag text onto separate lines** from the text that precedes the tag:

```html
Supervisor: Professor<a href="...">Yang Yu</a><br>
```

becomes:

```
Supervisor: Professor
Yang Yu
```

not:

```
Supervisor: Professor Yang Yu
```

This means a regex like `Supervisor:\s*(.+)` on the clean text will only capture `Professor`, not the full name. This explains why naive HTTP extraction finds **0-40%** advisor coverage while Camofox (which reads `document.body.innerText` from the browser) finds **70%+** — the browser preserves inline text flow correctly.

**Three mitigation strategies (use in order):**

1. **Camofox evaluate** — `document.body.innerText` returns text exactly as the browser renders it (inline, not split by `<a>`). Use the `/evaluate` endpoint.

2. **Multi-line fusion** — After finding `Supervisor:`, check the next line if the current line only captured a title fragment:
   ```python
   m = re.search(r'Supervisor:\s*(.+)', line)
   adv = m.group(1).strip()
   if adv in ('Professor', 'Prof', 'Associate', 'Associate Professor'):
       adv = lines[i + 1].strip()  # pick up next line
   info['advisor'] = adv
   ```

3. **Raw HTML regex** — Parse directly against HTML with `<a>` tags inline:
   ```python
   m = re.search(r'Supervisor:\s*(?:Prof\.?\s*)?(?:<[^>]+>)*([^<>\n]+?)(?:\s*<br|\s*Co-supervisor)', html, re.IGNORECASE)
   ```

A reusable script demonstrating all three is at `scripts/extract_advisor_via_camofox.py`.

---

### Pitfall: HTML Entity Encoding in Drupal Pages

CSAIL's Drupal 10 renders `&amp;` for ampersands in research area names (e.g., `&quot;Graphics &amp; Vision&quot;`). After extraction, always decode entities with `html.unescape()`:

```python
import html
raw = "Graphics &amp; Vision"
decoded = html.unescape(raw)  # → "Graphics & Vision"
```

Without this, `research_areas` will contain "AI &amp; ML" instead of "AI & ML". This applies to both regex-based and BeautifulSoup-based extraction — BeautifulSoup auto-decodes text node values, but regex-based extraction does not.

**Key observations from the CSAIL person page structure:**
- The **role** (e.g. "Graduate Student") sits as a bare text node between `<h1>` and the next `<h4>` — **not** inside a `<p>` or `<div>`. This is why `document.querySelector('article p')` won't find it. Select with `h1.nextSibling` and check `nodeType === 3`.
- **Research areas** and **Related Links** sections are optional — most grad student profiles lack them. Never fabricate these fields; simply omit them from the output record if absent.
- The **email** is always present as a `mailto:` link after an `<h4>Email</h4>` heading.
- The **last updated** date is in an `<article> <p>` containing "Last updated".
