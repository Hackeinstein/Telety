import asyncio
import logging
from datetime import datetime
from typing import Optional, Set
import os
from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram.error import TelegramError
from telegram.constants import ParseMode
from session_manager import check_session
# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Display fancy ASCII header"""
    header = """
\033[36m████████╗███████╗██╗     ███████╗████████╗██╗   ██╗
╚══██╔══╝██╔════╝██║     ██╔════╝╚══██╔══╝╚██╗ ██╔╝
   ██║   █████╗  ██║     █████╗     ██║    ╚████╔╝ 
   ██║   ██╔══╝  ██║     ██╔══╝     ██║     ╚██╔╝  
   ██║   ███████╗███████╗███████╗   ██║      ██║   
   ╚═╝   ╚══════╝╚══════╝╚══════╝   ╚═╝      ╚═╝   \033[0m
    """
    print(header)
    print("\033[35m" + "=" * 50 + "\033[0m")

class PostBot:
    def __init__(self):
        self.token: Optional[str] = None
        self.stored_message: Optional[Update] = None
        self.target_groups: Set[int] = set()
        self.is_posting: bool = False
        self.application: Optional[Application] = None

    def log_error(self, error: Exception) -> None:
        """Log errors to file with fancy formatting"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("errors.txt", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] ❌ {str(error)}\n")

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        welcome_message = (
            "🌟 <b>Welcome to TELETY!</b> 🌟\n\n"
            "💡 <b>Available Commands:</b>\n"
            "/start - Show this message\n"
            "/help - Show help information\n"
            "/post - Start posting process\n"
            "/cancel - Cancel current operation\n\n"
            "📝 Send me any message to store it for posting!"
        )
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.HTML)

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        help_text = (
            "📚 <b>TELETY Help Guide</b>\n\n"
            "1️⃣ Send me the message you want to post\n"
            "2️⃣ Use /post to send it to all groups\n"
            "3️⃣ Use /cancel to clear stored message\n\n"
            "⚠️ Make sure to add me as admin in groups!"
        )
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Store message for posting"""
        self.stored_message = update.message
        await update.message.reply_text(
            "✅ Message stored!\n"
            "Use /post when you're ready to send it."
        )

    async def handle_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /post command"""
        if self.is_posting:
            await update.message.reply_text("⚠️ Already posting! Please wait...")
            return

        if not self.stored_message:
            await update.message.reply_text(
                "❌ No message stored!\n"
                "Send me a message first."
            )
            return

        self.is_posting = True
        try:
            # Get groups list
            bot_updates = await context.bot.get_updates()
            self.target_groups.clear()
            for upd in bot_updates:
                if upd.my_chat_member and upd.my_chat_member.chat.type in ['group', 'supergroup']:
                    self.target_groups.add(upd.my_chat_member.chat.id)

            if not self.target_groups:
                await update.message.reply_text(
                    "❌ Not added to any groups!\n"
                    "Add me to groups first."
                )
                return

            await update.message.reply_text("🚀 Starting to post...")
            
            success = 0
            failed = 0
            msg = self.stored_message

            for group_id in self.target_groups:
                try:
                    if msg.text and not msg.caption:
                        await context.bot.send_message(
                            chat_id=group_id,
                            text=msg.text,
                            parse_mode=ParseMode.HTML
                        )
                    elif msg.photo:
                        await context.bot.send_photo(
                            chat_id=group_id,
                            photo=msg.photo[-1].file_id,
                            caption=msg.caption,
                            parse_mode=ParseMode.HTML
                        )
                    elif msg.video:
                        await context.bot.send_video(
                            chat_id=group_id,
                            video=msg.video.file_id,
                            caption=msg.caption,
                            parse_mode=ParseMode.HTML
                        )
                    elif msg.document:
                        await context.bot.send_document(
                            chat_id=group_id,
                            document=msg.document.file_id,
                            caption=msg.caption,
                            parse_mode=ParseMode.HTML
                        )
                    success += 1
                    await asyncio.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    failed += 1
                    self.log_error(e)

            # Send report
            total = len(self.target_groups)
            success_rate = (success / total) * 100 if total > 0 else 0
            
            report = (
                "📊 <b>Posting Complete!</b>\n\n"
                f"✅ Success: {success} groups\n"
                f"❌ Failed: {failed} groups\n"
                f"📈 Success Rate: {success_rate:.1f}%"
            )
            await update.message.reply_text(report, parse_mode=ParseMode.HTML)

        except Exception as e:
            self.log_error(e)
            await update.message.reply_text(f"❌ Error: {str(e)}")
        finally:
            self.is_posting = False
            self.stored_message = None

    async def handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /cancel command"""
        self.stored_message = None
        self.is_posting = False
        await update.message.reply_text("🚫 Operation cancelled. Message cleared.")

    async def initialize_bot(self, token: str) -> bool:
        """Initialize bot with handlers"""
        try:
            print("\n🔄 Initializing bot...")
            
            # Build application
            self.application = Application.builder().token(token).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.handle_start))
            self.application.add_handler(CommandHandler("help", self.handle_help))
            self.application.add_handler(CommandHandler("post", self.handle_post))
            self.application.add_handler(CommandHandler("cancel", self.handle_cancel))
            self.application.add_handler(MessageHandler(
                filters.ALL & ~filters.COMMAND,
                self.handle_message
            ))
            
            # Initialize and start
            await self.application.initialize()
            await self.application.start()
            
            print("✅ Bot initialized successfully!")
            return True
            
        except Exception as e:
            self.log_error(e)
            print(f"\n❌ Failed to initialize bot: {str(e)}")
            return False

    async def shutdown(self):
        """Cleanup bot resources"""
        try:
            if self.application:
                print("\n🔄 Shutting down bot...")
                await self.application.stop()
                await self.application.shutdown()
                print("✅ Bot shutdown complete")
        except Exception as e:
            self.log_error(e)
            print("❌ Error during shutdown")

def start_post():
    if not check_session():
        print("\n❌ Error: Please login first!")
        input("\n🔄 Press Enter to return to main menu...")
        return
    """Enhanced main entry point"""
    post_bot = PostBot()
    
    async def async_main():
        try:
            clear_screen()
            print_header()
            
            # Get bot token
            print("\n🔑 Get your bot token from @BotFather on Telegram")
            token = input("🤖 Enter your bot token: ").strip()
            
            # Initialize bot
            if not await post_bot.initialize_bot(token):
                return
            
            print("\n🚀 Bot is running!")
            print("💡 Press Ctrl+C to stop")
            print("\033[35m" + "=" * 50 + "\033[0m")
            
            # Start polling
            await post_bot.application.run_polling(drop_pending_updates=True)
                
        except KeyboardInterrupt:
            print("\n\n👋 Received shutdown signal...")
        except Exception as e:
            post_bot.log_error(e)
            print(f"\n❌ Error: {str(e)}")
        finally:
            await post_bot.shutdown()
    
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")
    finally:
        print("\n✨ Bot stopped. Press Enter to return to main menu...")
        input()

if __name__ == "__main__":
    start_post()