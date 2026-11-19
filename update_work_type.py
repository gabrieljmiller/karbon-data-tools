import argparse
import os
import sys
import urllib.parse

import pandas as pd
import requests
from dotenv import load_dotenv

# Bulk-update the Work Type of Karbon work items from a spreadsheet.
# Spreadsheet must have "Key" (WorkItemKey) and "Work Type" columns,
# e.g. see work_type_updates.xlsx

load_dotenv()

BASE_URL = "https://api.karbonhq.com/v3/WorkItems"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": os.getenv("bearer_token"),
    "AccessKey": os.getenv("access_key"),
}

KEY_COLUMN = "Key"
WORK_TYPE_COLUMN = "Work Type"


def load_updates(filename):
    if filename.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(filename)
    else:
        df = pd.read_csv(filename, encoding="utf-8-sig")

    missing = {KEY_COLUMN, WORK_TYPE_COLUMN} - set(df.columns)
    if missing:
        sys.exit(f"Spreadsheet is missing required column(s): {', '.join(sorted(missing))}")

    return df


def update_work_type(work_item_key, work_type):
    url = f"{BASE_URL}/{urllib.parse.quote(work_item_key)}"
    payload = {"WorkType": work_type}
    return requests.patch(url, headers=HEADERS, json=payload)


def main():
    parser = argparse.ArgumentParser(description="Bulk-update the Work Type of Karbon work items from a spreadsheet.")
    parser.add_argument(
        "spreadsheet",
        nargs="?",
        default="work_type_updates.xlsx",
        help="Path to a .xlsx/.csv file with 'Key' and 'Work Type' columns (default: work_type_updates.xlsx)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview the updates without sending any requests")
    args = parser.parse_args()

    if not os.path.exists(args.spreadsheet):
        sys.exit(f"Spreadsheet not found: {args.spreadsheet}")

    df = load_updates(args.spreadsheet)

    updated = 0
    skipped = 0
    failed = 0

    for _, row in df.iterrows():
        work_item_key = str(row[KEY_COLUMN]).strip()
        work_type = str(row[WORK_TYPE_COLUMN]).strip()

        if not work_item_key or work_item_key.lower() == "nan":
            continue
        if not work_type or work_type.lower() == "nan":
            print(f"Skipping {work_item_key}: no Work Type specified")
            skipped += 1
            continue

        if args.dry_run:
            print(f"[dry run] Would set Work Type -> '{work_type}' for {work_item_key}")
            continue

        try:
            response = update_work_type(work_item_key, work_type)
        except requests.RequestException as exc:
            print(f"Failed to update {work_item_key}: {exc}")
            failed += 1
            continue

        if response.status_code in (200, 204):
            print(f"Updated {work_item_key} -> '{work_type}'")
            updated += 1
        else:
            print(f"Failed to update {work_item_key}: {response.status_code} {response.text}")
            failed += 1

    if not args.dry_run:
        print(f"\nDone. Updated {updated}, skipped {skipped}, failed {failed}.")


if __name__ == "__main__":
    main()
