import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

INPUT_FILE = 'pre-package.txt'
OUTPUT_FILE = 'pre-package.json'
BASE_URL = 'https://www.shl.com'

TEST_TYPE_MAPPING = {
    'A': "Ability & Aptitude",
    'B': "Biodata & Situational Judgment",
    'C': "Competences",
    'D': "Development & 360",
    'E': "Assessment Exercise",
    'K': "Knowledge & Skills",
    'P': "Personality & Behaviour",
    'S': "Stimulations"
}

def scrape_table_data(page_url):

    try:
        resp = requests.get(page_url)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {page_url}: {e}")
        return []
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    table_container = soup.find("div", class_=lambda cls: cls and "custom__table-wrapper" in cls)
    if not table_container:
        table_container = soup.find("div", class_="custom__table-responsive")
    
    if not table_container:
        print(f"No table container found in {page_url}")
        return []
    
    table = table_container.find("table")
    if not table:
        print(f"No table found in container at {page_url}")
        return []
    
    tbody = table.find("tbody")
    if tbody:
        rows = tbody.find_all("tr")
    else:
        print(f"No tbody found in table at {page_url}. Using table element directly.")
        rows = table.find_all("tr")
    
    data = []
    for row in rows:
        if row.find("th"):
            continue
        
        cells = row.find_all("td")
        if len(cells) < 4:
            continue

        a_tag = cells[0].find("a", href=True)
        if a_tag:
            link = a_tag['href'].strip()
            full_url = urljoin(BASE_URL, link)
        else:
            full_url = ""
        
        remote_span = cells[1].find("span", class_="catalogue__circle -yes")
        remote_support = "Yes" if remote_span else "No"
        
        adaptive_span = cells[2].find("span", class_="catalogue__circle -yes")
        adaptive_support = "Yes" if adaptive_span else "No"
        
        key_spans = cells[3].find_all("span", class_="product-catalogue__key")
        test_types_found = []
        for span in key_spans:
            abbr = span.get_text(strip=True)
            if abbr in TEST_TYPE_MAPPING:
                test_types_found.append(TEST_TYPE_MAPPING[abbr])
        
        test_types_unique = list(dict.fromkeys(test_types_found))
        test_type_str = ", ".join(test_types_unique)
        

        row_data = {
            "url": full_url,
            "remote_support": remote_support,
            "adaptive_support": adaptive_support,
            "test_type": test_type_str
        }
        data.append(row_data)
        
    return data

def main():
    all_data = []

    try:
        with open(INPUT_FILE, 'r') as f:
            pages = [line.strip() for line in f if line.strip()]
    except IOError as e:
        print(f"Error reading {INPUT_FILE}: {e}")
        return

    for page in pages:
        if page.startswith('/'):
            page = urljoin(BASE_URL, page)
        print(f"→ Scraping {page} ...")
        try:
            page_data = scrape_table_data(page)
            print(f"   Found {len(page_data)} rows")
            all_data.extend(page_data)
        except Exception as ex:
            print(f"   ERROR on {page}: {ex}")
    
    try:
        with open(OUTPUT_FILE, 'w') as outfile:
            json.dump(all_data, outfile, indent=4)
        print(f"\nDone! {len(all_data)} rows written to {OUTPUT_FILE}")
    except IOError as e:
        print(f"Error writing to {OUTPUT_FILE}: {e}")

if __name__ == "__main__":
    main()
