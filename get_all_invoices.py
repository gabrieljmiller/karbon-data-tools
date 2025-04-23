import http.client
import json
import csv
import urllib
import os
import sys
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from datetime import date

# get base path depending on whether script is run from source or executable
try:
    base_path = os.path.dirname(sys.executable)
except Exception:
    base_path = os.path.dirname(os.path.abspath(__file__))

# Path to the .env file in the same directory as the executable/script
env_path = os.path.join(base_path, '.env')
print(f'env path: {env_path}')

# Load environment variables from the .env file
load_dotenv(dotenv_path=env_path)

conn = http.client.HTTPSConnection("api.karbonhq.com")
payload = ''
headers = {
    'Accept': 'application/json',
    'Authorization': os.getenv("bearer_token"),
    'AccessKey': os.getenv("access_key")
}

# Get current date
current_date = datetime.now().date()

def list_all_inv():
    print("Retrieving invoice list...")

    all_rows = []
    skip_value = 0
    seen_invoice_keys = set()

    while True:
        conn.request("GET", f"/v3/Invoices?$orderby=InvoiceDate&$top=100&$skip={skip_value}", payload, headers)
        res = conn.getresponse()
        data = res.read()
        inv_list_json_data = json.loads(data)
        invoices = inv_list_json_data.get("value", [])

        if not invoices:
            break

        for invoice in invoices:
            invoice_key = invoice.get("InvoiceKey", "")
            if invoice_key in seen_invoice_keys:
                continue
            seen_invoice_keys.add(invoice_key)

            client = invoice.get("Client", {})
            client_key = client.get("ClientKey", "")

            # Fetch client info
            conn.request("GET", f"/v3/Organizations/{client_key}?$expand=BusinessCards", payload, headers)
            res2 = conn.getresponse()
            data2 = res2.read()
            inv_detail_json_data = json.loads(data2)

            business_cards = inv_detail_json_data.get("BusinessCards", [])
            if business_cards and business_cards[0].get("Addresses"):
                address = business_cards[0]["Addresses"][0]
                address_lines = address.get("AddressLines", "")
                city = address.get("City", "")
                state = address.get("StateProvinceCounty", "")
                zipcode = address.get("ZipCode", "")
            else:
                address_lines = city = state = zipcode = ""

            row = {
                "Client": client.get("Name", ""),
                "Invoice Number": invoice.get("InvoiceNumber", ""),
                "Invoice Total": invoice.get("InvoiceTotal", ""),
                "Street": address_lines,
                "City": city,
                "State": state,
                "Zip": zipcode,
                "Status": invoice.get("InvoiceStatus", ""),
                "Due Date": invoice.get("PaymentDueDate", "").split("T")[0],
                "Invoice Date": invoice.get("InvoiceDate", "").split("T")[0],
                "Invoice Key": invoice_key,
                "Email Address": client.get("EmailAddress", "")
            }

            all_rows.append(row)
            print(f"{row['Invoice Number']}, {row['Client']}")

        skip_value += 100

    # Write to CSV using pandas
    df = pd.DataFrame(all_rows)
    df.to_csv("invoices.csv", index=False, encoding="utf-8")
    print("CSV file 'invoices.csv' has been created.")
    
def get_inv_line_items():
    print("Retrieving line items...")

    # Load invoice list with pandas
    df = pd.read_csv("invoices.csv", encoding="utf-8-sig")

    # Prepare list to collect all line items
    line_item_rows = []

    for _, row in df.iterrows():
        inv_key = str(row["Invoice Key"]).strip()
        inv_key_encoded = urllib.parse.quote(inv_key)
        conn.request("GET", f"/v3/Invoices/{inv_key_encoded}?$expand=LineItems", payload, headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))

        line_items = json_data.get("LineItems", [])
        for item in line_items:
            billable_item_type = item.get("BillableItemType", "")
            description = item.get("Description", "")
            line_item_total = item.get("Amount", 0)

            if billable_item_type in ("Entity", "TimeEntry"):
                work_key = item.get("BillableItemEntityKey", "")
                work_url = f"https://app2.karbonhq.com/YtfB1S5FYHG#/work/{work_key}/tasks"

                conn.request("GET", f"/v3/WorkItems/{work_key}", payload, headers)
                res = conn.getresponse()
                data = res.read()
                work_json = json.loads(data.decode("utf-8"))
                work_title = work_json.get("Title", "")
                work_type = work_json.get("WorkType", "")
            else:
                work_key = ""
                work_url = ""
                work_title = ""
                work_type = ""

            line_item_rows.append({
                "Invoice Number": row["Invoice Number"],
                "Client": row["Client"],
                "Street": row["Street"],
                "City": row["City"],
                "State": row["State"],
                "Zipcode": row["Zip"],
                "Email": row["Email Address"],
                "Invoice Total": row["Invoice Total"],
                "Status": row["Status"],
                "Due Date": row["Due Date"],
                "Invoice Date": row["Invoice Date"],
                "Line Item Description": description,
                "Line Item Total": line_item_total,
                "Work Title": work_title,
                "Work Type": work_type,
                "Work URL": work_url
            })

        print(f"Processed invoice {row['Invoice Number']} with {len(line_items)} line items.")

    # Write all line items to CSV using pandas
    output_filename = f"{datetime.today()} invoices_line_items.csv"
    pd.DataFrame(line_item_rows).to_csv(output_filename, index=False, quoting=1, encoding="utf-8")
    print(f"Spreadsheet '{output_filename}' with line items created.")

def get_additional_payment_info(payment_key):
    conn.request('GET', f'/v3/Payments/{payment_key}', payload, headers)
    res = conn.getresponse()
    data = res.read()
    payment_json = json.loads(data.decode("utf-8"))
    payment_method = payment_json.get('PaymentMethod', '')
    return payment_method

def get_inv_payments():
    print("Retrieving payments...")

    # Load invoice data
    df = pd.read_csv("invoices.csv", encoding="utf-8-sig")

    payment_rows = []

    for _, row in df.iterrows():
        inv_key = str(row["Invoice Key"]).strip()
        inv_key_encoded = urllib.parse.quote(inv_key)
        conn.request("GET", f"/v3/Invoices/{inv_key_encoded}?$expand=Payments", payload, headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))

        payments = json_data.get("Payments", [])

        for payment in payments:
            payment_date = payment.get("PaymentDate", "")
            payment_amount = payment.get("Amount", "")
            payment_type = payment.get("PaymentType", "")
            payment_key = payment.get("PaymentKey", "")
            payment_method = get_additional_payment_info(payment_key)

            payment_rows.append({
                "Invoice Number": row["Invoice Number"],
                "Client": row["Client"],
                "Street": row["Street"],
                "City": row["City"],
                "State": row["State"],
                "Zipcode": row["Zip"],
                "Email": row["Email Address"],
                "Invoice Total": row["Invoice Total"],
                "Status": row["Status"],
                "Due Date": row["Due Date"],
                "Invoice Date": row["Invoice Date"],
                "Payment Date": payment_date,
                "Payment Amount": payment_amount,
                "Payment Type": payment_type,
                "Payment Key": payment_key,
                "Payment Method": payment_method
            })

        print(f"Processed invoice {row['Invoice Number']} with {len(payments)} payments.")

    output_filename = f"{datetime.today()} invoices_payments.csv"
    pd.DataFrame(payment_rows).to_csv(output_filename, index=False, quoting=1, encoding="utf-8")
    print(f"Spreadsheet '{output_filename}' with payments created.")

def filter_overdue():
    # Load invoice data
    df = pd.read_csv("invoices.csv", encoding="utf-8")

    # Filter: status is AwaitingPayment and due date is before today
    df["Due Date"] = pd.to_datetime(df["Due Date"], errors="coerce")
    overdue_df = df[
        (df["Status"] == "AwaitingPayment") &
        (df["Due Date"].dt.date < date.today())
    ]

    # Drop unneeded columns
    overdue_df = overdue_df.drop(columns=["Invoice Key", "Status"])

    # Save result
    output_filename = f"{date.today()} overdue_invoices.csv"
    overdue_df.to_csv(output_filename, index=False)
    print(f"Overdue invoices filtered and saved to '{output_filename}'.")

def count_clients(year, month):
    # count number of individual clients served by month
    df = pd.read_csv('invoices.csv')

    # convert 'Invoice Date' to datetime
    df['Invoice Date'] = pd.to_datetime(df['Invoice Date'])

    # extract month and year from 'Invoice Date'
    filtered = df[(df['Invoice Date'].dt.year == year) & (df['Invoice Date'].dt.month == month)]

    # get unique clients
    unique_clients = filtered['Client'].nunique()

    print(f"Number of unique clients served in {month}/{year}: {unique_clients}")
    return unique_clients


# run functions 
get_inv_input = input("Generate new base invoice list? (y/n):")
get_line_items_input = input("Get line items? It will take much longer. (y/n):")
filter_overdue_input = input("Create a csv with only overdue invoices? (y/n):")
get_payments_input = input("Get payments for invoices? (y/n):")
count_clients_input = input("Count number of clients served in a month? (y/n):")

if get_inv_input == "y":
    list_all_inv()
if get_line_items_input == "y":
    get_inv_line_items()

if filter_overdue_input == "y":
    filter_overdue()
if get_payments_input == "y":
    get_inv_payments()
if count_clients_input == "y":
    year = int(input("Enter year (YYYY): "))
    month = int(input("Enter month (1-12): "))
    count_clients(year, month)