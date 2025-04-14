import csv

def extract_keys(csv_file):
    keys = []
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            keys.append(row["WorkItemKey"])
    return keys

if __name__ == "__main__":
    keys = extract_keys("work_items.csv")
    print(f"Extracted {len(keys)} work item keys.")
