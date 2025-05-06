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
    # check if field is empty
    custom_fields_mp = get_custom_fields(org_key)
    qb_admin_password = get_cf_value(custom_fields_mp, "QB Admin Password")
    
    if qb_admin_password == []:
        description = get_description(org_key)
        cf_values = extract_cf_from_description(description)
        qb_admin_password = cf_values.get("admin_password")
        if qb_admin_password:
            print(qb_admin_password)
        else:
            print("No QB Admin Password found in description")
            return
        payload = {
            "EntityKey": org_key,
            "CustomFieldValues": [
                {
                    "Key":   "bT3FHvnxFCg",               # e.g. "ZGNGtYyLm4z"
                    "Name":  "QB Admin Password",
                    "Type":  "Text",               # field type in Karbon
                    "Value": qb_admin_password             # Text fields expect a plain string
                }
            ]
        }
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        
        conn.request("PUT", f"/v3/CustomFieldValues/{org_key}", body, headers)
        res = conn.getresponse()
        print(f"Update status: {res.status} {res.reason}")
        return
        


df = pd.read_csv("organizations.csv", encoding="utf-8-sig")
    
update_qb_admin_password("7yXq7DfPPrm")  

# print(list_custom_fields())

## Steps
# get list of org keys from spreadsheet
# for each key:
# get the description
# check if custom fields are empty
# for each field, it empty, get value from description and update