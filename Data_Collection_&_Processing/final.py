#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os
import sys
import uuid  # For generating unique IDs

# === CONFIGURATION ===
INPUT_FILE = 'JSONs/final_copy.json'      # Input JSON file containing a list of courses.
OUTPUT_FILE = 'JSONs/products.json'   # Output JSON file for successfully scraped courses.
FAILED_FILE = 'JSONs/failed.json'     # Output JSON file for courses that fail processing.
TIMEOUT = 5                          # Reduced timeout (in seconds) to avoid long waits.
USER_AGENT = "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)"
HEADERS = {"User-Agent": USER_AGENT}


def scrape_course_page(url):
    """
    Given a course URL, fetch the page (using a lower timeout to avoid long delays)
    and parse its details using BeautifulSoup. Returns a dict with:
      - description: The text under the "Description" heading.
      - language: The text under the "Languages" heading (with trailing comma removed).
      - duration: The first numeric value found in the text under the "Assessment Length" heading.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
    except Exception as e:
        raise Exception(f"Request error: {e}")

    soup = BeautifulSoup(response.text, 'html.parser')
    # Initialize fields.
    description = ""
    language = ""
    duration = ""

    # Find all divs that contain course details.
    rows = soup.find_all("div", class_=lambda c: c and "product-catalogue-training-calendar__row" in c)
    for row in rows:
        h4 = row.find("h4")
        if not h4:
            continue
        key = h4.get_text(strip=True).lower()
        p = row.find("p")
        if not p:
            continue
        text = p.get_text(strip=True)
        if "description" in key:
            description = text
        elif "languages" in key:
            language = text.rstrip(',')
        elif "assessment" in key or "assessment length" in key:
            m = re.search(r'(\d+)', text)
            if m:
                duration = m.group(1)
    return {
        "description": description,
        "language": language,
        "duration": duration
    }


def load_json_file(filename):
    """Loads JSON data from a given file."""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def append_to_json(filename, records):
    """
    Appends new records (list of dicts) to an existing JSON file.
    If the file doesn't exist or is unreadable, it creates a new one.
    """
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            existing = []
    else:
        existing = []

    existing.extend(records)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=4)


def update_input_file(all_courses, successful_urls):
    """
    Updates the input JSON file (final.json) by removing successfully processed courses.
    Remaining courses include those that failed or were not attempted.
    """
    remaining = [course for course in all_courses if course.get("url") not in successful_urls]
    try:
        with open(INPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(remaining, f, indent=4)
        print(f"Updated {INPUT_FILE}: {len(remaining)} courses remaining.")
    except Exception as e:
        print(f"Error updating {INPUT_FILE}: {e}")


def main():
    # Load courses from the input JSON.
    try:
        courses = load_json_file(INPUT_FILE)
    except Exception as e:
        print(f"Error reading {INPUT_FILE}: {e}")
        sys.exit(1)

    success_records = []     # List of successfully scraped course details.
    failed_courses = []      # Courses that could not be scraped.
    successful_urls = set()  # Track URLs processed successfully.
    total = len(courses)
    print(f"Total courses to process: {total}")

    try:
        for idx, course in enumerate(courses, start=1):
            url = course.get("url")
            if not url:
                print("No URL found, skipping.")
                continue

            print(f"Processing {idx}/{total}: {url}")
            try:
                details = scrape_course_page(url)
            except Exception as ex:
                print(f"  ERROR on {url}: {ex}")
                failed_courses.append(course)
                continue

            # Build the new entry using the original course info and the scraped details.
            # A unique "id" is generated for each record.
            new_entry = {
                "id": str(uuid.uuid4()),
                "url": url,
                "adaptive_support": course.get("adaptive_support", ""),
                "description": details.get("description", ""),
                "language": details.get("language", ""),
                "duration": details.get("duration", ""),
                "remote_support": course.get("remote_support", ""),
                "test_type": [course.get("test_type", "")]
            }
            success_records.append(new_entry)
            successful_urls.add(url)
            # Short delay to lessen rapid-fire requests.
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected! Saving current progress...")

    # Append newly scraped courses to the output JSON.
    if success_records:
        append_to_json(OUTPUT_FILE, success_records)
        print(f"Appended {len(success_records)} successful records to {OUTPUT_FILE}")
    else:
        print("No successful records to save.")

    # Append failed courses to a separate JSON.
    if failed_courses:
        append_to_json(FAILED_FILE, failed_courses)
        print(f"Appended {len(failed_courses)} failed records to {FAILED_FILE}")

    # Update the input JSON file to remove successfully processed courses.
    if successful_urls:
        update_input_file(courses, successful_urls)


if __name__ == "__main__":
    main()
