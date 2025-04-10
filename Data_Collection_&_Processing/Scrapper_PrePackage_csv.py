#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv

# === CONFIGURATION ===
INPUT_FILE      = 'pre-package_Cat.txt'     # path to your input list of URLs (one per line)
OUTPUT_FILE     = 'Cat1.csv'   # path to the output CSV

def scrape_product_page(page_url):
    """
    Given a product page URL, returns a dict with
    Product, Description, Job Level, Language, Assessment Length.
    """
    resp = requests.get(page_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # 1) Product title
    product = soup.find('h1').get_text(strip=True) if soup.find('h1') else ''

    # 2) Initialize fields
    description = job_levels = languages = assessment_length = ''

    # 3) Walk through each info‑row and pick out the right one by its <h4>
    rows = soup.find_all('div', class_='product-catalogue-training-calendar__row typ')
    for row in rows:
        hdr = row.find('h4')
        if not hdr:
            continue
        key = hdr.get_text(strip=True).lower()
        para = row.find('p')
        text = para.get_text(strip=True) if para else ''

        if key == 'description':
            description = text
        elif key.startswith('job level'):
            job_levels = text
        elif key.startswith('languages'):
            languages = text
        elif key.startswith('assessment length'):
            assessment_length = text

    return {
        'Product': product,
        'Description': description,
        'Job Level': job_levels,
        'Language': languages,
        'Assessment Length': assessment_length,
    }

def main():
    # 1) Read all pages
    with open(INPUT_FILE, 'r') as f:
        pages = [line.strip() for line in f if line.strip()]

    records = []
    for page in pages:
        print(f"→ Scraping {page}")
        try:
            rec = scrape_product_page(page)
            records.append(rec)
        except Exception as e:
            print(f"   ERROR on {page}: {e}")

    # 2) Write out CSV
    fieldnames = ['Product', 'Description', 'Job Level', 'Language', 'Assessment Length']
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvf:
        writer = csv.DictWriter(csvf, fieldnames=fieldnames)
        writer.writeheader()
        for row in records:
            writer.writerow(row)

    print(f"\nDone! {len(records)} records written to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()