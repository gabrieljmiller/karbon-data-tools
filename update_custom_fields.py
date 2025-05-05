import http.client
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

conn = http.client.HTTPSConnection("api.karbonhq.com")
payload = ''
headers = {
    'Accept': 'application/json',
    'Authorization': os.getenv("bearer_token"),
    'AccessKey': os.getenv("access_key")
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

print(list_custom_fields())


## Steps
# get list of keys from spreadsheet
# for each key:
# get the description
# check if custom fields are empty
# for each field, it empty, get value from description and update