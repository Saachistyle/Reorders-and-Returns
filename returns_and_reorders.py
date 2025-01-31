import requests
import pandas as pd
from collections import defaultdict
import time
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Shopify API credentials
SHOP_NAME = "saachistyle-com"
ACCESS_TOKEN = "e2368ccdc7ee668dfb3992fd7d3bfdba"
API_VERSION = "2025-01"

# Endpoint URL
BASE_URL = f"https://{SHOP_NAME}.myshopify.com/admin/api/{API_VERSION}/orders.json"

# Logging configuration
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Data Storage
customer_orders = defaultdict(list)
unique_order_ids = set()
customer_refunds = []

def fetch_orders(url, params=None):
    retries = 5
    delay = 2  # Initial delay for retries

    while retries > 0:
        response = requests.get(url, headers={"X-Shopify-Access-Token": ACCESS_TOKEN}, params=params)
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", delay))
            time.sleep(retry_after)
            retries -= 1
            continue

        if response.status_code != 200:
            logging.error(f"Error: {response.status_code}, {response.text}")
            return [], None

        orders = response.json().get("orders", [])
        next_link = response.links.get("next", {}).get("url", None)
        time.sleep(0.3)
        return orders, next_link
    
    return [], None

def process_orders(orders):
    for order in orders:
        order_id = order["id"]
        if order_id in unique_order_ids:
            continue
        unique_order_ids.add(order_id)
        
        customer = order.get("customer", {})
        if not customer:
            continue
        
        customer_email = customer.get("email")
        customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
        order_date = order["created_at"]
        total_price = round(float(order["total_price"]), 2)
        items = [item["title"] for item in order["line_items"]]
        
        # Handle Returns
        refunds = order.get("refunds", [])
        return_items = []
        return_amount = 0.0
        
        for refund in refunds:
            for refund_line in refund.get("refund_line_items", []):
                return_items.append(refund_line["line_item"]["title"])
                return_amount += float(refund_line.get("subtotal", 0))
        
        final_amount = round(total_price - return_amount, 2)
        
        if return_items:
            customer_refunds.append({
                "Customer Name": customer_name,
                "Email": customer_email,
                "Order Date": order_date,
                "Original Amount": total_price,
                "Items": ", ".join(items),
                "Returned Items": ", ".join(return_items),
                "Return Amount": round(return_amount, 2),
                "Final Amount": final_amount
            })
        
        # Handle Reorders
        customer_orders[customer_email].append({
            "Name": customer_name,
            "Order Date": order_date,
            "Amount": total_price,
            "Items": ", ".join(items)
        })

def get_all_orders(start_date, end_date=None):
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    params = {
        "status": "any",
        "created_at_min": start_date,
        "created_at_max": end_date,
        "limit": 250,
        "fields": "id,created_at,line_items,total_price,customer,refunds"
    }
    url = BASE_URL
    urls_to_fetch = [url]

    with ThreadPoolExecutor(max_workers=10) as executor:
        while urls_to_fetch:
            futures = {executor.submit(fetch_orders, url, params): url for url in urls_to_fetch}
            urls_to_fetch = []

            for future in as_completed(futures):
                orders, next_link = future.result()
                process_orders(orders)

                if next_link:
                    urls_to_fetch.append(next_link)
                    params = None

def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def save_csvs():
    # Returns CSV
    returns_df = pd.DataFrame(customer_refunds)
    returns_df.to_csv("returns.csv", index=False)
    print("Return data has been saved to CSV.")
    
    # Reorders CSV
    reorders_data = []
    for email, orders in customer_orders.items():
        if len(orders) >= 2:
            orders = sorted(orders, key=lambda x: x['Order Date'])
            total_amount = round(sum(order["Amount"] for order in orders), 2)
            customer_row = {"Name": orders[0]["Name"], "Email": email, "Total Amount": total_amount}
            
            for i, order in enumerate(orders, start=1):
                suffix = ordinal(i)
                customer_row[f"{suffix} Purchase Date"] = order["Order Date"]
                customer_row[f"{suffix} Purchase Amount"] = round(order["Amount"], 2)
                customer_row[f"{suffix} Purchase Items"] = order["Items"]
            
            reorders_data.append(customer_row)
    
    reorders_df = pd.DataFrame(reorders_data)
    reorders_df.to_csv("reorders.csv", index=False)
    print("Reorder data has been saved to CSV.")

def main():
    start_date = input("Enter the start date (YYYY-MM-DD): ")
    end_date = input("Enter the end date (YYYY-MM-DD) or press Enter to use the current date: ")
    print("Processing...please wait.")
    get_all_orders(start_date, end_date)
    save_csvs()
    print("Completed!")

if __name__ == "__main__":
    main()
