import requests
import os
import csv
from dotenv import load_dotenv

load_dotenv()

BEARER_TOKEN = os.getenv("bearer_token")
ACCESS_KEY = os.getenv("access_key")

HEADERS = {
    "Authorization": BEARER_TOKEN,
    "AccessKey": ACCESS_KEY,
    "Accept": "application/json"
}

BASE_URL = "https://api.karbonhq.com/v3/Timesheets"
OUTPUT_FILE = "all_time_entries.csv"

def fetch_all_time_entries():
    all_entries = []
    url = f"{BASE_URL}?$expand=TimeEntries"

    while url:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break

        data = response.json()
        timesheets = data.get("value", [])

        for sheet in timesheets:
            timesheet_key = sheet.get("TimesheetKey")
            timesheet_date = sheet.get("StartDate")
            for entry in sheet.get("TimeEntries", []):
                entry["ParentTimesheetKey"] = timesheet_key
                entry["TimesheetStartDate"] = timesheet_date
                # If the entry has a 'Date' field, include it explicitly
                all_entries.append(entry)

        url = data.get("@odata.nextLink")

    return all_entries

def save_to_csv(entries, filename):
    if not entries:
        print("No entries found.")
        return

    fieldnames = list(entries[0].keys())
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)

    print(f"Saved {len(entries)} entries to {filename}")

if __name__ == "__main__":
    entries = fetch_all_time_entries()
    save_to_csv(entries, OUTPUT_FILE)
