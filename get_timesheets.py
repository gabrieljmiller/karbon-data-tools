import requests
import os
import csv
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.karbonhq.com/v3/Timesheets"

headers = {
    'Accept': 'application/json',
    'Authorization': os.getenv("bearer_token"),
    'AccessKey': os.getenv("access_key")
}

def get_all_timesheets():
    timesheets = []
    url = BASE_URL
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break

        data = response.json()
        timesheets.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
    return timesheets

def save_timesheets_to_csv(timesheets, filename="timesheets.csv"):
    if not timesheets:
        print("No timesheets to write.")
        return

    fieldnames = sorted(timesheets[0].keys())

    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(timesheets)

    print(f"Saved {len(timesheets)} timesheets to {filename}.")

if __name__ == "__main__":
    all_timesheets = get_all_timesheets()
    save_timesheets_to_csv(all_timesheets)
