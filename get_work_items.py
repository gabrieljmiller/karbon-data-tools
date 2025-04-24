import requests
import os
import csv
from dotenv import load_dotenv

# get work items by client
load_dotenv()

BEARER_TOKEN = os.getenv("bearer_token")
ACCESS_KEY = os.getenv("access_key")
CLIENT_KEY = os.getenv("client_key")
BASE_URL = "https://api.karbonhq.com/v3/WorkItems"

headers = {
    'Accept': 'application/json',
    'Authorization': os.getenv("bearer_token"),
    'AccessKey': os.getenv("access_key")
}

def get_work_items_by_client(client_key):
    work_items = []
    url = f"{BASE_URL}?$filter=ClientKey eq '{client_key}'"

    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break

        data = response.json()
        work_items.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    return work_items

def save_work_items_to_csv(work_items, filename="work_items.csv"):
    if not work_items:
        print("No work items found.")
        return

    fieldnames = sorted(work_items[0].keys())
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(work_items)

    print(f"Saved {len(work_items)} work items to {filename}.")

if __name__ == "__main__":
    work_items = get_work_items_by_client(CLIENT_KEY)
    save_work_items_to_csv(work_items)
