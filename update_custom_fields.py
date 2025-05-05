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
    "accounting_software": re.compile(r"^Accounting Software\s*:\s*([^\r\n]+)", re.I | re.M),
    "admin_password":      re.compile(r"^Admin Password\s*:\s*([^\r\n]+)",   re.I | re.M),
    "ras_id":              re.compile(r"^RAS ID\s*:\s*([^\r\n]+)",           re.I | re.M),
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

def extract_cf_from_description(description):
    out = {}
    for key, pattern in _PATTERNS.items():
        m = pattern.search(description)
        out[key] = m.group(1).strip() if m else None
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
    
    if qb_admin_password == "":
        description = get_description(org_key)
        cf_values = extract_cf_from_description(description)
        qb_admin_password = cf_values.get("QB Admin Password")
        if qb_admin_password:
            print(qb_admin_password)


df = pd.read_csv("organizations.csv", encoding="utf-8-sig")
    
update_qb_admin_password("2VM8k9XRBkJw")  



## Steps
# get list of org keys from spreadsheet
# for each key:
# get the description
# check if custom fields are empty
# for each field, it empty, get value from description and update