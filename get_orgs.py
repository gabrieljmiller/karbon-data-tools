import http.client
import os
from dotenv import load_dotenv
import json
import pandas as pd
import re

# Load environment variables from .env file
load_dotenv()

conn = http.client.HTTPSConnection("api.karbonhq.com")
payload = ''
headers = {
    'Accept': 'application/json',
    'Authorization': os.getenv("bearer_token"),
    'AccessKey': os.getenv("access_key")
}

def get_description(org_key: str) -> str:
    conn.request("GET", f"/v3/Organizations/{org_key}", headers=headers)
    res  = conn.getresponse()
    body = res.read()

    # ----- 1) non-200 means org is missing or forbidden -------------------
    if res.status != 200:
        print(f"   ⚠️  {org_key}: GET /Organizations → {res.status}")
        return ""

    # ----- 2) empty body or the literal word 'null' -----------------------
    if not body or body.strip() == b"null":
        print(f"   ⚠️  {org_key}: organisation record is empty")
        return ""

    # ----- 3) decode JSON safely -----------------------------------------
    try:
        resp_json = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        print(f"   ⚠️  {org_key}: invalid JSON in response")
        return ""

    # ----- 4) dig out the description if present -------------------------
    entity_desc = resp_json.get("EntityDescription") or {}
    text = entity_desc.get("Text", "")

    if not text:
        print(f"   ℹ️  {org_key}: no description field")
    return text

def get_cf_value(data:dict, cf_name:str):
    for cf in data.get("CustomFieldValues", []):
        if cf.get("Name") == cf_name:
            return cf.get("Value")
    return None

def main():
    df = pd.read_csv("organizations.csv", encoding="utf-8-sig")
    output_data = []

    for _, row in df.iterrows():  # loop through every row
        org_key = str(row["Key"]) # Ensure org_key is a string
        org_name = str(row["Name"])  # Ensure org_name is a string

        if pd.isna(org_key) or org_key.strip() == "":  # skip blank keys, just in case
            print("Skipping empty org_key.")
            continue

        print(f"Processing org_key: {org_key}")

        # Fetch the full organization details
        conn.request("GET", f"/v3/Organizations/{org_key}", headers=headers)
        res = conn.getresponse()
        body = res.read()

        org_description = ""
        accounting_software = ""

        if res.status == 200 and body.strip() != b"null":
            try:
                org_data = json.loads(body.decode("utf-8"))

                # Get description
                entity_desc = org_data.get("EntityDescription") or {}
                org_description = entity_desc.get("Text", "")
                if not org_description:
                    print(f"   ℹ️  {org_key}: no description field found in full organization data.")

                # Get "Accounting Software" custom field
                accounting_software = get_cf_value(org_data, "Accounting Software")
                if not accounting_software:
                    print(f"   ℹ️  {org_key}: 'Accounting Software' custom field not found or empty.")

            except json.JSONDecodeError:
                print(f"   ⚠️  {org_key}: Invalid JSON in organization details response.")
            except Exception as e:
                print(f"   ❌  An error occurred for {org_key}: {e}")
        else:
            print(f"   ⚠️  {org_key}: Failed to fetch organization details. Status: {res.status}")

        output_data.append({
            "Org_Key": org_key,
            "Description": org_description,
            "Accounting Software": accounting_software,
            "Name": org_name
        })

    # Create a new DataFrame from the collected data
    output_df = pd.DataFrame(output_data)

    # Save the new DataFrame to a CSV file
    output_filename = "organization_details.csv"
    output_df.to_csv(output_filename, index=False, encoding="utf-8-sig")
    print(f"\nSuccessfully extracted data and saved to {output_filename}")

if __name__ == "__main__":
    main()