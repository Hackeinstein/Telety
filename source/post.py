# post.py
import asyncio
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    ContextTypes,
    MessageHandler,
    filters
)
from typing import List, Dict

# Constants
POST_DELAY = 30  # seconds between posts
SUPPORTED_FILE_TYPES = {
    'document', 'photo', 'video', 'animation', 
    'audio', 'voice', 'video_note'
}

# Store bot token globally
BOT_DATA: Dict = {
    'token': None,
    'message_to_forward': None,
    'groups': set()
}

def log_error(error: Exception, module: str = 'post') -> None:
    """Log errors to post_errors.txt"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(f"{module}_errors.txt", "a") as f:
        f.write(f"[{timestamp}] {str(error)}\n")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    await update.message.reply_text(
        "Welcome to TELETY Post Bot!\n\n"
        "Send me the message you want to post to multiple groups.\n"
        "Once you're ready to post, use /post command."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    await update.message.reply_text(
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/post - Start posting to all groups\n"
        "/cancel - Cancel current operation"
    )

async def save_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save message to be forwarded"""
    BOT_DATA['message_to_forward'] = update.message
    await update.message.reply_text(
        "Message saved! Use /post when you're ready to send it to all groups."
    )

async def post_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /post command"""
    if not BOT_DATA['message_to_forward']:
        await update.message.reply_text(
            "No message to post! Send me a message first."
        )
        return

    msg = BOT_DATA['message_to_forward']
    success_count = 0
    fail_count = 0
    
    await update.message.reply_text("Starting to post messages...")

    # Get list of groups bot is in
    bot = context.bot
    updates = await bot.get_updates()
    for upd in updates:
        if upd.my_chat_member and upd.my_chat_member.chat.type in ['group', 'supergroup', 'channel']:
            BOT_DATA['groups'].add(upd.my_chat_member.chat.id)

    total_groups = len(BOT_DATA['groups'])
    if total_groups == 0:
        await update.message.reply_text(
            "Bot is not added to any groups yet!\n"
            "Please add the bot to groups first."
        )
        return

    # Post to each group
    for i, group_id in enumerate(BOT_DATA['groups'], 1):
        try:
            # Handle different types of messages
            if msg.text and not msg.caption:
                await bot.send_message(
                    chat_id=group_id,
                    text=msg.text,
                    disable_web_page_preview=True
                )
            elif msg.photo:
                await bot.send_photo(
                    chat_id=group_id,
                    photo=msg.photo[-1].file_id,
                    caption=msg.caption
                )
            elif msg.video:
                await bot.send_video(
                    chat_id=group_id,
                    video=msg.video.file_id,
                    caption=msg.caption
                )
            elif msg.document:
                await bot.send_document(
                    chat_id=group_id,
                    document=msg.document.file_id,
                    caption=msg.caption
                )
            # Add more message types as needed

            success_count += 1
            await update.message.reply_text(
                f"Progress: {i}/{total_groups}\n"
                f"Posted to group {i} successfully!"
            )

        except Exception as e:
            fail_count += 1
            log_error(e)
            await update.message.reply_text(
                f"Failed to post to group {i}: {str(e)}"
            )

        # Delay between posts
        if i < total_groups:
            await asyncio.sleep(POST_DELAY)

    # Final stats
    await update.message.reply_text(
        f"\nPosting completed!\n"
        f"Successfully posted to: {success_count} groups\n"
        f"Failed: {fail_count} groups\n"
        f"Success rate: {(success_count/total_groups)*100:.2f}%"
    )

    # Clear saved message
    BOT_DATA['message_to_forward'] = None

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cancel command"""
    BOT_DATA['message_to_forward'] = None
    await update.message.reply_text(
        "Operation cancelled. Saved message cleared."
    )

async def run_bot(token: str) -> None:
    """Run the bot"""
    try:
        application = Application.builder().token(token).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("post", post_message))
        application.add_handler(CommandHandler("cancel", cancel))
        application.add_handler(MessageHandler(
            filters.ALL & ~filters.COMMAND, 
            save_message
        ))

        # Start bot
        await application.run_polling()

    except Exception as e:
        log_error(e)
        print(f"Bot error: {str(e)}")

def start_post() -> None:
    """Entry point for posting"""
    try:
        # Get bot token
        if not BOT_DATA['token']:
            print("\nGet your bot token from @BotFather on Telegram")
            BOT_DATA['token'] = input("Enter bot token: ")

        print("\nStarting bot... Send /start to your bot to begin.")
        print("Press Ctrl+C to return to main menu.")
        
        # Run bot
        asyncio.run(run_bot(BOT_DATA['token']))

    except KeyboardInterrupt:
        print("\nBot stopped.")
    except Exception as e:
        log_error(e)
        print(f"\nError: {str(e)}")
    
    input("\nPress Enter to return to main menu...")

if __name__ == "__main__":
    start_post()