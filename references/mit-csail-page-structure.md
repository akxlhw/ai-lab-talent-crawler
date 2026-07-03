# MIT CSAIL Person Page Structure

## Overview

MIT CSAIL has a Drupal-based website at `https://www.csail.mit.edu/` with person detail pages at `/person/<name-slug>`.

## Person Detail Page Structure

**URL pattern**: `https://www.csail.mit.edu/person/<name-slug>`

### Accessibility Tree Structure (consistent across pages)

```
- heading "PI Core/Dual" [level=4]      # or just "PI" for some
- heading "<Person Name>" [level=1]
- text: <role_raw>                       # e.g. "Professor", "Associate Professor"
- heading "Email" [level=4]
- link "email@mit.edu" [mailto]
- heading "Phone" [level=4]              # OPTIONAL — many pages lack this
- text: <phone number>
- heading "Room" [level=4]              # OPTIONAL
- link "<room-code>" [map URL]
- paragraph: <bio text>                  # OPTIONAL — many pages lack this
- paragraph: "Last updated <date>"
- heading "Research Areas" [level=4]     # OPTIONAL — many pages lack this
- link "<Research Area Name>" [/taxonomy/term/N]  # 0-3 links
- heading "Impact Areas" [level=4]       # OPTIONAL
- link "<Impact Area Name>" [/taxonomy/term/N]
- heading "Related Links" [level=4]      # OPTIONAL
- link "Website" [eN]: [/url: <homepage_url>]
- heading "Projects" [level=2]           # OPTIONAL
- ...
- heading "Groups" [level=2]             # Community of Research / Research Group sections
- ...
```

### Role heading variation: "PI" vs "PI Core/Dual"

Most faculty pages have a `heading "PI Core/Dual" [level=4]` tag. However:
- **"PI"** (without "Core/Dual") appears on some **emeritus** professors (e.g., Albert R. Meyer, Tomaso Poggio)
- **"PI Core/Dual"** is the standard for active faculty
- **Student pages** (PhD Student, Postdoc, etc.) have NO PI heading at all

### Key Extraction Rules

1. **role_raw**: Look for the text node IMMEDIATELY after the `<h1>Name</h1>`. It's a plain text node (not wrapped in a link or heading). Examples:
   - `Professor` → "Professor"
   - `Associate Professor` → "Associate Professor"  
   - `Assistant Professor` → "Assistant Professor"
   - `Professor of the Practice` → "Professor of the Practice"
   - `Adjunct Professor` → "Adjunct Professor"
   - `Institute Professor` → "Institute Professor" (prestigious MIT-wide title — e.g., Thomas Magnanti, Ronald Rivest)
   - `Professor Emeritus` → "Professor Emeritus" (emeritus/retired — e.g., Albert R. Meyer)
   - `PhD Student` → "PhD Student" (common for grad students)
   - `Graduate Student` → "Graduate Student" (also common — interchangeable with "PhD Student" on CSAIL pages)

2. **Named professorships**: Some bios include named chairs in the first paragraph (e.g., "the Amar Bose Professor of Computing", "the RSA Professor of Mathematics", "the Thomas and Gerd Perkins Professor of EECS"). Use the named professorship as the full role_raw when available, fall back to the short role text. Known named professorships seen on CSAIL:
   - "Norbert Wiener Professor" (Ankur Moitra)
   - "Eugene McDermott Professor" (Tomaso Poggio)
   - "TIBCO Career Development Associate Professor" (Stefanie Mueller)
   - "Esther and Harold E. Edgerton Assistant Professor of Electrical Engineering & Computer Science" (Jonathan Ragan-Kelley)
   - "Distinguished Professor of Computer Science" (Rob Miller)

3. **Research Areas**: Located under the "Research Areas" heading, these are taxonomy term links (typically 0-3). Common values:
   - "AI & ML"
   - "Graphics & Vision"
   - "Computer Architecture"
   - "Security & Cryptography"
   - "Algorithms & Theory"
   - "Systems & Networking"
   - "Computational Biology"
   - "Programming Languages & Software Engineering"
   - "Human-Computer Interaction"
   - "Robotics"

   **IMPORTANT**: Many CSAIL pages have NO "Research Areas" section at all. Leave `research_areas` as an empty list when absent — do not infer from bio text. Some pages also have an **"Impact Areas"** section (distinct from Research Areas) listing application domains like "Big Data", "Cybersecurity", "Manufacturing", "Education", "Entertainment", "Internet of Things", "Wireless".

   **CSS selector alternatives — two class patterns exist on CSAIL**: Research area links may appear under either (or both) of these CSS selectors:
   - `.research-areas .field--name-field-research-area a` (Drupal field system)
   - `.area-tags.person-areas a` (theme-level class, observed in production — see Boyuan Chen, Heng-Jui Chang)

   When using BeautifulSoup, prefer the broader selector `.area-tags` or combine both via `soup.select('.area-tags a, .research-areas a')`. The Drupal field selector may miss results on pages that only use the theme-level `.area-tags` class.

   **Hidden taxonomy term links**: On some pages (especially Group pages and Format A student pages), research area taxonomy links exist in the HTML but are NOT visible in the browser accessibility snapshot — they're rendered in a non-visible sidebar metadata block. `browser_snapshot` will miss them entirely. When scraping programmatically, these can still be extracted via `browser_console` using `document.querySelectorAll('a[href*="taxonomy/term/"]')`, or in BeautifulSoup by searching for any `<a href="/taxonomy/term/N">` in the full page HTML. To distinguish research areas from impact areas (which use the same `/taxonomy/term/N` URL pattern), check the nearest preceding `<h4>` heading or use the term IDs directly:

   - Research Area term IDs: `9` (AI & ML), `10` (Algorithms & Theory), `11` (Computer Architecture), `12` (Computational Biology), `13` (Systems & Networking), `14` (Programming Languages & Software Engineering), `15` (Human-Computer Interaction), `16` (Graphics & Vision), `17` (Robotics), `18` (Security & Cryptography)

   - Impact Area term IDs: `3` (Big Data), `4` (Cybersecurity), `5` (Education), `6` (Entertainment), `7` (Internet of Things), `8` (Manufacturing), `19` (Wireless)

   **Production extraction strategy** (proven across Batches 17 and 18): Use three extraction methods in order of specificity, aggregating results from each:

   1. `.research-areas .field--name-field-research-area a` → visible person-level tags
   2. `.area-tags a` → alternative theme-level class (may overlap with #1)
   3. `a[href*="/taxonomy/term/"]` filtered by known Research Area term IDs → hidden sidebar/group-level tags

   Deduplicate across all three sources. This catches research areas even when they only exist in hidden metadata.

   **DUPLICATION WARNING**: When extracting via DOM selectors (e.g., `document.querySelectorAll('.field--name-field-research-area a')`), research areas appear **twice** per page — once in the main content column and once in the sidebar `.page-metadata` block. Always deduplicate the array while preserving order:

   ```javascript
   const seen = new Set();
   const deduped = Array.from(document.querySelectorAll('.field--name-field-research-area a'))
     .map(a => a.textContent.trim())
     .filter(a => seen.has(a) ? false : seen.add(a));
   ```

   This does NOT apply when extracting via accessibility tree snapshot (which only shows each element once).

4. **Homepage**: Found under "Related Links" heading as a link with varying text labels. Observed label variants (all seen in production):
   - **"Homepage"** (e.g., Kartik Chandra → `https://cs.stanford.edu/~kach/`)
   - **"Official Website"** (e.g., Boyuan Chen → `https://boyuan.space/`)
   - **"Personal Website"** / **"Website"** (most common on older pages)
   - **"Home page"**

   The link's `/url:` in the accessibility tree is the reliable target, not the link text itself.

   **Alternate location — `page-resources` section**: Some CSAIL pages (especially Format B) list the homepage link inside a `<div class="content-container page-resources">` block rather than in a `.field--name-field-external-site` div. When scraping via HTML/BeautifulSoup, always search the full page for links with relevant text rather than relying on a single CSS class.

   ⚠️ **CRITICAL PITFALL — Footer social icon contamination**: CSAIL's page footer contains social media links — `twitter.com/MIT_CSAIL`, `facebook.com/MITCSAIL`, `youtube.com/user/MITCSAIL`, `instagram.com/mit_csail`, `linkedin.com/company/mit-csail`, and `computing.mit.edu`. When doing naive homepage extraction (e.g., "first non-MIT link on the page"), these footer icons are selected before any genuine personal homepage, causing false positives for 60-70% of people who have no homepage listed. **Always filter these out explicitly**:

   ```python
   FOOTER_SOCIAL = [
       "twitter.com/MIT_CSAIL", "facebook.com/MITCSAIL",
       "youtube.com/user/MITCSAIL", "instagram.com/mit_csail",
       "linkedin.com/company/mit-csail", "computing.mit.edu",
       "accessibility.mit.edu", "web.mit.edu"
   ]
   def is_footer_social(href):
       return any(d in href for d in FOOTER_SOCIAL)
   ```

   **Recommended homepage detection priority** (proven in production):
   1. Links with text containing "homepage", "official website", "personal website", "home page", "my website" — AND not footer social
   2. Links inside `.page-resources` section — AND not footer social, not MIT domain
   3. Fallback: first non-MIT, non-social, non-accessibility link — BUT filter footer SOCIAL_DOMAINS first

   **Non-standard homepage locations**: Some people only have LinkedIn links inside a `research-social-media` div block. This is NOT a standard homepage — only record it if the `homepage` field specifically allows social links.

5. **cohort_year**: Some CSAIL person pages DO show cohort/join year in the bio paragraph (`.field--name-field-description`). Extraction patterns:

   - **PhD completion year** — look for "PhD at/in <university> in YYYY" or "completed her PhD at MIT in 2006"
   - **Join/MIT year** — look for "joined MIT in <month> YYYY" or "joined CSAIL in YYYY"
   - **Degree year** — look for "S.B./S.M./Ph.D. degree from <university> in YYYY"
   - **Since year** — look for "since YYYY" (e.g., "PhD student at MIT CSAIL since 2021", "at MIT since 2019")
   - **Started/began year** — look for "started in YYYY" or "began in YYYY"

   Broader fallback regex (Python): `r'(?:since|joined|started|began)\s*(?:in\s*)?(?:the\s*)?(?:fall|spring|summer\s*)?(?:of\s*)?(20\d{2})'`

   When a page lacks a bio paragraph entirely (~40% of faculty, ~100% of students), cohort_year cannot be determined from the CSAIL page and must come from external sources (MIT directory, personal websites, LinkedIn, Google Scholar).

   Field prevalence: ~15% of faculty pages have an explicit PhD or join-year in the bio.

6. **Email**: Always present as a mailto link under the "Email" heading.

   ⚠️ **CRITICAL PITFALL — Footer press-requests link contamination**: CSAIL's footer contains a `mailto:news@csail.mit.edu?subject=CSAIL%20Media%20Inquiry` link for "Press Requests". When doing naive email extraction with a broad `mailto:([^"]+)` regex (matching the first mailto on the page), this footer link is selected before the person's email for ~30% of pages (pages where the person's email div sits deeper in the DOM tree after the footer). This causes false-positive emails showing the press-request address instead of the person's real email.

   **Fix — scope extraction to the contact section**:

   ```python
   import re
   # Good — only looks inside the person's contact info section
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
           email = email_match.group(1)

   # Bad — catches footer "Press Requests" mailto first
   # email_match = re.search(r'<a href="mailto:([^"]+)"', html)
   ```

   With BeautifulSoup, scope to the contact info div:

   ```python
   from bs4 import BeautifulSoup
   soup = BeautifulSoup(html, 'html.parser')
   contact_div = soup.find('div', class_='person-contact-info')
   if contact_div:
       email_link = contact_div.find('a', href=lambda h: h and h.startswith('mailto:'))
       if email_link:
           email = email_link['href'][7:]  # strip 'mailto:'
   ```

   This is a parallel contamination to the footer social icon pitfall for homepage extraction (see rule #4). Both arise from the same cause — CSAIL footer links matching before person-specific content when using first-match-in-document extraction.

7. **Groups section**: Shows which Community of Research and Research Groups the person belongs to. This can be used to infer broad research areas but is not a substitute for explicit Research Areas tags.

   **Two distinct sources of group information exist on CSAIL pages (don't confuse them):**

   - **Embedded group cards** (Format A pages): Found inside the `<h2>Groups</h2>` section. Each card shows the group name, lead(s), description, +member count. These contain the group's own Research/Impact Areas, which can be used as a fallback for the person's `research_areas`. Extraction strategy detailed in the "Group-Level Research Areas as Fallback" section below.

   - **`field--name-field-associated-research-groups`** (Drupal taxonomy field, present on ~5-10% of pages): A person-level metadata field that links directly to named research groups the person belongs to. Found in the sidebar metadata block (not in the visible Groups section). Examples seen: Jesse Michel → "Programming Systems Group", Ramya Muthukrishnan → "Medical Vision Group", "Vision Group". Extract via CSS selector: `.field--name-field-associated-research-groups a`. This field contains the **named group labels** (not research area tags) and is distinct from both the person-level `research_areas` and the group cards' research areas.

### Raw HTML DOM Structure (for programmatic extraction)

When using Python/requests for batch extraction (faster than browser navigation), the Drupal 10 HTML has consistent CSS classes:

| Field | CSS Class / HTML Pattern | Notes |
|-------|--------------------------|-------|
| role_raw | `.field--name-field-title` | Always present — plain text of the role/title |
| research_areas | `.field--name-field-research-area` (inside `.research-areas` section) | Often absent — empty list if missing |
| homepage | `.field--name-field-external-site a` | Often absent — link text varies. **Alternate location**: `.page-resources` section. ⚠️ Filter footer social icons (see rule #4). |
| associated_groups | `.field--name-field-associated-research-groups a` | Sometimes present — lists the named research groups the person belongs to (e.g., "Programming Systems Group", "Medical Vision Group"). These are taxonomy-term links distinct from the embedded group cards in the Groups section. |
| last_updated | `<p class="last-updated">Last updated Mon DD 'YY</p>` | Always present — useful for freshness check |

**HTML entity handling**: Research area names use HTML entities. Decode as:
- `&amp;` → `&` (e.g., "Graphics &amp; Vision" → "Graphics & Vision")
- `&#039;` → `'` (e.g., "Last updated Nov 20 &#039;25")
- `&lt;` / `&gt;` → `<` / `>`

**Regex extraction patterns** (Python):
```python
# role
m = re.search(r'field--name-field-title[^>]*>([^<]+)</div>', html)

# research areas
area_section = re.search(
    r'<div class="field field--name-field-research-area[^>]*field__items">(.*?)</div>\\s*</div>',
    html, re.DOTALL
)
if area_section:
    areas = re.findall(r'<a[^>]*>([^<]+)</a>', area_section.group(1))
    areas = [a.replace('&amp;', '&') for a in areas]

# homepage
m = re.search(r'field--name-field-external-site[^>]*>\\s*<a\\s+href="([^"]+)"', html)
```

**IMPORTANT: BeautifulSoup is more reliable than raw regex for batch extraction.** Live sessions have shown regex failing on Drupal's HTML (whitespace, entity encoding, line breaks between attributes) while BeautifulSoup consistently succeeds. Specific known failure: the regex for `field--name-field-title` can return empty strings for some pages even when the HTML structure is identical to pages where it works. **Always prefer BeautifulSoup with CSS selectors** for production batch extraction:

```python
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

# role
title_div = soup.find('div', class_='field--name-field-title')
role_raw = title_div.get_text(strip=True) if title_div else ""

# research areas
area_links = soup.select('.research-areas .field--name-field-research-area a')
research_areas = [a.get_text(strip=True).replace('&amp;', '&') for a in area_links]

# homepage
ext_site = soup.find('div', class_='field--name-field-external-site')
homepage = ext_site.find('a')['href'] if ext_site and ext_site.find('a') else ""
```

Reserve regex only for simple substring searches (e.g., finding year patterns in bio text).

**Batch extraction using requests + concurrent.futures** (preferred for 10+ people — ~5x faster than sequential):
```python
import requests, re, concurrent.futures

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

def fetch_person(person):
    try:
        resp = session.get(person["source_detail_url"], timeout=30)
        html = resp.text
        # extract fields with regex (see patterns above)
        return person["name"], {"role_raw": role, "homepage": homepage, ...}
    except Exception as e:
        return person["name"], {"error": str(e)}

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    fut_map = {ex.submit(fetch_person, p): p for p in people}
    for fut in concurrent.futures.as_completed(fut_map):
        name, data = fut.result()
        # write incrementally to JSONL
```
This is ~10x faster than `browser_navigate` per page and avoids the browser tool call budget.

**Server timeout fallback**: The MIT CSAIL server occasionally drops connections or times out on HTTP requests (read timeout 30s, `RemoteDisconnected` errors). When this happens:
1. Retry once with a longer timeout (60s)
2. If still failing, fall back to `browser_navigate(url)` which uses the Camofox browser service (different network path, often succeeds)
3. Record the fallback in the output report

### Two Distinct Page Formats

CSAIL person pages come in two distinct formats. The format a page uses determines what fields are available:

#### Format A: Newer/Sparse (most common for recent additions)

Minimal layout. Only shows: name, role, email, optional room, last-updated date, and Groups section. No person-level Research Areas, no Related Links, no bio paragraph.

- **Research Areas**: ONLY visible in the embedded **group card** (the group/project the person belongs to). These are the group's research areas, not the person's, but are the best signal available.
- **Homepage**: NOT listed on the page.
- **Cohort year**: NOT available.

Pages in this format: Yilun Du, Maggie Du, Barış Ekim, Fares Elsabbagh, Josh Engels, Logan Engstrom, Ezra Erives, Katie Everett, Ethan Fahnestock, Felix Faltings, Faraz Faruqi, Yumou Fei, Annie Feng, Meng Feng, Ying Feng, Nolan Fey, Gabriel Filipe, Margherita Firenze, Maxwell Fishelson, Noah Fisher, Alexandra Forsey-Smerek, Camilo Fosco, Joshua Fried.

#### Format B: Older/Detailed (legacy pages, likely created before ~2022)

Richer layout. Includes everything from Format A PLUS some of: person-level Research Areas section, person-level Impact Areas section, "Related Links" section with personal website, bio paragraph with education history.

- **Research Areas**: Listed at the person level under `<h4>Research Areas</h4>` with taxonomized links to `/taxonomy/term/N`.
- **Impact Areas**: Listed separately under `<h4>Impact Areas</h4>` — these are application domains (Big Data, Cybersecurity, Manufacturing, etc.), NOT research areas. Keep them distinct.
- **Homepage**: Found under "Related Links" section, often labeled "Personal Website" or "Website". Common patterns: `https://people.csail.mit.edu/<username>` or personal domain.
- **Cohort year**: Extractable from bio text when education history is included (e.g., "I received my BS in ... in 2018").

Pages in this format: Wei Fang, Axel Feldmann, **Boyuan Chen** (research_areas=["AI & ML", "Graphics & Vision", "Robotics"], homepage="https://boyuan.space/"), **Heng-Jui Chang** (research_areas=["AI & ML"], homepage="https://people.csail.mit.edu/hengjui/"), **Kartik Chandra** (homepage="https://cs.stanford.edu/~kach/"), **Martin Chan** (homepage="https://www.martinchan.org/"), **Makram Chahine** (homepage="https://www.mit.edu/~chahine/"), **Michael Burgess** (homepage="https://mburgjr.github.io/"), **Niklas Hagemann** (research_areas=["Human-Computer Interaction", "Robotics"], homepage="https://niklashagemann.cargo.site"), **Andreas Alexander Haupt** (research_areas=["AI & ML", "Human-Computer Interaction"], homepage="https://www.andyhaupt.com/"), **Alexandra Henzinger** (research_areas=["Security & Cryptography", "Systems & Networking"], homepage="https://people.csail.mit.edu/ahenz/"), **Kyle Hogan** (research_areas=["Computer Architecture", "Security & Cryptography"]),

### Page Completeness Variability

CSAIL person pages vary significantly in completeness:

| Field | Faculty Present Rate | Student (Format B) | Student (Format A) | Notes |
|-------|---------------------|---------------------|---------------------|-------|
| role_raw | ~100% | ~100% | ~100% | Always on the page |
| email | ~100% | ~100% | ~100% | Always present |
| Bio paragraph | ~60% | ~20% | ~0% | Only Format B students have bios; senior profs always have bios |
| Person-level Research Areas | ~50% | ~20% | ~0% | Format A students have **group-level** research areas instead (see below) |
| Group-level Research Areas (fallback) | ~30% | ~0% | ~30% | From the embedded group card — groups like LIS, R&R ML, SLS |
| Homepage link | ~40% | ~10% | ~0% | Under "Related Links", pattern `people.csail.mit.edu/username` or personal domain |
| Phone | ~50% | ~0% | ~0% | Random presence |
| Room | ~60% | ~30% | ~30% | Some students have room listed |
| cohort_year | ~10% | ~5% | ~0% | Only from bio text education history (e.g. "BS in 2018") |
| Impact Areas | ~30% | ~10% | ~0% | Application domain tags, distinct from Research Areas |
### Group-Level Research Areas as Fallback

When a student page lacks person-level Research Areas (Format A), the page's Groups section embeds cards for each research group the student belongs to. These group cards contain their own `<h4>Research Areas</h4>` and `<h4>Impact Areas</h4>` in the HTML. These are **the research group's areas**, not the individual student's specialized areas, but they are the only research signal available from the CSAIL page.

**Extraction strategy**: Parse the group cards' Research Areas and aggregate them (dedup) as the person's `research_areas`. Examples observed:
- Yilun Du (LIS group) → "AI & ML", "Robotics"
- Barış Ekim → "Algorithms & Theory", "AI & ML", "Computational Biology"
- Logan Engstrom (R&R ML + Algorithms Group) → "AI & ML", "Algorithms & Theory", "Cybersecurity", "Graphics & Vision", "Security & Cryptography"
- Gabriel Filipe (multiple groups) → "AI & ML", "Algorithms & Theory", "Computer Architecture", "Graphics & Vision", "Programming Languages & Software Engineering", "Robotics"

**Caveat**: Group-level areas are broader and less precise than person-level tags. Note this in the output report.

**Sparse page pattern**: Graduate Students (especially those early in their program) frequently have pages with **only** name, email, and room — no research areas, no homepage, no bio. This is normal, not a parsing error. Always leave missing fields omitted/empty rather than guessing.

Graduate Student listings on the People directory also frequently use "Graduate Student" as the role text rather than "PhD Student", even when the person is pursuing a PhD. Both forms appear and should be preserved as-is.

### ⚠️ Drupal Nested Field Div Pitfall (Regex Extraction)

When extracting `research_areas` via regex from CSAIL pages, the Drupal 10 HTML has a tricky nested structure that frequently causes empty results:

```html
<!-- OUTER wrapper div — also class="field--name-field-research-area" -->
<div class="field field--name-field-research-area">
  <!-- INNER container div — also class="field--name-field-research-area"! -->
  <div class="field field--name-field-research-area field--type-entity-reference field--label-hidden field__items">
    <div class="field__item"><a href="/taxonomy/term/9" hreflang="en">AI &amp; ML</a></div>
  </div>
</div>
```

Drupal 10 renders entity-reference fields with **two nested `<div>` elements sharing `class="field--name-field-research-area"`**. If your regex only captures the opening of the outer div (e.g., `r'.*?<div[^>]*class="[^"]*field--name-field-research-area[^"]*"'`), it will match the outer div's `<` and stop there — the actual content is inside the **inner** div, which is a separate, nested tag with the same class.

**Three reliable approaches:**

**Approach A — Match through both closing `</div>` tags** (includes content from both nested wrappers):
```python
research_field = re.search(
    r'<h4[^>]*>Research\s*Areas?\s*</h4>.*?'
    r'<div[^>]*class="[^"]*field--name-field-research-area[^"]*"[^>]*>'
    r'.*?</div>\s*</div>',
    html, re.DOTALL | re.IGNORECASE
)
# The trailing </div>\s*</div> closes both inner and outer divs
if research_field:
    areas = re.findall(
        r'<a[^>]*href="/taxonomy/term/\d+"[^>]*>(.*?)</a>',
        research_field.group(0)
    )
```

**Approach B — Target the inner div specifically** (more precise, no nesting ambiguity):
```python
area_section = re.search(
    r'<div[^>]*class="[^"]*field--name-field-research-area[^"]*'
    r'field__items[^"]*"[^>]*>.*?</div>\s*</div>',
    html, re.DOTALL
)
if area_section:
    areas = re.findall(r'<a[^>]*>([^<]+)</a>', area_section.group(1))
    areas = [a.replace('&amp;', '&') for a in areas]
```
The `field__items` class only appears on the inner div, making this unambiguous.

**Approach C — Skip div nesting entirely; match taxonomy term links** (most robust, harder to get wrong):
```python
terms = re.findall(
    r'<a[^>]*href="/taxonomy/term/\d+"[^>]*>(.*?)</a>',
    html
)
terms = [re.sub(r'<[^>]+>', '', t).replace('&amp;', '&').strip()
         for t in terms if re.sub(r'<[^>]+>', '', t).strip()]
```
This doesn't care about div nesting at all. Caveat: the same `/taxonomy/term/N` pattern is used for **Impact Area** links too. To separate, check the nearest preceding `<h4>` heading, or extract research vs impact areas independently from their respective `<h4>` sections.

**When using BeautifulSoup** (recommended), this nesting is transparent — CSS selectors handle it naturally:
```python
# Both outer and inner divs match the same class selector, soup.find_all finds only one
soup.select('.research-areas .field--name-field-research-area a')
```

### Batch Bio Follow-up Strategy

When following up bio details for 25+ people across CSAIL:

1. **Option A: Sequential browser navigation** — Visit each detail page via `browser_navigate(url)`. The CSAIL site loads pages individually (no JS-heavy SPA). Extract from the snapshot returned by `browser_navigate`. Use `browser_snapshot(full=true)` or `browser_console(expression=...)` only when the initial snapshot is truncated or you need hidden content.

2. **Option B: Concurrent HTTP fetching (preferred for >10 people)** — CSAIL person pages are simple Drupal-rendered static HTML. Use `requests` (preferred — better timeout handling) or `urllib.request` (stdlib, zero dependency) with `concurrent.futures.ThreadPoolExecutor` (3-5 workers) to fetch all pages simultaneously. This is ~5x faster than sequential browser navigation. Parse the HTML with BeautifulSoup (preferred) or regex. Handle timeouts gracefully — if a page times out via HTTP, retry once with a longer timeout or fall back to `browser_navigate`.

3. **Extract per-person and accumulate** — Write each person's result to a JSONL file immediately after extraction (don't batch-write at the end in case of tool call limits).

4. **Handle sparse pages gracefully** — Set empty arrays/null for missing fields rather than guessing. Most graduate student pages will only have `role_raw: "Graduate Student"` and sometimes a homepage from "Related Links". Never fabricate "PhD Student" — CSAIL uses both "Graduate Student" and "PhD Student" interchangeably; preserve the exact role text from the page.

5. **Efficiency tip**: After the first few pages, you'll recognize the pattern — with concurrent HTTP, all 25 pages can be fetched in ~10-15 seconds using 3-5 workers. The browser tool should be reserved for pages that require JavaScript rendering or have unusual structure. Reserve browser fallback for the ~5-10% of pages that time out over HTTP. Write results to `bio_updates_batchN.jsonl` as you go.

6. **Batch data points** (graduate student batches, ~25 people each):
   - **Batch 14 (G-H)**: role_raw=100%, research_areas=4/25, homepage=3/25, cohort_year=0/25
   - **Batch 15 (H-J)**: role_raw=100%, research_areas=10/25, homepage=9/25, cohort_year=0/25
   - **Batch 17 (K-L)**: role_raw=100%, research_areas=4/25, homepage=3/25, cohort_year=0/25
   - **Batch 18 (L-Li)**: role_raw=100%, research_areas=4/25, homepage=5/25, cohort_year=0/25
   - **Batch 19 (Liu-Math)**: role_raw=100%, research_areas=6/25, homepage=4/25, cohort_year=0/25
   - **Batch 20 (M-P)**: role_raw=100%, research_areas=5/25, homepage=0/25, cohort_year=0/25
   - **Batch 21 (P-R)**: role_raw=100%, research_areas=3/25, homepage=2/25, cohort_year=0/25
   - **Batch 22 (P-R/cont.)**: role_raw=25/25 (100%), research_areas=2/25 (8%), homepage=2/25 (8%), cohort_year=0/25
     Notable finds: Matthew Perron (5 areas: Algorithms & Theory, Computer Architecture, Programming Languages & Software Engineering, Systems & Networking, Security & Cryptography), Benoit Marc Pit--Claudel (1 area: Systems & Networking + homepage https://pit-claudel.fr/benoit/), Charilaos Pipis (homepage https://charispipis.com/)
   - **Batch 23 (Q-Rag)**: role_raw=17/17 (100%), research_areas=1/17 (~6%), homepage=0/17 (0%), cohort_year=0/17 (0%)
     All 17 are "Graduate Student" — zero role diversity. Marianne Rakic had group-level areas from CAML group card (AI & ML, Graphics & Vision). No homepages found.
   Research areas range: 2-10/25 (8-40%) in larger batches; Batch 23 at 1/17 (~6%) extends the low end for research_areas. Homepage range: 0-9/25 (0-36%) — Batch 23 at 0/17 is the first batch with zero homepages found. Cohort_year is consistently 0/25 across all batches — never available for graduate students from the CSAIL page alone.

### Additional Fields: room, social, teaser

Beyond the core fields above, CSAIL person pages may contain:

- **room**: Present on ~30-60% of pages. Found in: `<span class='room'>TEXT</span>` or as bare text after "Room" heading. Example: `45-733`, `32-G585B`, `13-3025`.

- **social media** (LinkedIn, Twitter/X): Wrapped in `<div class="research-social-media">` with icon links. Extract platform usernames from href patterns:
  - Twitter/X: `x.com/<username>` or `twitter.com/<username>`
  - LinkedIn: `linkedin.com/in/<profile-id>`
  - GitHub: `github.com/<username>`
  These are NOT homepages — store separately under a `social` key.

- **teaser** (`field--name-field-teaser-text`): A short subtitle shown in listing cards, not the main page. May contain a research group name or lab tagline. Example: "FutureTech Research Group", "Our goal is to enable artificial intelligence..." (shared by multiple students in the same group). This is the same text for all members of a group and is NOT a personal bio — do not conflate with `description`.

- **description** (`field--name-field-description`): The personal bio paragraph. Only ~3% of graduate student pages have this (compared to ~60% of faculty). When present, it's the best source for cohort_year extraction.

### Cohort Year Extraction from Descriptions

When a description/bio paragraph is present, try these extraction strategies in order:

1. **Explicit year mentions** — "PhD student at MIT since 2022", "joined CSAIL in 2021", "started in fall 2019", "class of 2023"
2. **Ordinal year patterns** — "first-year EECS PhD student" → 2025 (inferred from current academic year), "second-year PhD student" → 2024, etc. Update YEAR_MAP annually.
3. **Degree completion years** — "BS in ... in 2018" → indicates graduated undergrad in 2018, may imply started PhD in ~2018-2019
4. **"I am a Ph.D. student at MIT CSAIL"** with no year → no cohort_year can be determined from the CSAIL page alone

**Prevalence**: Only ~3% of graduate student pages have a description paragraph, and of those, only ~30% include an extractable year.
