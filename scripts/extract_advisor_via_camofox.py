#!/usr/bin/env python3
"""
Extract advisor/supervisor info from personal pages using Camofox browser API.
Pattern: create one tab, navigate through N pages, evaluate JS for rendered text.

When to use:
  - HTTP-only extraction (urllib/requests) misses supervisor info because:
    1. Page is JS-rendered and BeautifulSoup text has <a>-tag text splitting
    2. Supervisor info is embedded in biography prose, not "Supervisor:" label
    3. Page redirects to a different domain with different HTML structure

Requires: Camofox running at http://localhost:9377, pip install requests
"""
import json, re, time, requests
from collections import Counter

def run(jsonl_path, base_url='http://localhost:9377', user_id='batch_crawl', role_filter='PhD Students'):
    """Run advisor extraction via Camofox for all persons in a JSONL missing advisor field."""
    BASE = base_url
    USER_ID = user_id

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        records = [json.loads(l) for l in f if l.strip()]

    missing = [(r['name'], r['homepage']) for r in records[1:]
               if r.get('type') == 'person' and r.get('role_section') == role_filter
               and not r.get('advisor') and r.get('homepage')]

    if not missing:
        print('No records missing advisor field.')
        return records

    print(f'Targeting {len(missing)} pages via Camofox...')

    # Create a single tab (reuse across all navigations)
    resp = requests.post(f'{BASE}/tabs', json={'userId': USER_ID, 'sessionKey': 'advisor_batch'})
    tab_id = resp.json()['tabId']
    print(f'Tab created: {tab_id}')

    def extract_from_rendered(text):
        """Find advisor in rendered page text (handles both Supervisor: and prose patterns)."""
        info = {}
        patterns = [
            # Pattern 1: "under the supervision of Prof. XYZ"
            (r'(?:under\s+the\s+supervision|supervised\s+by)\s*(?:Prof\.?\s*)?([A-Z][a-zA-Z\s.-]{2,50}?)(?:\s*[.,;]|\s*$)',
             lambda m: m.group(1).strip()),
            # Pattern 2: "Supervisor: ..."
            (r'Supervisor[:\s]+(?:Prof\.?\s*)?([A-Z][a-zA-Z\s.-]{2,50})',
             lambda m: m.group(1).strip()),
            # Pattern 3: "Co-supervisor: ..."
            (r'Co-supervisor[:\s]+(?:Prof\.?\s*)?([A-Z][a-zA-Z\s.-]{2,50})',
             lambda m: m.group(1).strip()),
        ]
        for pat, extract in patterns:
            m = re.search(pat, text)
            if m:
                val = extract(m)
                val = re.sub(r'\s+', ' ', val).strip().rstrip('.,; ')
                if any(c.isalpha() for c in val) and len(val) >= 2:
                    if 'Co-supervisor' in pat:
                        info['co_advisor'] = val
                    else:
                        info['advisor'] = val
                    break
        return info

    results = {}
    for i, (name, url) in enumerate(missing):
        try:
            resp = requests.post(f'{BASE}/tabs/{tab_id}/navigate',
                                 json={'url': url, 'userId': USER_ID, 'sessionKey': 'advisor_batch'},
                                 timeout=15)
            if resp.status_code != 200:
                continue
            time.sleep(0.8)

            resp = requests.post(f'{BASE}/tabs/{tab_id}/evaluate',
                                 json={'userId': USER_ID, 'sessionKey': 'advisor_batch',
                                       'expression': 'document.body.innerText'},
                                 timeout=15)
            if resp.status_code == 200 and resp.json().get('result'):
                text = resp.json()['result']
                info = extract_from_rendered(text)
                if info.get('advisor'):
                    results[name] = info

            if (i + 1) % 10 == 0:
                print(f'  [{i+1}/{len(missing)}] Found: {len(results)}')
        except Exception as e:
            continue

    # Clean up tab
    requests.delete(f'{BASE}/tabs/{tab_id}', params={'userId': USER_ID})

    print(f'\nFound {len(results)} more advisor entries')

    # Merge into records
    for r in records:
        if r.get('name') in results:
            for k, v in results[r['name']].items():
                r[k] = v

    # Clean common extraction artifacts
    for r in records:
        adv = r.get('advisor')
        if adv:
            # Remove title prefixes
            for prefix in ['Professor ', 'Prof. ', 'Prof ', 'Associate Professor ', 'Associate Prof ']:
                if adv.startswith(prefix):
                    adv = adv[len(prefix):]
            # Remove "essor" fragment (from "Professor" split across lines)
            if adv == 'essor' or not any(c.isalpha() for c in adv):
                del r['advisor']
                continue
            r['advisor'] = adv.strip().rstrip('.').rstrip(' ,')

    # Save
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    total = sum(1 for r in records[1:] if r.get('type') == 'person' and r.get('role_section') == role_filter)
    with_adv = sum(1 for r in records[1:] if r.get('type') == 'person' and r.get('role_section') == role_filter and r.get('advisor'))
    print(f'\nAdvisor coverage: {with_adv}/{total}')

    # Print by advisor
    adv_counts = Counter()
    for r in records[1:]:
        if r.get('advisor'):
            adv_counts[r['advisor']] += 1
    print('\nStudents per advisor:')
    for a, c in adv_counts.most_common():
        print(f'  {a}: {c}')

    return records

if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else 'output/lamda_lab/_2026-07-03.jsonl'
    run(path)
