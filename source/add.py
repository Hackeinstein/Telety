# add.py
import os
import asyncio
from datetime import datetime
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputPeerUser
from typing import List, Tuple

# Constants
DELAY = 60  # seconds between adds
DAILY_LIMIT = 50  # Telegram's approximate daily limit
ADD_BATCH = 10  # Users to add before showing progress

def log_error(error: Exception, module: str = 'add') -> None:
    """Log errors to add_errors.txt"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(f"{module}_errors.txt", "a") as f:
        f.write(f"[{timestamp}] {str(error)}\n")

async def get_credentials() -> Tuple[int, str]:
    """Get API credentials from user"""
    print("\nEnter your Telegram API credentials:")
    api_id = input("API ID: ")
    api_hash = input("API Hash: ")
    return int(api_id), api_hash

async def get_user_file() -> str:
    """Get path to file containing usernames"""
    while True:
        filepath = input("\nEnter path to username file: ")
        if os.path.exists(filepath):
            return filepath
        print("File not found. Please try again.")

async def get_target_group() -> str:
    """Get target group link/ID"""
    return input("\nEnter target group link or ID: ")

async def load_users(filepath: str) -> List[str]:
    """Load usernames from file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

async def add_members(client: TelegramClient, group: str, users: List[str]) -> None:
    """Main adding function"""
    try:
        # Get target group entity
        target_group = await client.get_entity(group)
        
        total_users = len(users)
        successful_adds = 0
        failed_adds = 0
        
        print(f"\nStarting to add {total_users} users...")
        print("This process will take time due to Telegram's rate limits.")
        print(f"Maximum daily limit: {DAILY_LIMIT} users\n")

        for i, username in enumerate(users, 1):
            try:
                # Get user entity
                user = await client.get_entity(username)
                
                # Add user to group
                await client(InviteToChannelRequest(
                    channel=target_group,
                    users=[user]
                ))
                
                successful_adds += 1
                
                # Show progress after each batch
                if i % ADD_BATCH == 0:
                    print(f"Progress: {i}/{total_users} processed")
                    print(f"Success: {successful_adds}, Failed: {failed_adds}")
                
                # Check daily limit
                if successful_adds >= DAILY_LIMIT:
                    print("\nDaily limit reached. Please try again tomorrow.")
                    break
                
                # Delay between adds
                await asyncio.sleep(DELAY)

            except errors.FloodWaitError as e:
                failed_adds += 1
                wait_time = e.seconds
                print(f"\nRate limit hit. Waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)

            except Exception as e:
                failed_adds += 1
                log_error(e)
                print(f"Error adding {username}: {str(e)}")
                await asyncio.sleep(DELAY)

        # Final stats
        print("\nOperation completed!")
        print(f"Total processed: {successful_adds + failed_adds}")
        print(f"Successfully added: {successful_adds}")
        print(f"Failed: {failed_adds}")
        print(f"Success rate: {(successful_adds / (successful_adds + failed_adds)) * 100:.2f}%")

    except Exception as e:
        log_error(e)
        print(f"\nError: {str(e)}")

async def main_add() -> None:
    """Main adding coordinator"""
    try:
        # Get necessary information
        api_id, api_hash = await get_credentials()
        user_file = await get_user_file()
        target_group = await get_target_group()

        # Load users
        users = await load_users(user_file)
        if not users:
            print("\nNo users found in file.")
            return

        # Initialize client
        client = TelegramClient('adder_session', api_id, api_hash)
        await client.start()

        # Run adder
        await add_members(client, target_group, users)
        
        # Cleanup
        await client.disconnect()

    except Exception as e:
        log_error(e)
        print(f"\nError: {str(e)}")

    input("\nPress Enter to return to main menu...")

def start_add() -> None:
    """Entry point for adding members"""
    asyncio.run(main_add())

if __name__ == "__main__":
    start_add()