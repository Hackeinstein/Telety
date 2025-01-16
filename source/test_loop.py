import asyncio
import sys
import tracemalloc
from telegram import Bot
from telegram.error import InvalidToken, NetworkError
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Enable tracemalloc
tracemalloc.start()

async def test_bot_token(token: str) -> None:
    """Test basic bot functionality and print diagnostic information"""
    try:
        print("\n=== Testing Bot Configuration ===")
        
        # Initialize bot
        print("Initializing bot...")
        bot = Bot(token)
        
        # Test getMe
        print("\nTesting bot.getMe()...")
        me = await bot.get_me()
        print(f"Bot Info:\n"
              f"- ID: {me.id}\n"
              f"- Name: {me.first_name}\n"
              f"- Username: {me.username}\n"
              f"- Can join groups: {me.can_join_groups}\n"
              f"- Can read group messages: {me.can_read_all_group_messages}\n")
        
        # Get bot permissions
        print("\nGetting bot updates to check permissions...")
        updates = await bot.get_updates()
        print(f"Number of available updates: {len(updates)}")
        
        if updates:
            print("\nLast few updates:")
            for update in updates[-3:]:  # Show last 3 updates
                print(f"- Update ID: {update.update_id}")
                if update.message:
                    print(f"  Message: {update.message.text[:50]}...")
                if update.my_chat_member:
                    print(f"  Chat Type: {update.my_chat_member.chat.type}")
                    print(f"  Chat ID: {update.my_chat_member.chat.id}")
        
        # Test event loop
        print("\nChecking event loop status...")
        loop = asyncio.get_running_loop()
        print(f"Event loop running: {loop.is_running()}")
        print(f"Event loop closed: {loop.is_closed()}")
        
        # Memory snapshots
        print("\nMemory usage snapshot:")
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        print("Top 3 memory allocations:")
        for stat in top_stats[:3]:
            print(f"{stat.count} memory blocks: {stat.size/1024:.1f} KiB")
            print(f"Largest allocation: {stat.size/1024:.1f} KiB")
            print(f"At {stat.traceback[0]}")

    except InvalidToken:
        print("Error: Invalid bot token")
        logger.error("Invalid token provided", exc_info=True)
    except NetworkError:
        print("Error: Network connection issue")
        logger.error("Network error occurred", exc_info=True)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        logger.error("Unexpected error occurred", exc_info=True)

async def main():
    """Main entry point for testing"""
    print("=== Telegram Bot Diagnostic Tool ===")
    token = input("\nEnter your bot token: ").strip()
    
    try:
        await test_bot_token(token)
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        logger.error("Test failed", exc_info=True)
    finally:
        # Proper cleanup
        pending = asyncio.all_tasks()
        for task in pending:
            if task is not asyncio.current_task():
                task.cancel()
        
        print("\nTest complete. Check the logs for detailed information.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        logger.error("Fatal error occurred", exc_info=True)