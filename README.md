# Karbon API Tools
python scripts for downloading bulk data from Karbon via API

## Setup
1. **clone the repository**
```
git clone https://github.com/yourusername/karbon-data-tools.git
cd karbon-data-tools
```
2. (Optional) Create and Activate a virtual environment
```
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```
3. Install dependencies
``` 
pip install -r requirements.txt
```
4. Create an .env file in the project directory
```
bearer_token=your_karbon_bearer_token
access_key=your_karbon_access_key
```

## get_all_invoices.py

### Features
- Export invoices from Karbon into a csv file
- optionally:
    - fetch line items
    - fetch payments
    - fetch only overdue invoices
    - count unique clients served in a particular month

### Usage
run the script
```
python get_all_invoices.py
```
You will be prompted to choose actions like:

1: Generate new base invoice list
2: Get line items (slow)
3: Create CSV with overdue invoices
4: Get payments for invoices
5: Count clients served in a month

### Output files
*these will appear in the same directory when the script is completed*
- invoices.csv — All invoice data
- YYYY-MM-DD invoices_line_items.csv — Line item breakdown
- YYYY-MM-DD invoices_payments.csv — Payment history
- YYYY-MM-DD overdue_invoices.csv — Overdue invoice report