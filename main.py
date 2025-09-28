#!/usr/bin/env python3
import os
import sys
import logging
import argparse
import schedule
import time
import signal
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.scraper import YarmarkaGeScraper
from src.telegram_bot import TelegramNotifierSync
from src.state_manager import StateManager

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class BaraholkaWatchBot:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.running = True
        
        # Load configuration
        self.bot_token = os.getenv('BOT_TOKEN')
        self.chat_id = os.getenv('CHAT_ID')
        
        # Support multiple URLs
        urls_str = os.getenv('YARMARKA_URLS', 'https://yarmarka.ge/goods/c_2438/0/0?sort=new')
        self.yarmarka_urls = [url.strip() for url in urls_str.split(',') if url.strip()]
        
        self.check_interval = int(os.getenv('CHECK_INTERVAL_MINUTES', 30))
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("BOT_TOKEN and CHAT_ID must be set in environment variables")
        
        # Initialize components
        self.scraper = YarmarkaGeScraper()
        self.telegram = TelegramNotifierSync(self.bot_token, self.chat_id)
        self.state = StateManager(os.getenv("STATE_FILE", "sent_ads.json"))
        
        logger.info(f"Bot initialized - Dry run: {self.dry_run}")
        logger.info(f"Check interval: {self.check_interval} minutes")
        logger.info(f"Target URLs: {', '.join(self.yarmarka_urls)}")
        
    def test_connection(self) -> bool:
        """Test Telegram bot connection."""
        logger.info("Testing Telegram bot connection...")
        return self.telegram.test_connection()
    
    def check_for_new_products(self) -> None:
        """Main function to check for new products and send notifications."""
        try:
            logger.info(f"Starting product check at {datetime.now()}")
            
            # Scrape products from all URLs
            logger.info(f"Scraping products from {len(self.yarmarka_urls)} categories...")
            all_products = []
            for url in self.yarmarka_urls:
                logger.info(f"Scraping: {url}")
                products = self.scraper.scrape_new_products(url)
                all_products.extend(products)
            
            products = all_products
            
            if not products:
                logger.info("No matching products found")
                return
            
            logger.info(f"Found {len(products)} matching products")
            
            # Filter out already sent products
            new_products = self.state.filter_new_products(products)
            
            if not new_products:
                logger.info("No new products to send")
                return
            
            logger.info(f"Sending notifications for {len(new_products)} new products")
            
            # Send notifications
            success_count = self.telegram.send_batch_notifications(new_products, dry_run=self.dry_run)
            
            if success_count > 0:
                # Mark successfully sent products
                if not self.dry_run:
                    self.state.mark_products_sent(new_products[:success_count])
                logger.info(f"Successfully processed {success_count} notifications")
            else:
                logger.warning("No notifications were sent successfully")
            
            # Cleanup old entries periodically
            self.state.cleanup_old_entries()
            
            # Log statistics
            stats = self.state.get_stats()
            logger.info(f"Bot statistics: {stats}")
            
        except Exception as e:
            logger.error(f"Error during product check: {e}", exc_info=True)
    
    def run_once(self) -> None:
        """Run the bot once (for testing)."""
        logger.info("Running bot once...")
        self.check_for_new_products()
    
    def run_scheduled(self) -> None:
        """Run the bot on schedule."""
        logger.info(f"Starting scheduled bot with {self.check_interval}-minute intervals")
        
        # Schedule the job
        schedule.every(self.check_interval).minutes.do(self.check_for_new_products)
        
        # Run immediately on start
        self.check_for_new_products()
        
        # Main loop
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(60)  # Wait a minute before retrying
        
        logger.info("Bot stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

def main():
    parser = argparse.ArgumentParser(description='Baraholka Watch Bot')
    parser.add_argument('--dry-run', action='store_true', 
                      help='Run in dry mode without sending actual Telegram messages')
    parser.add_argument('--once', action='store_true', 
                      help='Run once and exit (for testing)')
    parser.add_argument('--test-connection', action='store_true', 
                      help='Test Telegram bot connection and exit')
    parser.add_argument('--reset-state', action='store_true', 
                      help='Reset bot state (clear all sent ads tracking)')
    parser.add_argument('--stats', action='store_true', 
                      help='Show bot statistics and exit')
    
    args = parser.parse_args()
    
    try:
        bot = BaraholkaWatchBot(dry_run=args.dry_run)
        
        if args.test_connection:
            success = bot.test_connection()
            sys.exit(0 if success else 1)
        
        if args.reset_state:
            bot.state.reset_state()
            logger.info("State reset completed")
            sys.exit(0)
        
        if args.stats:
            stats = bot.state.get_stats()
            print(f"Bot Statistics:")
            print(f"  Total ads sent: {stats['total_sent']}")
            print(f"  Sent in last 24h: {stats['sent_last_24h']}")
            print(f"  State file: {stats['state_file']}")
            print(f"  State file exists: {stats['file_exists']}")
            sys.exit(0)
        
        # Test connection before starting
        if not bot.test_connection():
            logger.error("Telegram connection test failed")
            sys.exit(1)
        
        if args.once:
            bot.run_once()
        else:
            bot.setup_signal_handlers()
            bot.run_scheduled()
    
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()