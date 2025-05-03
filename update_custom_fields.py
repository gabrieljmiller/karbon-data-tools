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

print(get_description("3R9lghymWNgZ"))