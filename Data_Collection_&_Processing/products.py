#!/usr/bin/env python3
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import time
import re
from bs4 import BeautifulSoup
import sys

# Configuration
INPUT_FILE = 'JSONs/final_copy.json'         # JSON file with basic course info.
OUTPUT_FILE = 'JSONs/products.json'      # Output JSON file with successfully detailed info.
FAILED_FILE = 'JSONs/failed.json'         # Output JSON file for failed courses.
USER_AGENT = "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)"
HEADERS = {"User-Agent": USER_AGENT}

def create_session():
    """
    Creates and returns a requests Session object with a retry strategy to overcome 
    transient network issues and timeouts.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=5,  # Number of total retries (for network-level errors)
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1  # Wait 1, 2, 4... seconds between retries
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_page(url, session):
    """
    Fetches the URL using the provided session and returns the page content.
    Uses a 30-second timeout to allow slow servers extra time.
    """
    try:
        response = session.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_course_details(url, session):
    """
    Given a course URL, fetches the page and scrapes:
      - Description: from the <p> tag under the "Description" heading.
      - Language: from the <p> tag under the "Languages" heading.
      - Duration: numeric value from the <p> tag under the "Assessment length" heading.
    Returns a dict with these values.
    """
    page_content = fetch_page(url, session)
    if not page_content:
        return None

    soup = BeautifulSoup(page_content, 'html.parser')
    # Look for all rows that contain course details.
    detail_rows = soup.find_all("div", class_=lambda x: x and "product-catalogue-training-calendar__row" in x)
    description = ""
    language = ""
    duration = ""

    for row in detail_rows:
        h4 = row.find("h4")
        if not h4:
            continue
        heading = h4.get_text(strip=True).lower()
        p = row.find("p")
        if not p:
            continue
        p_text = p.get_text(strip=True)
        if "description" in heading:
            description = p_text
        elif "languages" in heading:
            language = p_text.rstrip(",")
        elif "assessment" in heading or "assessment length" in heading:
            # Extract numeric value from text (e.g., "Approximate Completion Time in minutes = 36")
            match = re.search(r'(\d+)', p_text)
            if match:
                duration = match.group(1)
    return {
        "description": description,
        "language": language,
        "duration": duration
    }

def save_data(updated_courses, failed_courses):
    """
    Appends updated_courses to OUTPUT_FILE and writes failed_courses to FAILED_FILE.
    """
    # Append new courses to products.json if it exists.
    products_list = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r') as infile:
                products_list = json.load(infile)
            print(f"Loaded {len(products_list)} existing records from {OUTPUT_FILE}")
        except Exception as e:
            print(f"Error loading {OUTPUT_FILE}: {e}")
            products_list = []

    # Append new records.
    products_list.extend(updated_courses)
    try:
        with open(OUTPUT_FILE, 'w') as outfile:
            json.dump(products_list, outfile, indent=4)
        print(f"\nSuccessfully appended {len(updated_courses)} records to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error writing to {OUTPUT_FILE}: {e}")

    if failed_courses:
        try:
            with open(FAILED_FILE, 'w') as failed_out:
                json.dump(failed_courses, failed_out, indent=4)
            print(f"Saved {len(failed_courses)} failed records to {FAILED_FILE}")
        except Exception as e:
            print(f"Error writing to {FAILED_FILE}: {e}")

def update_input_file(all_courses, processed_idx, updated_courses):
    """
    Updates the input file (final.json) by removing the successfully scraped courses.
    The remaining courses include:
      - Processed courses that did not scrape successfully.
      - Courses that have not been attempted yet.
    """
    # Build a set of urls for courses that succeeded.
    success_urls = {entry["url"] for entry in updated_courses}

    # Courses from the already attempted portion of the list which were not successful.
    attempted_unsuccessful = [
        course for course in all_courses[:processed_idx] if course.get("url") not in success_urls
    ]
    # Append all courses that have not yet been processed.
    not_attempted = all_courses[processed_idx:]
    remaining_courses = attempted_unsuccessful + not_attempted

    try:
        with open(INPUT_FILE, 'w') as infile:
            json.dump(remaining_courses, infile, indent=4)
        print(f"Updated {INPUT_FILE} with {len(remaining_courses)} remaining courses.")
    except Exception as e:
        print(f"Error writing to {INPUT_FILE}: {e}")

def main():
    # Load courses from the input JSON.
    try:
        with open(INPUT_FILE, 'r') as f:
            courses = json.load(f)
    except Exception as e:
        print(f"Error reading {INPUT_FILE}: {e}")
        return

    session = create_session()  # Create a session with retry logic.
    updated_courses = []  # Successfully scraped courses.
    failed_courses = []     # Courses that failed after retries.
    total = len(courses)
    processed_idx = 0     # Keep track of courses already attempted

    try:
        for idx, course in enumerate(courses, start=1):
            processed_idx = idx  # This marks the progress (1-indexed)
            url = course.get("url")
            if not url:
                print("No URL found for element, skipping.")
                continue

            print(f"Processing ({idx}/{total}): {url}")
            max_retries = 2
            attempt = 0
            details = None

            # Attempt extraction with retries.
            while attempt <= max_retries and details is None:
                details = extract_course_details(url, session)
                if details is None:
                    if attempt < max_retries:
                        attempt += 1
                        print(f"  Retry {attempt}/{max_retries} for {url}")
                        time.sleep(1)  # Pause before retrying.
                    else:
                        print(f"  Failed after {attempt + 1} attempts: {url}")
                        break
            
            if details is None:
                failed_courses.append(course)
                continue
            
            # Build the new entry with additional details.
            new_entry = {
                "url": url,
                "adaptive_support": course.get("adaptive_support", ""),
                "description": details.get("description", ""),
                "language": details.get("language", ""),
                "duration": details.get("duration", ""),
                "remote_support": course.get("remote_support", ""),
                "test_type": [course.get("test_type", "")]
            }
            updated_courses.append(new_entry)
            # Pause briefly to reduce load on the server.
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected! Saving scraped data before exit...")
        # Save the new successful and failed courses.
        save_data(updated_courses, failed_courses)
        # Update the input file to remove successfully scraped courses.
        update_input_file(courses, processed_idx, updated_courses)
        sys.exit(0)

    # After processing all courses, save data.
    save_data(updated_courses, failed_courses)
    # Update the input file with the remaining courses.
    update_input_file(courses, total, updated_courses)

if __name__ == "__main__":
    main()
