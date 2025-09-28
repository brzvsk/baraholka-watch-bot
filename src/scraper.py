import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Product:
    title: str
    price: str
    link: str
    product_id: str
    telegram_link: Optional[str] = None

class YarmarkaGeScraper:
    def __init__(self, base_url: str = "https://yarmarka.ge"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Keywords to search for (hardcoded as requested)
        self.keywords = ["стеллаж", "стелаж", "журнальный", "столик", "зеркало"]
    
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
                    
                    # Find price - look in the parent container
                    price = "N/A"
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
                    
                    product = Product(
                        title=title,
                        price=price,
                        link=f"{self.base_url}{product_path}",
                        product_id=product_id
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