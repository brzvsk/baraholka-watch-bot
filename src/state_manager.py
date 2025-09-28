import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Set
import os

logger = logging.getLogger(__name__)

class StateManager:
    def __init__(self, state_file: str = "sent_ads.json"):
        self.state_file = state_file
        self.sent_ads = {}  # Dict[product_id, timestamp]
        self.load_state()
    
    def load_state(self) -> None:
        """Load previously sent ads from file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sent_ads = data.get('sent_ads', {})
                logger.info(f"Loaded {len(self.sent_ads)} previously sent ads")
            else:
                logger.info("No previous state file found, starting fresh")
                self.sent_ads = {}
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            self.sent_ads = {}
    
    def save_state(self) -> None:
        """Save current state to file."""
        try:
            data = {
                'sent_ads': self.sent_ads,
                'last_updated': datetime.now().isoformat()
            }
            
            # Write to temporary file first, then rename for atomic operation
            temp_file = f"{self.state_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            os.rename(temp_file, self.state_file)
            logger.debug(f"State saved with {len(self.sent_ads)} entries")
            
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def is_product_sent(self, product_id: str) -> bool:
        """Check if a product has already been sent."""
        return product_id in self.sent_ads
    
    def mark_product_sent(self, product_id: str) -> None:
        """Mark a product as sent."""
        self.sent_ads[product_id] = datetime.now().isoformat()
        logger.debug(f"Marked product {product_id} as sent")
    
    def filter_new_products(self, products: list) -> list:
        """Filter out products that have already been sent."""
        new_products = []
        for product in products:
            if not self.is_product_sent(product.product_id):
                new_products.append(product)
            else:
                logger.debug(f"Skipping already sent product: {product.title} (ID: {product.product_id})")
        
        logger.info(f"Found {len(new_products)} new products out of {len(products)} total")
        return new_products
    
    def mark_products_sent(self, products: list) -> None:
        """Mark multiple products as sent."""
        for product in products:
            self.mark_product_sent(product.product_id)
        self.save_state()
    
    def cleanup_old_entries(self, days: int = 7) -> None:
        """Remove entries older than specified days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            initial_count = len(self.sent_ads)
            
            # Create new dict with only recent entries
            new_sent_ads = {}
            for product_id, timestamp_str in self.sent_ads.items():
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if timestamp > cutoff_date:
                        new_sent_ads[product_id] = timestamp_str
                except ValueError:
                    # Keep entries with invalid timestamps (backward compatibility)
                    new_sent_ads[product_id] = timestamp_str
            
            self.sent_ads = new_sent_ads
            removed_count = initial_count - len(self.sent_ads)
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old entries")
                self.save_state()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_stats(self) -> Dict[str, any]:
        """Get statistics about tracked products."""
        total_sent = len(self.sent_ads)
        
        # Count entries from last 24 hours
        yesterday = datetime.now() - timedelta(days=1)
        recent_count = 0
        
        for timestamp_str in self.sent_ads.values():
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                if timestamp > yesterday:
                    recent_count += 1
            except ValueError:
                pass
        
        return {
            'total_sent': total_sent,
            'sent_last_24h': recent_count,
            'state_file': self.state_file,
            'file_exists': os.path.exists(self.state_file)
        }
    
    def reset_state(self) -> None:
        """Reset all state (for testing purposes)."""
        self.sent_ads = {}
        try:
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
            logger.info("State reset successfully")
        except Exception as e:
            logger.error(f"Error resetting state: {e}")