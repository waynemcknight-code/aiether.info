#!/usr/bin/env python3
"""
fetch_corruption_watch.py

Pulls posts from the Corruption Watch Texas RSS feed and generates
Hugo markdown files in content/corruption-watch/.

Usage:
    python3 fetch_corruption_watch.py

Run from anywhere; CONTENT_DIR can be overridden via env var.
"""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FEED_URL = 'https://rss.app/feeds/xVoBopWv7bZSdBrs.json'
CONTENT_DIR = Path(os.environ.get(
    'CONTENT_DIR',
    '/home/wayne/aiether.info/content/corruption-watch'
))
PAGE_URL = 'https://www.facebook.com/people/Corruption-Watch-Texas/61571888697510/'
PAGE_NAME = 'Corruption Watch — Texas'


def slugify(text: str, maxlen: int = 60) -> str:
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text.strip())
    text = text[:maxlen].rstrip('-')
    return text.lower()


def fetch_feed() -> dict:
    req = urllib.request.Request(FEED_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def parse_date(date_str: str) -> datetime:
    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))


def make_filename(dt: datetime, title: str) -> str:
    stamp = dt.strftime('%Y-%m-%d')
    slug = slugify(title) or 'post'
    return f'{stamp}-{slug}.md'


def post_to_markdown(item: dict) -> str:
    title = (item.get('title') or '').strip()
    url = item.get('url') or ''
    date_str = item.get('date_published') or ''
    content = (item.get('content_text') or item.get('content_html') or '').strip()
    image = item.get('image') or ''

    dt = parse_date(date_str) if date_str else datetime.now(timezone.utc)
    iso_date = dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    # Escape any quotes in title for YAML
    safe_title = title.replace('"', '\\"')

    lines = [
        '---',
        f'title: "{safe_title}"',
        f'date: {iso_date}',
        'draft: false',
        f'externalUrl: "{url}"',
        f'categories: ["Corruption Watch"]',
        '---',
        '',
    ]

    if image:
        lines += [f'![]({image})', '']

    lines += [
        content,
        '',
        '---',
        '',
        f'*Originally posted on [{PAGE_NAME}]({PAGE_URL}). '
        f'[View original post]({url}).*',
        '',
    ]

    return '\n'.join(lines)


def main():
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    print(f'Fetching {FEED_URL} ...')
    feed = fetch_feed()
    items = feed.get('items', [])
    print(f'Feed: {feed.get("title")}  —  {len(items)} items')

    added = skipped = 0

    for item in items:
        title = (item.get('title') or 'post').strip()
        date_str = item.get('date_published') or ''
        dt = parse_date(date_str) if date_str else datetime.now(timezone.utc)
        filename = make_filename(dt, title)
        dest = CONTENT_DIR / filename

        if dest.exists():
            print(f'  SKIP  {filename}')
            skipped += 1
            continue

        md = post_to_markdown(item)
        dest.write_text(md, encoding='utf-8')
        print(f'  ADD   {filename}')
        added += 1

    print(f'\nDone. Added {added}, skipped {skipped}.')
    if added:
        print(f'\nRebuild Hugo to publish:')
        print(f'  cd /home/wayne/aiether.info && hugo --cleanDestinationDir --minify')


if __name__ == '__main__':
    main()
