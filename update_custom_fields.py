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

# one regex per label, anchored to “start of line” to avoid false matches
_PATTERNS = {
    "accounting_software": re.compile(
        r"^Accounting Software[ \t]*:[ \t]*([^\r\n]*)", re.I | re.M
    ),
    "admin_password": re.compile(
        r"^Admin Password[ \t]*:[ \t]*([^\r\n]*)",      re.I | re.M
    ),
    "ras_id": re.compile(
        r"^RAS ID[ \t]*:[ \t]*([^\r\n]*)",              re.I | re.M
    ),
}

def get_description(org_key: str) -> str:
    conn.request("GET", f"/v3/Organizations/{org_key}", headers=headers)
    res  = conn.getresponse()
    body = res.read()

    # ----- 1) non‑200 means org is missing or forbidden -------------------
    if res.status != 200:
        print(f"  ⚠️  {org_key}: GET /Organizations → {res.status}")
        return ""

    # ----- 2) empty body or the literal word 'null' -----------------------
    if not body or body.strip() == b"null":
        print(f"  ⚠️  {org_key}: organisation record is empty")
        return ""

    # ----- 3) decode JSON safely -----------------------------------------
    try:
        resp_json = json.loads(body.decode("utf‑8"))
    except json.JSONDecodeError:
        print(f"  ⚠️  {org_key}: invalid JSON in response")
        return ""

    # ----- 4) dig out the description if present -------------------------
    entity_desc = resp_json.get("EntityDescription") or {}
    text = entity_desc.get("Text", "")

    if not text:
        print(f"  ℹ️  {org_key}: no description field")
    return text

def list_custom_fields():
    conn.request("GET", f"/v3/CustomFields", payload, headers)
    res = conn.getresponse()
    data = res.read()
    resp_json = json.loads(data.decode("utf-8"))
    cf_keys = []
    cf_names = []
    for cf in resp_json["value"]:
        cf_keys.append(cf["Key"])
        cf_names.append(cf["Name"])
    cf_mp = dict(zip(cf_names, cf_keys))
    return cf_mp

def get_custom_fields(org_key):
    conn.request("GET", f"/v3/CustomFieldValues/{org_key}", payload, headers)
    res = conn.getresponse()
    data = res.read()
    resp_json = json.loads(data.decode("utf-8"))
    return resp_json

def extract_cf_from_description(description: str) -> dict[str, str | None]:
    out = {}
    for key, pattern in _PATTERNS.items():
        m = pattern.search(description)
        if m:
            val = m.group(1).strip()           # '' if nothing after colon
            out[key] = val or None             # turn '' into None
        else:
            out[key] = None
    return out

def get_cf_value(data:dict, cf_name:str):
    for cf in data.get("CustomFieldValues", []):
        if cf.get("Name") == cf_name:
            return cf.get("Value")
    return None

def update_qb_admin_password(org_key):
    # 1. Get current value
    current = get_cf_value(get_custom_fields(org_key), "QB Admin Password")
    if current:                      # already set → bail out
        print(f"Field already populated: {current}")
        return

    # 2. Pull it from the description
    description  = get_description(org_key)
    if description is None:
        print(f"No description found for {org_key}")
        return
    new_pw       = extract_cf_from_description(description).get("admin_password")
    if not new_pw:
        print("No QB Admin Password found in description")
        return

    # 3. Build Karbon‑compliant payload
    payload = {
        "EntityKey": org_key,
        "CustomFieldValues": [
            {
                "Key":   "bT3FHvnxFCg",          # key of the CF definition
                "Name":  "QB Admin Password",
                "Type":  "Text",
                "Value": [new_pw]                # ← must be a list
            }
        ]
    }
    body = json.dumps(payload).encode("utf-8")   # bytes
    headers["Content-Type"] = "application/json" # add/overwrite

    # 4. Send request
    conn.request("PUT",
                 f"/v3/CustomFieldValues/{org_key}",
                 body=body,
                 headers=headers)

    res = conn.getresponse()
    print(f"Update status: {res.status} {res.reason}")
    print(res.read().decode())
        
def update_accounting_software(org_key):
    ## NOTE this does not work because this field is limited to 4 values
    # 1. Get current value
    current = get_cf_value(get_custom_fields(org_key), "Accounting Software")
    if current:                      # already set → bail out
        print(f"Field already populated: {current}")
        return

    # 2. Pull it from the description
    description  = get_description(org_key)
    if description is None:
        print(f"No description found for {org_key}")
        return
    new_pw       = extract_cf_from_description(description).get("accounting_software")
    if not new_pw:
        print("No Accounting Software found in description")
        return

    # 3. Build Karbon‑compliant payload
    payload = {
        "EntityKey": org_key,
        "CustomFieldValues": [
            {
                "Key":   "36yxh2LSmwRY",          # key of the CF definition
                "Name":  "Accounting Software",
                "Type":  "Text",
                "Value": [new_pw]                # ← must be a list
            }
        ]
    }
    body = json.dumps(payload).encode("utf-8")   # bytes
    headers["Content-Type"] = "application/json" # add/overwrite

    # 4. Send request
    conn.request("PUT",
                 f"/v3/CustomFieldValues/{org_key}",
                 body=body,
                 headers=headers)

    res = conn.getresponse()
    print(f"Update status: {res.status} {res.reason}")
    print(res.read().decode())

def update_ras_id(org_key):
    # 1. Get current value
    current = get_cf_value(get_custom_fields(org_key), "RAS ID")
    if current:                      # already set → bail out
        print(f"Field already populated: {current}")
        return

    # 2. Pull it from the description
    description  = get_description(org_key)
    if description is None:
        print(f"No description found for {org_key}")
        return
    new_pw       = extract_cf_from_description(description).get("ras_id")
    if not new_pw:
        print("No RAS ID found in description")
        return

    # 3. Build Karbon‑compliant payload
    payload = {
        "EntityKey": org_key,
        "CustomFieldValues": [
            {
                "Key":   "3gBCy74scz6T",          # key of the CF definition
                "Name":  "RAS ID",
                "Type":  "Text",
                "Value": [new_pw]                # ← must be a list
            }
        ]
    }
    body = json.dumps(payload).encode("utf-8")   # bytes
    headers["Content-Type"] = "application/json" # add/overwrite

    # 4. Send request
    conn.request("PUT",
                 f"/v3/CustomFieldValues/{org_key}",
                 body=body,
                 headers=headers)

    res = conn.getresponse()
    print(f"Update status: {res.status} {res.reason}")
    print(res.read().decode())

def update_from_csv(org_name, org_key):
    # get values from csv
    df = pd.read_csv("custom_fields_to_update.csv", encoding="utf-8-sig")
    match = df[df["Account Name"] == org_name]

    if match.empty:
        return None
    
    fields = ['Entity Type', 'Back Up Method', 'Closing Date Password']
    
    entity_type = match['Entity Type'].iloc[0]
    backup_method = match['Back Up Method'].iloc[0]

    #build payload
    payload = {
        "EntityKey": org_key,
        "CustomFieldValues": [
            {
                "Key":   "DRrWHybmW1V", 
                "Name":  "Backup Method",
                "Type":  "Text",
                "Value": [backup_method]
            },
            {
                "Key":   "fb94WsjszXM", 
                "Name":  "Entity Type",
                "Type":  "List: Single",
                "Value": [entity_type]
            }
        ]
    }

    # send request
    body = json.dumps(payload).encode("utf-8")
    headers["Content-Type"] = "application/json"

    conn.request("PUT",
                 f"/v3/CustomFieldValues/{org_key}",
                 body=body,
                 headers=headers)
    
    res = conn.getresponse()
    print(f"Update status: {res.status} {res.reason}")
    print(res.read().decode())

def main():
    df = pd.read_csv("organizations.csv", encoding="utf-8-sig")

    for _, row in df.iterrows():                # loop through every row
        org_key  = row["Key"]
        org_name = row["Name"]

        if pd.isna(org_key):                    # skip blank keys, just in case
            continue

        print(f"Updating → {org_name}  ({org_key})")
        # update_qb_admin_password(org_key)
        update_from_csv(org_name, org_key)

# print(list_custom_fields())
main()

## Steps
# get list of org keys from spreadsheet
# for each key:
# get the description
# check if custom fields are empty
# for each field, it empty, get value from description and update