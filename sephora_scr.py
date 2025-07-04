"""
This script scrapes product URLs from Sephora's website for specified categories.

It scrolls through several categories on sephora.com using Selenium and collects the links to each product.
The resulting list of URLs is saved to ``data/product_urls.csv``. The CSV contains two columns:
``category`` and ``URL``. 

!!! IMPORTANT !!!
To run this scraper you must have Chrome and the matching ChromeDriver
installed. Provide the path to `chromedriver` through editing the `chrome_path`
variable below. The generated URL list can then be processed by the
`product_scr.py` scraper to gather detailed product information.

While running the script, keep the Chrome browser open, and always visible. If you leave it, the script won't collect properly.
"""

import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def scrape_all_paginated_products(driver, base_url, category, final_df, max_pages=50):
    """Scrolls through all pages of a given category on Sephora's website and collects product URLs.

    Paratemeters:
    driver: selenium.webdriver
        The Selenium WebDriver instance used to control the browser.
    base_url: str
        The base URL of the Sephora website.
    category: str
        Category to append to the base URL.
    final_df: pandas.DataFrame
        DataFrame to store the collected product URLs.
    max_pages: int, optional
        Maximum number of pages to scrape. Default is 50.

    Returns:
    final_df: pandas.DataFrame
        DataFrame containing the unique collected product URLs found in given categories.
    """

    all_hrefs = set()
    for page in range(1, max_pages + 1):
        url = f"{base_url}/{category}?currentPage={page}"
        print(f"Loading page {page}: {url}")
        driver.get(url)
        time.sleep(4)
        driver.execute_script("window.scrollBy(0, 1);")
        time.sleep(0.5)

        previous_count = -1
        scroll_attempts = 0
        while scroll_attempts < 7:
            product_blocks = driver.find_elements(By.CSS_SELECTOR, "div.css-11ifn8v.e15t7owz0")
            current_count = len(product_blocks)

            if current_count == previous_count:
                scroll_attempts += 1
            else:
                scroll_attempts = 0 

            previous_count = current_count

            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(1.5)

        print(f"Collected {current_count} products on page {page}")
        if current_count == 0:
            print("No products found, stopping pagination.")
            break

        for block in product_blocks:
            anchors = block.find_elements(By.XPATH, ".//a[contains(@href, '/product/')]")
            for anchor in anchors:
                href = anchor.get_attribute("href")
                if href and href not in all_hrefs:
                    all_hrefs.add(href)
                    final_df.loc[len(final_df)] = {"category": category, "URL": href}
    return final_df

# Set the path to your ChromeDriver executable
# Make sure to download the correct version for your Chrome browser
# and adjust the path accordingly.
chrome_path = "/Users/jadziazaczek/chromedriver-mac-arm64/chromedriver"
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36")
service = Service(executable_path=chrome_path)
driver = webdriver.Chrome(service=service, options=options)

#Sephora categories to scrape, used to construct URLs
categories = ['cleanser', 
              'facial-treatments', 
              'moisturizing-cream-oils-mists', 
              'lip-balm-lip-care', 
              'face-mask', 
              'sunscreen-sun-protection', 
              'eye-treatment-dark-circle-treatment']
final_df = pd.DataFrame(columns = ['category', 'URL']) #DataFrame that will hold the collected links

# Loop through each category and scrape all paginated products
for category in categories:
    final_df = scrape_all_paginated_products(driver, "https://www.sephora.com/shop", category, final_df)
    
driver.quit()

# Save the collected URLs to a CSV file
final_df.to_csv('./data/product_urls_full.csv', index = False)