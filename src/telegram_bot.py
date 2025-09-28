import asyncio
import logging
from typing import Optional
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError, RetryAfter, TimedOut
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest
import time
from src.scraper import Product
import httpx

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        
        # Configure HTTP client with larger connection pool
        self.http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=20,  # Increase connection pool size
                max_keepalive_connections=10,
                keepalive_expiry=30
            ),
            timeout=httpx.Timeout(30.0)  # 30 second timeout
        )
        
        # Create bot with custom request handler
        self.request = HTTPXRequest(
            connection_pool_size=20,
            connect_timeout=10,
            pool_timeout=10,
            read_timeout=30
        )
        self.bot = Bot(token=bot_token, request=self.request)
        
        self.last_message_time = 0
        self.min_interval = 1.5  # Minimum 1.5 seconds between messages to avoid rate limiting
    
    def format_message(self, product: Product) -> str:
        """Format product information into a Telegram message."""
        message = f"🛋️ <b>{product.title}</b>\n\n"
        message += f"💰 Цена: <code>{product.price}</code>\n"
        
        # Add date if available
        if product.date_posted:
            message += f"📅 Опубликовано: {product.date_posted}\n"
        
        return message.rstrip()
    
    def create_inline_keyboard(self, product: Product) -> Optional[InlineKeyboardMarkup]:
        """Create inline keyboard with buttons for product page and Telegram."""
        keyboard = []
        
        # Add product page button
        keyboard.append([
            InlineKeyboardButton(
                text="🔗 Посмотреть объявление",
                url=product.link
            )
        ])
        
        # Add Telegram button if available
        if product.telegram_link:
            keyboard.append([
                InlineKeyboardButton(
                    text="💬 Посмотреть в Telegram",
                    url=product.telegram_link
                )
            ])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def send_notification_with_retry(self, product: Product, dry_run: bool = False, max_retries: int = 3) -> bool:
        """Send notification with retry logic and exponential backoff."""
        for attempt in range(max_retries + 1):
            try:
                return await self._send_single_notification(product, dry_run)
            
            except RetryAfter as e:
                if attempt < max_retries:
                    wait_time = e.retry_after + 1  # Add 1 second buffer
                    logger.warning(f"Rate limited, waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Rate limited, max retries exceeded for {product.title}")
                    return False
            
            except (TimedOut, ConnectionError) as e:
                if attempt < max_retries:
                    wait_time = (2 ** attempt) + 1  # Exponential backoff: 2, 5, 9 seconds
                    logger.warning(f"Connection error ({e}), retrying in {wait_time} seconds (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Connection error, max retries exceeded for {product.title}: {e}")
                    return False
            
            except TelegramError as e:
                logger.error(f"Telegram error for {product.title}: {e}")
                return False
            
            except Exception as e:
                logger.error(f"Unexpected error sending notification for {product.title}: {e}")
                return False
        
        return False
    
    async def _send_single_notification(self, product: Product, dry_run: bool = False) -> bool:
        """Send notification about new product."""
        # Rate limiting
        current_time = time.time()
        if current_time - self.last_message_time < self.min_interval:
            sleep_time = self.min_interval - (current_time - self.last_message_time)
            await asyncio.sleep(sleep_time)
        
        message = self.format_message(product)
        keyboard = self.create_inline_keyboard(product)
        
        if dry_run:
            keyboard_info = f" with button: {product.telegram_link}" if keyboard else ""
            logger.info(f"DRY RUN - Would send message{keyboard_info}:\n{message}")
            return True
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=False
            )
            
            self.last_message_time = time.time()
            logger.info(f"Successfully sent notification for product: {product.title}")
            return True
            
        except TelegramError as e:
            logger.error(f"Telegram error sending notification for {product.title}: {e}")
            
            # If HTML parsing fails, try with plain text
            try:
                plain_message = f"🛋️ *{product.title}*\n\n"
                plain_message += f"💰 Цена: {product.price}\n"
                
                # Add date if available
                if product.date_posted:
                    plain_message += f"📅 Опубликовано: {product.date_posted}\n"
                
                plain_message = plain_message.rstrip()
                
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=plain_message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard,
                    disable_web_page_preview=False
                )
                
                self.last_message_time = time.time()
                logger.info(f"Sent plain text notification for product: {product.title}")
                return True
                
            except TelegramError as e2:
                logger.error(f"Failed to send even plain text notification: {e2}")
                raise e2  # Re-raise to trigger retry logic
    
    async def send_notification(self, product: Product, dry_run: bool = False) -> bool:
        """Send notification about new product (public interface)."""
        return await self.send_notification_with_retry(product, dry_run)
    
    async def send_batch_notifications(self, products: list[Product], dry_run: bool = False) -> int:
        """Send notifications for multiple products."""
        success_count = 0
        total_products = len(products)
        
        logger.info(f"Starting batch notification for {total_products} products")
        
        for i, product in enumerate(products, 1):
            logger.debug(f"Processing product {i}/{total_products}: {product.title}")
            
            success = await self.send_notification_with_retry(product, dry_run=dry_run)
            if success:
                success_count += 1
            
            # Progress logging every 5 products or at the end
            if i % 5 == 0 or i == total_products:
                logger.info(f"Progress: {i}/{total_products} processed, {success_count} successful")
            
            # Small delay between messages to avoid overwhelming the API
            if i < total_products:  # Don't sleep after the last message
                await asyncio.sleep(0.5)
        
        logger.info(f"Batch complete: sent {success_count}/{total_products} notifications successfully")
        return success_count
    
    async def test_connection(self) -> bool:
        """Test if the bot can connect to Telegram API."""
        try:
            me = await self.bot.get_me()
            logger.info(f"Bot connection successful. Bot name: {me.first_name} (@{me.username})")
            return True
        except TelegramError as e:
            logger.error(f"Bot connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing bot connection: {e}")
            return False
    
    async def close(self):
        """Close HTTP connections."""
        if hasattr(self, 'http_client'):
            await self.http_client.aclose()
        if hasattr(self, 'request'):
            await self.request.shutdown()

# Synchronous wrapper for easier integration
class TelegramNotifierSync:
    def __init__(self, bot_token: str, chat_id: str):
        self.notifier = TelegramNotifier(bot_token, chat_id)
    
    def send_notification(self, product: Product, dry_run: bool = False) -> bool:
        """Synchronous wrapper for sending single notification."""
        return asyncio.run(self.notifier.send_notification(product, dry_run))
    
    def send_batch_notifications(self, products: list[Product], dry_run: bool = False) -> int:
        """Synchronous wrapper for sending multiple notifications."""
        return asyncio.run(self.notifier.send_batch_notifications(products, dry_run))
    
    def test_connection(self) -> bool:
        """Synchronous wrapper for testing connection."""
        return asyncio.run(self.notifier.test_connection())
    
    def close(self):
        """Close HTTP connections."""
        asyncio.run(self.notifier.close())
