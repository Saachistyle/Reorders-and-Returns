File Preparation:
    This script fetches order data from Shopify and processes both reorders and returns. No pre-downloaded files are needed, as the script retrieves data via the Shopify API.

How to Run:
    To execute the script, use the following command in your terminal or command prompt:
        - Mac/Linux: python3 returns_and_reorders.py
        - Windows: python returns_and_reorders.py

    You will be prompted to enter a start date and end date for the orders you want to process. If no end date is entered, the script defaults to the current date.

Output Files:
    1. returns.csv - Contains a list of customers who have returned items, with details like original purchase amount, return amount, and final revenue.
    2. reorders.csv - Identifies repeat customers and logs their sequential purchases, including order dates, amounts, and items bought.

Sample Data:
    1. returns.csv: 2024 - current day (1/31/25)
    2. reorders.csv: 2024 - current day (1/31/25)

Processing Summary:
    1. Fetches all orders from Shopify within the specified date range.
    2. Filters and processes:
        - Returns: Identifies refunded orders, calculates refund amounts, and adjusts final revenue.
        - Reorders: Tracks multiple purchases by the same customer and organizes them in sequential order.
    3. Saves results into well-structured CSV files for further analysis.
    4. Ensure your Shopify API credentials are correctly set in the script before execution. If you encounter errors, verify your date inputs and API access permissions.