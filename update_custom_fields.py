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


def get_description(org_key):
    conn.request("GET", f"/v3/Organizations/{org_key}", payload, headers)
    res = conn.getresponse()
    data = res.read()
    resp_json = json.loads(data.decode("utf-8"))
    description = resp_json.get("EntityDescription", {}).get("Text", "")
    return description

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
        


df = pd.read_csv("organizations.csv", encoding="utf-8-sig")
    
update_qb_admin_password("7cQ25cf3hJl")  

# print(list_custom_fields())

## Steps
# get list of org keys from spreadsheet
# for each key:
# get the description
# check if custom fields are empty
# for each field, it empty, get value from description and update