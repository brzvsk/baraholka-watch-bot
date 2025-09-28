import requests
from bs4 import BeautifulSoup
import logging
import re
import os
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Product:
    title: str
    price: str
    link: str
    product_id: str
    date_posted: Optional[str] = None
    telegram_link: Optional[str] = None

class YarmarkaGeScraper:
    def __init__(self, base_url: str = "https://yarmarka.ge"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Load cookies from environment
        cookie_string = os.getenv('COOKIE_STRING')
        if cookie_string:
            # Parse cookie string into individual cookies
            cookies = {}
            for cookie in cookie_string.split('; '):
                if '=' in cookie:
                    key, value = cookie.split('=', 1)
                    cookies[key] = value
            self.session.cookies.update(cookies)
            logger.info(f"Loaded {len(cookies)} cookies including geo=tbilisi")
        
        # Load keywords from environment variable
        keywords_str = os.getenv('SEARCH_KEYWORDS', 'стеллаж,стелаж,журнальный,столик,зеркало')
        self.keywords = [keyword.strip() for keyword in keywords_str.split(',') if keyword.strip()]
        logger.info(f"Loaded search keywords: {self.keywords}")
    
    def fetch_listings(self, url: str) -> List[Product]:
        """Fetch and parse product listings from the main page."""
        try:
            logger.info(f"Fetching listings from: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Find all product containers with name links
            name_links = soup.find_all('div', class_='product-list__name')
            
            for name_div in name_links:
                try:
                    # Get the link from the name div
                    link_tag = name_div.find('a')
                    if not link_tag:
                        continue
                    
                    # Extract product link and ID
                    product_path = link_tag.get('href')
                    if not product_path:
                        continue
                        
                    # Extract product ID from path like /g_zhurnalnystol_445772
                    match = re.search(r'/g_(.+)_(\d+)$', product_path)
                    if not match:
                        continue
                    
                    product_name, product_id = match.groups()
                    
                    # Get the product title
                    title = link_tag.get_text(strip=True)
                    if not title:
                        continue
                    
                    # Check if title contains any of our keywords
                    title_lower = title.lower()
                    if not any(keyword.lower() in title_lower for keyword in self.keywords):
                        continue
                    
                    # Find price and date - look in the parent container
                    price = "N/A"
                    date_posted = None
                    container = name_div.find_parent()
                    while container and price == "N/A":
                        price_elem = container.find('div', class_='product-list__price')
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            # Extract price from text like "Цена: 40 GEL"
                            price_match = re.search(r'(\d+(?:\.\d+)?)\s*GEL', price_text)
                            if price_match:
                                price = f"{price_match.group(1)} GEL"
                            break
                        container = container.find_parent()
                        if not container or container.name == 'body':
                            break
                    
                    # Find date - look in the productitem__footer
                    container = name_div.find_parent()
                    while container and not date_posted:
                        # Look for productitem__footer that contains the date
                        footer_elem = container.find('div', class_='productitem__footer')
                        if footer_elem:
                            # Find the text-right div that contains the date
                            date_elem = footer_elem.find('div', class_='text-right')
                            if date_elem:
                                date_text = date_elem.get_text(strip=True)
                                # Check if it looks like a date (contains common date patterns)
                                if re.search(r'(назад|вчера|сегодня|\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2} [а-я]+ \d{4})', date_text):
                                    date_posted = date_text
                            break
                        container = container.find_parent()
                        if not container or container.name == 'body':
                            break
                    
                    product = Product(
                        title=title,
                        price=price,
                        link=f"{self.base_url}{product_path}",
                        product_id=product_id,
                        date_posted=date_posted
                    )
                    products.append(product)
                    logger.info(f"Found matching product: {title} - {price}")
                    
                except Exception as e:
                    logger.error(f"Error processing product: {e}")
                    continue
            
            logger.info(f"Found {len(products)} matching products")
            return products
            
        except requests.RequestException as e:
            logger.error(f"Error fetching listings: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing listings: {e}")
            return []
    
    def get_telegram_link(self, product: Product) -> Optional[str]:
        """Extract Telegram chat link from product page."""
        try:
            logger.info(f"Fetching Telegram link for: {product.link}")
            response = self.session.get(product.link, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for "Посмотреть в чате" button with Telegram link
            chat_link = soup.find('a', text=re.compile(r'Посмотреть в чате'))
            if chat_link and chat_link.get('href'):
                telegram_url = chat_link.get('href')
                if telegram_url.startswith('https://t.me/'):
                    logger.info(f"Found Telegram link: {telegram_url}")
                    return telegram_url
            
            # Alternative: look for any t.me link in the page
            all_links = soup.find_all('a', href=re.compile(r'https://t\.me/'))
            for link in all_links:
                href = link.get('href')
                if '/baraholka_' in href and href != 'https://t.me/baraholka_ge':
                    logger.info(f"Found Telegram link (alternative method): {href}")
                    return href
            
            logger.warning(f"No Telegram link found for product: {product.title}")
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error fetching product page {product.link}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error extracting Telegram link: {e}")
            return None
    
    def scrape_new_products(self, listings_url: str) -> List[Product]:
        """Main method to scrape and return new products with Telegram links."""
        products = self.fetch_listings(listings_url)
        
        # Get Telegram links for all products
        for product in products:
            product.telegram_link = self.get_telegram_link(product)
        
        # Filter out products without Telegram links
        products_with_links = [p for p in products if p.telegram_link]
        logger.info(f"Found {len(products_with_links)} products with Telegram links")
        
        return products_with_links