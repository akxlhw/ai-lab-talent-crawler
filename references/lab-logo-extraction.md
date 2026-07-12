# Lab Logo Extraction

Extract the representative logo image for each AI lab, used in lab cards / directory listings.

## When to use

- User wants to display a lab card with a logo image
- Default part of the crawl workflow (not optional)

## Sources (in priority order)

1. **Favicon** (`<link rel="icon" href="...">`)
2. **Header logo** (`<img>` with "logo" in `src` or `alt`)
3. **Lab acronym image** (e.g., `lamda.png`, `sail.png`, `openai.png`)
4. **First large non-banner image** in header/main navigation

## Heuristic

```javascript
function getLabLogo(docUrl) {
    // Strategy 1: favicon
    let favicon = document.querySelector('link[rel*="icon"]');
    if (favicon && favicon.href) return favicon.href;

    // Strategy 2: img with "logo" in src/alt
    let logo = document.querySelector('img[src*="logo" i], img[alt*="logo" i]');
    if (logo && logo.src) return logo.src;

    // Strategy 3: img with lab acronym in src (e.g., lamda.png, sail.png)
    let labName = window.location.hostname.split('.')[0];
    let acronymImg = document.querySelector(`img[src*="${labName}" i]`);
    if (acronymImg && acronymImg.src) return acronymImg.src;

    // Strategy 4: first image in header that is square-ish and not tiny
    let header = document.querySelector('header, .navbar, .site-header, nav');
    if (header) {
        let imgs = header.querySelectorAll('img');
        for (let img of imgs) {
            if (img.naturalWidth >= 40 && img.naturalHeight >= 40 && img.naturalWidth < 400) {
                return img.src;
            }
        }
    }

    return null;
}
```

## Output

Store in a lab-level metadata file (not per-person):

```json
{
  "lab_name": "南京大学LAMDA实验室",
  "lab_slug": "lamda_lab",
  "homepage": "http://www.lamda.nju.edu.cn/",
  "logo_url": "http://www.lamda.nju.edu.cn/images/pub/lamda.png",
  "collected_at": "2026-07-03T05:20:00Z"
}
```

Also add `logo_url` to the lab's entry in `labs.yaml` for reuse across crawls.

## Fallback

If no logo is found, omit the field. Never fabricate a URL.
