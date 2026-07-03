# Profile Photo Extraction

Default step during bio detail page followup (Phase 3). Extract `photo_url` from every member's personal page. The `photo_url` field is part of the standard JSONL output schema (see `references/output-schema.md`).

## When to use

- Always — every crawl extracts photo_url as a default field
- Do not download the image; record only the URL
- If extraction fails for a page, skip that person's photo (don't fabricate)

## General approach (all labs)

For any lab's personal pages:

1. Fetch each person's homepage (concurrent HTTP with ThreadPoolExecutor for static HTML pages; browser for JS-rendered pages)
2. Find the profile photo: first `<img>` on the page that is NOT a logo/badge/nav icon (size > 80px in either dimension, or first img with person name/userid in src)
3. Exclude images whose src contains: logo, badge, nju_, background, button, social, twitter, facebook, linkedin
4. Record the absolute URL as photo_url

## LAMDA-specific patterns

LAMDA personal pages at `www.lamda.nju.edu.cn/{userid}/` consistently have profile photos:

| Role | Photo URL pattern | Example |
|------|------------------|---------|
| Faculty (lamda.nju domain) | `/{userid}/{Name}'s HomePage@LAMDA_files/headphoto.jpg` | gaow: headphoto.jpg |
| Faculty (cs.nju domain) | First sizable img in page (varies) | zhouzh: zhouzh-nju-260302.jpg |
| PhD students (modern) | `/imgs/{userid}.jpg` | liuyr: liuyr.jpg |
| PhD students (older) | `/file/{userid}.jpg` or `/images/{userid}.jpg` | qianmz: qianmz.JPG |
| PhD students (variant) | `/pic/{userid}.jpg`, `index_files/{userid}.jpg` | various |

Success rate: ~78% (84/108). Failures are mostly external-domain pages (cs.nju.edu.cn, ai.nju.edu.cn) or default avatar.

Implementation: fetch each page with urllib + ThreadPoolExecutor(max_workers=8), extract first img where src contains the user's pinyin slug or headphoto/portrait/profile keywords.

## Stanford Profiles pattern

Most Stanford faculty have a profile page at:

```
https://profiles.stanford.edu/{name-slug}
```

The photo is usually the first `<img>` inside `<main>`.

## Robust JavaScript selectors

```javascript
function getProfilePhoto(name) {
    // Strategy 1: match alt text to the person's name
    let img = document.querySelector(`main img[alt="${name}"]`);

    // Strategy 2: match the profilephoto URL pattern
    if (!img) {
        img = document.querySelector('main img[src*="profilephoto"]');
    }

    // Strategy 3: first image in main
    if (!img) {
        img = document.querySelector('main img');
    }

    if (img && img.src && img.src.includes('profilephoto')) {
        return {
            found: true,
            src: img.src,
            width: img.naturalWidth,
            height: img.naturalHeight,
            alt: img.alt
        };
    }

    return { found: false };
}
```

## Photo URL pattern

```
https://profiles.stanford.edu/proxy/api/cap/profiles/{profileId}/resources/profilephoto/350x350.{timestamp}.jpg
```

## Accuracy

- ~95% for Stanford Profiles
- Failures usually mean the person has not uploaded a photo
- Always prefer JavaScript extraction over LLM parsing to avoid token cost

## Output

Add a `photo_url` field to the JSONL record:

```json
{
  "name": "Fei-Fei Li",
  "photo_url": "https://profiles.stanford.edu/proxy/api/cap/profiles/15052/resources/profilephoto/350x350.1550534393295.jpg"
}
```

## Generalizing to other labs

For non-Stanford sites, the same approach applies:

1. Look for the profile page
2. Use `main img` or `img[alt*="name"]` selectors
3. Verify the image URL looks like a real photo (not a logo)
4. Record dimensions if possible to avoid default/placeholder avatars
