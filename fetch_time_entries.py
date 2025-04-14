import requests
import os
import csv
from dotenv import load_dotenv
from extract_workitem_keys import extract_keys

load_dotenv()

BEARER_TOKEN = os.getenv("bearer_token")
ACCESS_KEY = os.getenv("access_key")

HEADERS = {
    "Authorization": BEARER_TOKEN,
    "AccessKey": ACCESS_KEY,
    "Accept": "application/json"
}

BASE_URL = "https://api.karbonhq.com/v3/TimeEntries"

# EDIT THESE
START_DATE = "2024-01-01T00:00:00Z"
END_DATE = "2024-03-31T23:59:59Z"

def build_filter(keys):
    chunks = [keys[i:i+20] for i in range(0, len(keys), 20)]  # Split to avoid overly long URL
    filters = []
    for chunk in chunks:
        key_list = ", ".join([f"'{key}'" for key in chunk])
        filters.append(f"WorkItemKey in ({key_list})")
    combined = " or ".join(filters)
    return f"EntryDate ge {START_DATE} and EntryDate le {END_DATE} and ({combined})"

def fetch_entries(work_item_keys):
    entries = []
    chunks = [work_item_keys[i:i+20] for i in range(0, len(work_item_keys), 20)]

    for chunk in chunks:
        key_list = ", ".join([f"'{key}'" for key in chunk])
        filter_str = f"EntryDate ge {START_DATE} and EntryDate le {END_DATE} and WorkItemKey in ({key_list})"
        url = f"{BASE_URL}?$filter={filter_str}"

        while url:
            response = requests.get(url, headers=HEADERS)
            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
                break
            data = response.json()
            entries.extend(data.get("value", []))
            url = data.get("@odata.nextLink")

    return entries


def save_to_csv(entries, filename="time_entries.csv"):
    if not entries:
        print("No entries found.")
        return
    fieldnames = sorted(entries[0].keys())
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)
    print(f"Saved {len(entries)} time entries to {filename}.")

if __name__ == "__main__":
    keys = extract_keys("work_items.csv")
    entries = fetch_entries(keys)
    save_to_csv(entries)
