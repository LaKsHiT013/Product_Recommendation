#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# === CONFIGURATION ===
INPUT_FILE   = 'individual_assessment.txt'   # path to your list of pages
OUTPUT_FILE  = 'individual_assessment_Cat.txt'     # where to write the extracted URLs
BASE_URL     = 'https://www.shl.com'
HEADER_TEXT  = 'Individual Test Solutions'  # the table‑header to target

def extract_individual_links(page_url):
    """
    Fetches page_url, finds the table whose first <th> is HEADER_TEXT,
    and returns a list of full URLs from the <a> tags in that first column.
    """
    resp = requests.get(page_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Find the table by matching the header text
    table = None
    for tbl in soup.find_all('table'):
        th = tbl.find('th', string=lambda t: t and t.strip() == HEADER_TEXT)
        if th:
            table = tbl
            break

    if not table:
        return []

    links = []
    # Skip the header row, then for each <tr> grab the first-column <a>
    for tr in table.find_all('tr')[1:]:
        td = tr.find('td', class_='custom__table-heading__title')
        if not td:
            continue
        a = td.find('a', href=True)
        if a:
            full = urljoin(page_url, a['href'])
            links.append(full)
    return links

def main():
    all_links = []

    # 1) Read your list of pages
    with open(INPUT_FILE, 'r') as f:
        pages = [line.strip() for line in f if line.strip()]

    # 2) For each page, extract the individual‑test links
    for page in pages:
        if page.startswith('/'):
            page = urljoin(BASE_URL, page)
        print(f"→ scraping {page}")
        try:
            found = extract_individual_links(page)
            print(f"   found {len(found)} links")
            all_links.extend(found)
        except Exception as e:
            print(f"   ERROR on {page}: {e}")

    # 3) Write them all out
    with open(OUTPUT_FILE, 'w') as out:
        for link in all_links:
            out.write(link + '\n')

    print(f"\nDone! {len(all_links)} links written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
