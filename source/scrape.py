# scrape.py
import os
import sys
from datetime import datetime
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import asyncio
from typing import Tuple, List

# Constants
BATCH_SIZE = 200
DELAY = 2  # seconds between batches

def log_error(error: Exception, module: str = 'scrape') -> None:
    """Log errors to scrape_errors.txt"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(f"{module}_errors.txt", "a") as f:
        f.write(f"[{timestamp}] {str(error)}\n")

async def get_credentials() -> Tuple[int, str]:
    """Get API credentials from user"""
    print("\nGet your API credentials from https://my.telegram.org/apps")
    api_id = input("Enter API ID: ")
    api_hash = input("Enter API Hash: ")
    return int(api_id), api_hash

async def get_group_link() -> str:
    """Get group/channel link from user"""
    return input("\nEnter group/channel link or ID: ")

async def save_users(users: List[str], group_name: str) -> str:
    """Save usernames to file"""
    filename = f"users_{group_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for user in users:
            if user:  # Only save non-empty usernames
                f.write(f"{user}\n")
    return filename

async def scrape_users(client: TelegramClient, group: str) -> None:
    """Main scraping function"""
    try:
        # Connect to group/channel
        entity = await client.get_entity(group)
        group_name = entity.username or str(entity.id)
        
        users = set()
        offset = 0
        total_attempts = 0
        failed_attempts = 0

        print("\nScraping users...")
        print("Progress: ", end="", flush=True)

        while True:
            try:
                # Get participants
                participants = await client(GetParticipantsRequest(
                    channel=entity,
                    filter=ChannelParticipantsSearch(''),
                    offset=offset,
                    limit=BATCH_SIZE,
                    hash=0
                ))

                # Break if no more participants
                if not participants.users:
                    break

                # Extract usernames
                for user in participants.users:
                    if user.username:
                        users.add(user.username)

                # Update progress
                print(".", end="", flush=True)
                offset += len(participants.users)
                total_attempts += 1

                # Delay to respect rate limits
                await asyncio.sleep(DELAY)

            except errors.FloodWaitError as e:
                failed_attempts += 1
                print(f"\nRate limit hit. Waiting {e.seconds} seconds...")
                await asyncio.sleep(e.seconds)

            except Exception as e:
                failed_attempts += 1
                log_error(e)
                print(f"\nError: {str(e)}")
                await asyncio.sleep(DELAY)

        # Save results
        filename = await save_users(list(users), group_name)
        
        # Print stats
        print(f"\n\nScraping completed!")
        print(f"Total users found: {len(users)}")
        print(f"Success rate: {((total_attempts - failed_attempts) / total_attempts) * 100:.2f}%")
        print(f"Results saved to: {filename}")

    except Exception as e:
        log_error(e)
        print(f"\nError: {str(e)}")

async def main_scrape() -> None:
    """Main scraping coordinator"""
    try:
        api_id, api_hash = await get_credentials()
        group = await get_group_link()

        # Initialize client
        client = TelegramClient('scraper_session', api_id, api_hash)
        await client.start()

        # Run scraper
        await scrape_users(client, group)
        
        # Cleanup
        await client.disconnect()

    except Exception as e:
        log_error(e)
        print(f"\nError: {str(e)}")

    input("\nPress Enter to return to main menu...")

def start_scrape() -> None:
    """Entry point for scraping"""
    asyncio.run(main_scrape())

if __name__ == "__main__":
    start_scrape()