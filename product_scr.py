""" 
This script scrapes product details from Sephora's website using the URLs collected by `sephora_scr.py`.

The script reads URLs from `data/product_urls.csv`. Using Selenium it navigates
to each product page, and extracts the product name, brand, and ingredients.

The results are saved in `data/product_data.csv`, and any skipped URLs (e.g., products that are not available) are saved in `data/product_skipped.csv`.

!!! IMPORTANT !!!
The sephora_scr.py saves data into `data/product_urls_full.csv`, however this script uses `data/product_urls.csv` to read the URLs.
For easier use, take one category from `data/product_urls_full.csv` and copy into `data/product_urls.csv` before running this script.
After running the script and saving* data, change the category in `data/product_urls.csv` to the next one you want to scrape.

* The script will overwrite the `data/product_data.csv` and `data/product_skipped.csv` files, each time it runs.
To save data, after you finish collecting, change the names of both csv files, substituting 'product' into the category name. See README.md for example
"""

import random
from tqdm import tqdm

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# List of user agents to randomize browser requests and avoid detection.
user_agents = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.96 Safari/537.36",
]

# Function to initialize the Selenium WebDriver with specific options.
def init_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--headless=new")
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    return webdriver.Chrome(options=options)

# Read the product URLs from the CSV file.
data = pd.read_csv('data/product_urls.csv')
data = data.dropna(subset=["URL"])
urls = data["URL"].tolist()
categories = data["category"].tolist()



def main():
    """
    Main function to scrape product details from Sephora's website. It initializes the Selenium WebDriver, iterates through the product URLs,
    and extracts product details such as name, brand, and ingredients. The results are saved to CSV files.
    The function handles exceptions and skips URLs for products that are not available. 
    """
    driver = init_driver()
    products = [] # List to store product details.
    skipped_urls = [] # List to store skipped products.

    try:
        #Iterate though each product URL, and give progress bar in terminal.
        for url, category in tqdm(zip(urls, categories), total=len(urls), desc="Scraping products"):
            try:
                print(f"Scraping {url}")
                driver.get(url)
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # Scroll to the ingredients section so it loads properly.
                try:
                    section = driver.find_element(By.ID, "ingredients")
                    driver.execute_script("arguments[0].scrollIntoView();", section)
                except Exception:
                    pass

                soup = BeautifulSoup(driver.page_source, "html.parser")

                #Skips products that are not available.
                if soup.find(
                    string=lambda text: text and "Sorry, this product is not available" in text
                ):
                    print(f"Skipping unavailable product at {url}")
                    skipped_urls.append({"Category": category, "URL": url})
                    continue
                
                # Extract product details, using beautiful soup.
                name_tag = soup.find("span", {"data-at": "product_name"})
                name = name_tag.text.strip() if name_tag else None

                brand_tag = soup.find("a", {"data-at": "brand_name"})
                brand = brand_tag.text.strip() if brand_tag else None

                ingredients = None
                ingredient_div = soup.find("div", {"id": "ingredients"})
                if ingredient_div:
                    # Collect ingredients from nested divs.
                    divs = ingredient_div.find_all("div")
                    texts = [
                        div.get_text(strip=True) for div in divs if div.get_text(strip=True)
                    ]
                    if texts:
                        ingredients = " ".join(texts)

                # Append the product details to the list.
                products.append(
                    {
                        "Category": category,
                        "URL": url,
                        "Brand": brand,
                        "Product Name": name,
                        "Ingredients": ingredients,
                    }
                )
            # Handle exceptions for individual product pages.
            except Exception:
                import traceback
                print(f"Error scraping {url}")
                traceback.print_exc()
    finally:
        driver.quit()

    # Save the collected product data and skipped URLs to CSV files.
    data_products = pd.DataFrame(products)
    data_products.to_csv("data/product_data.csv", index=False)
    pd.DataFrame(skipped_urls).to_csv("data/product_skipped.csv", index=False)
    print("Scraping complete.")

# Run the main function when the script is executed.
if __name__ == "__main__":
    main()