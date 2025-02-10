import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict
import os
import signal
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, ChatAdminRequiredError
from telethon.tl.types import InputPeerChannel
from config import API_ID, API_HASH
from login import check_session, print_header, clear_screen

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)
logger = logging.getLogger(__name__)

class PostBot:
    def __init__(self):
        self.stored_message = None
        self.target_groups: Dict[int, str] = {}
        self.is_posting: bool = False
        self.client: Optional[TelegramClient] = None
        self.stop_event = None

    def log_error(self, error: Exception) -> None:
        """Log errors to file with fancy formatting"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("errors.txt", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] ❌ {str(error)}\n")
        logger.error(f"Error occurred: {str(error)}")

    async def initialize_client(self) -> bool:
        """Initialize Telethon client"""
        try:
            self.client = TelegramClient('telety_session', API_ID, API_HASH)
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                print("\n❌ No active session! Please login first.")
                return False
                
            print("\n✅ Client initialized successfully!")
            return True
            
        except Exception as e:
            self.log_error(e)
            print(f"\n❌ Failed to initialize client: {str(e)}")
            return False

    async def send_message_to_group(self, group, message):
        """Send a message to a specific group with error handling"""
        try:
            if hasattr(message, 'media'):
                await self.client.send_file(
                    group,
                    file=message.media,
                    caption=message.text if hasattr(message, 'text') else None
                )
            else:
                await self.client.send_message(group, message.text)
            return True
        except FloodWaitError as e:
            logger.warning(f"Rate limit hit, waiting {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            return False
        except ChatAdminRequiredError:
            logger.error(f"Bot needs admin rights in the group")
            return False
        except Exception as e:
            self.log_error(e)
            return False

    def setup_handlers(self):
        """Set up all message handlers"""
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            await event.reply(
                "🌟 <b>Welcome to TELETY!</b> 🌟\n\n"
                "💡 <b>Available Commands:</b>\n"
                "/start - Show this message\n"
                "/help - Show help information\n"
                "/post - Start posting process\n"
                "/cancel - Cancel current operation\n\n"
                "📝 Send me any message to store it for posting!",
                parse_mode='html'
            )

        @self.client.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            await event.reply(
                "📚 <b>TELETY Help Guide</b>\n\n"
                "1️⃣ Send me the message you want to post\n"
                "2️⃣ Use /post to send it to all groups\n"
                "3️⃣ Use /cancel to clear stored message\n\n"
                "⚠️ Make sure to add me as admin in groups!",
                parse_mode='html'
            )

        @self.client.on(events.NewMessage(pattern='/post'))
        async def post_handler(event):
            if self.is_posting:
                await event.reply("⚠️ Already posting! Please wait...")
                return

            if not self.stored_message:
                await event.reply("❌ No message stored!\nSend me a message first.")
                return

            try:
                self.is_posting = True
                await event.reply("🔍 Getting group list...")
                
                # Get all dialogs
                async for dialog in self.client.iter_dialogs():
                    if dialog.is_group or dialog.is_channel:
                        self.target_groups[dialog.id] = dialog.title

                if not self.target_groups:
                    await event.reply("❌ Not added to any groups!")
                    return

                await event.reply(f"🚀 Starting to post to {len(self.target_groups)} groups...")
                
                success = 0
                failed = 0

                for group_id, group_name in self.target_groups.items():
                    try:
                        if await self.send_message_to_group(group_id, self.stored_message):
                            success += 1
                        else:
                            failed += 1
                        await asyncio.sleep(2)  # Rate limiting
                    except Exception as e:
                        self.log_error(e)
                        failed += 1
                        continue

                # Send report
                total = len(self.target_groups)
                success_rate = (success / total) * 100 if total > 0 else 0
                
                report = (
                    "📊 <b>Posting Complete!</b>\n\n"
                    f"✅ Success: {success} groups\n"
                    f"❌ Failed: {failed} groups\n"
                    f"📈 Success Rate: {success_rate:.1f}%"
                )
                await event.reply(report, parse_mode='html')

            except Exception as e:
                self.log_error(e)
                await event.reply(f"❌ Error during posting: {str(e)}")
            finally:
                self.is_posting = False
                self.stored_message = None
                self.target_groups.clear()

        @self.client.on(events.NewMessage(pattern='/cancel'))
        async def cancel_handler(event):
            self.stored_message = None
            self.is_posting = False
            self.target_groups.clear()
            await event.reply("🚫 Operation cancelled. Message cleared.")

        @self.client.on(events.NewMessage)
        async def message_handler(event):
            if event.message.text and event.message.text.startswith('/'):
                return  # Skip commands
                
            self.stored_message = event.message
            await event.reply(
                "✅ Message stored!\n"
                "Use /post when you're ready to send it."
            )

def start_post():
    """Main entry point for the bot"""
    if not check_session():
        print("\n❌ Error: Please login first!")
        input("\n🔄 Press Enter to return to main menu...")
        return

    clear_screen()
    print_header()
    
    # Create and get event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    post_bot = PostBot()
    
    async def start_bot():
        try:
            if not await post_bot.initialize_client():
                return
                
            print("\033[35m" + "=" * 50 + "\033[0m")
            print("\n🚀 Bot is running!")
            print("💡 Press Ctrl+C to stop")
            
            post_bot.setup_handlers()
            await post_bot.client.run_until_disconnected()
                
        except KeyboardInterrupt:
            print("\n\n👋 Received shutdown signal...")
        except Exception as e:
            post_bot.log_error(e)
            print(f"\n❌ Error: {str(e)}")
        finally:
            if post_bot.client:
                await post_bot.client.disconnect()

    try:
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        pass
    finally:
        try:
            # Cancel all running tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
                
            # Run loop until tasks are cancelled
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
            # Close the loop
            loop.close()
        except Exception as e:
            print(f"\n❌ Error during cleanup: {str(e)}")
        
        print("\n✨ Bot stopped. Press Enter to return to main menu...")
        input()

if __name__ == "__main__":
    start_post()