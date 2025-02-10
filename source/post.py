
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict
import os
import json
from telethon import TelegramClient, events
from telethon.errors import (
    FloodWaitError, 
    ChatAdminRequiredError, 
    ChannelPrivateError,
    UserNotParticipantError
)
from telethon.tl.types import InputPeerChannel, ChatAdminRights, Channel, Chat
from telethon.tl.functions.channels import GetParticipantRequest
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
        self.target_groups: Dict[str, str] = {}  # str keys for JSON compatibility
        self.is_posting: bool = False
        self.client: Optional[TelegramClient] = None
        self.bot_token: Optional[str] = None
        self.groups_file = 'bot_groups.json'
        self.load_saved_groups()

    def load_saved_groups(self):
        """Load saved groups from file"""
        try:
            if os.path.exists(self.groups_file):
                with open(self.groups_file, 'r') as f:
                    self.target_groups = json.load(f)
        except Exception as e:
            self.log_error(e)
            self.target_groups = {}

    def save_groups(self):
        """Save groups to file"""
        try:
            with open(self.groups_file, 'w') as f:
                json.dump(self.target_groups, f)
        except Exception as e:
            self.log_error(e)

    def log_error(self, error: Exception) -> None:
        """Log errors to file with fancy formatting"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("errors.txt", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] ❌ {str(error)}\n")
        logger.error(f"Error occurred: {str(error)}")

    async def initialize_client(self, bot_token: str) -> bool:
        """Initialize Telethon client with bot token"""
        try:
            self.bot_token = bot_token
            self.client = TelegramClient('bot_session', API_ID, API_HASH)
            await self.client.start(bot_token=bot_token)
            
            if not await self.client.is_user_authorized():
                print("\n❌ Invalid bot token!")
                return False
                
            # Verify all saved groups
            await self.verify_saved_groups()
            print("\n✅ Bot initialized successfully!")
            return True
            
        except Exception as e:
            self.log_error(e)
            print(f"\n❌ Failed to initialize bot: {str(e)}")
            return False

    async def verify_saved_groups(self):
        """Verify all saved groups are still valid"""
        invalid_groups = []
        for group_id in list(self.target_groups.keys()):
            try:
                if not await self.check_bot_permissions(int(group_id)):
                    invalid_groups.append(group_id)
            except Exception as e:
                invalid_groups.append(group_id)
                self.log_error(e)

        # Remove invalid groups
        for group_id in invalid_groups:
            del self.target_groups[str(group_id)]
        
        self.save_groups()

    async def check_bot_permissions(self, chat_id: int) -> bool:
        """Check if bot has required permissions in the group"""
        try:
            bot = await self.client.get_me()
            participant = await self.client(GetParticipantRequest(
                channel=chat_id,
                participant=bot.id
            ))
            return hasattr(participant.participant, 'admin_rights')
        except Exception as e:
            self.log_error(e)
            return False

    async def verify_group(self, group_id: int, group_title: str = None) -> bool:
        """Verify if a group can be added to the bot's list"""
        try:
            # Get chat info
            chat = await self.client.get_entity(group_id)
            
            # If title wasn't provided, get it from chat
            if not group_title:
                group_title = getattr(chat, 'title', 'Unknown Group')

            # Check bot permissions
            if await self.check_bot_permissions(chat.id):
                self.target_groups[str(chat.id)] = group_title
                self.save_groups()
                return True
            return False
        except UserNotParticipantError:
            logger.error(f"Bot is not a participant in group {group_id}")
            return False
        except Exception as e:
            self.log_error(e)
            return False
    async def send_message_to_group(self, group_id, message):
        """Send a message to a specific group with error handling"""
        try:
            if not await self.check_bot_permissions(int(group_id)):
                return False

            if message.media:  # If message has media
                await self.client.send_file(
                    int(group_id),
                    file=message.media,
                    caption=message.text if hasattr(message, 'text') else None
                )
            elif hasattr(message, 'text') and message.text:  # For text-only messages
                await self.client.send_message(
                    int(group_id),
                    message=message.text  # Changed from message.text to message=message.text
                )
            else:
                logger.error("Message has no content to send")
                return False
                
            return True
                
        except FloodWaitError as e:
            logger.warning(f"Rate limit hit, waiting {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            return False
        except Exception as e:
            self.log_error(e)
            return False

    def setup_handlers(self):
        """Set up all message handlers"""
        @self.client.on(events.NewMessage(pattern='/addgroup'))
        async def add_group_handler(event):
            try:
                # Only work in groups, not private chats
                if not event.is_group and not event.is_channel:
                    await event.reply(
                        "❌ This command only works in groups!\n"
                        "Add me to a group and use /addgroup there."
                    )
                    return

                chat = await event.get_chat()
                if await self.verify_group(chat.id, chat.title):
                    await event.reply(
                        "✅ Successfully added this group!\n"
                        "I'll post messages here when you use /post"
                    )
                else:
                    await event.reply(
                        "❌ Failed to add group.\n"
                        "Make sure I have admin rights!"
                    )

            except Exception as e:
                self.log_error(e)
                await event.reply("❌ Error adding group. Try again later.")

        @self.client.on(events.NewMessage(pattern='/removegroup'))
        async def remove_group_handler(event):
            try:
                if not event.is_group and not event.is_channel:
                    await event.reply("❌ This command only works in groups!")
                    return

                chat_id = str(event.chat_id)
                if chat_id in self.target_groups:
                    del self.target_groups[chat_id]
                    self.save_groups()
                    await event.reply("✅ Removed this group from posting list.")
                else:
                    await event.reply("❌ This group wasn't in my posting list.")

            except Exception as e:
                self.log_error(e)
                await event.reply("❌ Error removing group.")

        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            await event.reply(
                "🌟 <b>Welcome to TELETY!</b> 🌟\n\n"
                "💡 <b>Available Commands:</b>\n"
                "/start - Show this message\n"
                "/help - Show help information\n"
                "/post - Start posting process\n"
                "/groups - List connected groups\n"
                "/addgroup - Add current group (use in group)\n"
                "/removegroup - Remove current group (use in group)\n"
                "/cancel - Cancel current operation\n\n"
                "📝 Send me any message to store it for posting!",
                parse_mode='html'
            )

        @self.client.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            await event.reply(
                "📚 <b>TELETY Help Guide</b>\n\n"
                "1️⃣ Add me to your groups as admin\n"
                "2️⃣ Use /addgroup in each group to activate posting\n"
                "3️⃣ Send me messages to store them\n"
                "4️⃣ Use /post to send to all groups\n"
                "5️⃣ Use /groups to see connected groups\n\n"
                "⚠️ Make sure to make me admin in groups!",
                parse_mode='html'
            )

        @self.client.on(events.NewMessage(pattern='/groups'))
        async def groups_handler(event):
            if not self.target_groups:
                await event.reply(
                    "❌ No groups configured!\n"
                    "Add me to groups and use /addgroup in each group."
                )
                return
                
            groups_list = "\n".join([
                f"📌 {group_name}" 
                for group_name in self.target_groups.values()
            ])
            
            await event.reply(
                f"📋 <b>Connected Groups:</b>\n\n{groups_list}\n\n"
                f"Total: {len(self.target_groups)} groups",
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
                
                if not self.target_groups:
                    await event.reply(
                        "❌ Not added to any groups!\n"
                        "Add me to groups as admin first."
                    )
                    return

                await event.reply(f"🚀 Starting to post to {len(self.target_groups)} groups...")
                
                success = 0
                failed = 0

                for group_id, group_name in self.target_groups.items():
                    try:
                        if await self.send_message_to_group(group_id, self.stored_message):
                            success += 1
                            logger.info(f"Successfully posted to {group_name}")
                        else:
                            failed += 1
                            logger.error(f"Failed to post to {group_name}")
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

        @self.client.on(events.NewMessage(pattern='/cancel'))
        async def cancel_handler(event):
            self.stored_message = None
            self.is_posting = False
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
            print("\n🔑 Get your bot token from @BotFather on Telegram")
            bot_token = input("🤖 Enter your bot token: ").strip()
            
            if not await post_bot.initialize_client(bot_token):
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