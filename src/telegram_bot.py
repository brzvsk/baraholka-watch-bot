import asyncio
import logging
from typing import Optional
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.constants import ParseMode
import time
from src.scraper import Product

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = Bot(token=bot_token)
        self.last_message_time = 0
        self.min_interval = 1  # Minimum 1 second between messages to avoid rate limiting
    
    def format_message(self, product: Product) -> str:
        """Format product information into a Telegram message."""
        message = f"🛋️ <b>{product.title}</b>\n\n"
        message += f"💰 Цена: <code>{product.price}</code>\n"
        message += f"🔗 <a href='{product.link}'>Посмотреть объявление</a>\n\n"
        message += f"🆔 ID: {product.product_id}"
        
        return message
    
    def create_inline_keyboard(self, product: Product) -> Optional[InlineKeyboardMarkup]:
        """Create inline keyboard with Telegram link button."""
        if not product.telegram_link:
            return None
            
        keyboard = [[
            InlineKeyboardButton(
                text="💬 Посмотреть в Telegram",
                url=product.telegram_link
            )
        ]]
        
        return InlineKeyboardMarkup(keyboard)
    
    async def send_notification(self, product: Product, dry_run: bool = False) -> bool:
        """Send notification about new product."""
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_message_time < self.min_interval:
                await asyncio.sleep(self.min_interval - (current_time - self.last_message_time))
            
            message = self.format_message(product)
            keyboard = self.create_inline_keyboard(product)
            
            if dry_run:
                keyboard_info = f" with button: {product.telegram_link}" if keyboard else ""
                logger.info(f"DRY RUN - Would send message{keyboard_info}:\n{message}")
                return True
            
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
                plain_message = f"🛋️ {product.title}\n\n"
                plain_message += f"💰 Цена: {product.price}\n"
                plain_message += f"🔗 Ссылка: {product.link}\n\n"
                plain_message += f"🆔 ID: {product.product_id}"
                
                if not dry_run:
                    await self.bot.send_message(
                        chat_id=self.chat_id,
                        text=plain_message,
                        reply_markup=keyboard,
                        disable_web_page_preview=False
                    )
                
                logger.info(f"Sent plain text notification for product: {product.title}")
                return True
                
            except TelegramError as e2:
                logger.error(f"Failed to send even plain text notification: {e2}")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error sending notification: {e}")
            return False
    
    async def send_batch_notifications(self, products: list[Product], dry_run: bool = False) -> int:
        """Send notifications for multiple products."""
        success_count = 0
        
        for product in products:
            success = await self.send_notification(product, dry_run=dry_run)
            if success:
                success_count += 1
            
            # Small delay between messages
            await asyncio.sleep(1)
        
        logger.info(f"Sent {success_count}/{len(products)} notifications successfully")
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