
from session_manager import SessionManager
import os
import sys
from datetime import datetime
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, Channel, Chat
from telethon.tl.functions.messages import GetFullChatRequest
import asyncio
from typing import Tuple, List
from login import check_session, print_header, clear_screen

# Constants
BATCH_SIZE = 200
DELAY = 2  # seconds between batches

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
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

def log_error(error: Exception, module: str = 'scrape') -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("errors.txt", "a") as f:
        f.write(f"[{timestamp}] {str(error)}\n")

async def scrape_users(client: TelegramClient, group: str) -> None:
    try:
        # Get entity with better error handling
        try:
            if group.isdigit() or (group.startswith('-') and group[1:].isdigit()):
                entity = await client.get_entity(int(group))
            else:
                entity = await client.get_entity(group)

            # Safer group name extraction
            if hasattr(entity, 'username') and entity.username:
                group_name = entity.username
            else:
                group_name = str(entity.id)

        except ValueError:
            print("\n❌ Error: Group not found. Make sure the link/ID is correct.")
            return
        except errors.FloodWaitError as e:
            print(f"\n⚠️ Rate limit hit. Please wait {e.seconds} seconds")
            log_error(e)
            return

        users = set()
        offset = 0
        total_attempts = 0
        failed_attempts = 0
        last_batch_size = BATCH_SIZE

        print("\n🔍 Scraping users...")
        print("📊 Progress: ", end="", flush=True)

        while last_batch_size == BATCH_SIZE:
            try:
                # Get participants
                result = await client(GetParticipantsRequest(
                    channel=entity,
                    filter=ChannelParticipantsSearch(''),
                    offset=offset,
                    limit=BATCH_SIZE,
                    hash=0
                ))

                # Process users from this batch
                for user in result.users:
                    if user.username:  # Only store users with usernames
                        users.add(user.username)

                # Update progress
                last_batch_size = len(result.users)
                offset += last_batch_size
                total_attempts += 1
                print(".", end="", flush=True)

                # Show periodic stats
                if total_attempts % 5 == 0:
                    print(f"\n📊 Found {len(users)} unique users so far...")

                # Break if no more users
                if last_batch_size < BATCH_SIZE:
                    break

                # Delay to respect rate limits
                await asyncio.sleep(DELAY)

            except errors.FloodWaitError as e:
                failed_attempts += 1
                wait_time = e.seconds
                print(f"\n⚠️ Rate limit hit. Waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                continue

            except errors.ChatAdminRequiredError:
                print("\n❌ Error: Admin privileges required to scrape this group")
                log_error("Admin privileges required")
                break

            except errors.ChannelPrivateError:
                print("\n❌ Error: This is a private channel/group")
                log_error("Private channel/group")
                break

            except Exception as e:
                failed_attempts += 1
                print(f"\n❌ Error during scraping: {str(e)}")
                log_error(e)
                await asyncio.sleep(DELAY)
                continue

        # Save results if we found any users
        if users:
            try:
                # Generate filename with group name and timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"users_{group_name}_{timestamp}.txt"

                # Save users to file
                with open(filename, "w", encoding="utf-8") as f:
                    for user in sorted(users):  # Sort for readability
                        f.write(f"{user}\n")

                # Print final stats
                print("\n\n✅ Scraping completed!")
                print(f"👥 Total unique users found: {len(users)}")
                print(f"🔄 Total batches attempted: {total_attempts}")
                print(f"❌ Failed attempts: {failed_attempts}")
                if total_attempts > 0:
                    success_rate = ((total_attempts - failed_attempts) / total_attempts) * 100
                    print(f"📊 Success rate: {success_rate:.2f}%")
                print(f"💾 Results saved to: {filename}")

            except Exception as e:
                print("\n❌ Error saving results to file")
                log_error(e)
                # If file save fails, print users to console as fallback
                print("\n👥 Users found:")
                for user in sorted(users):
                    print(user)
        else:
            print("\n❌ No users found or unable to scrape users from this group")

    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        log_error(e)

async def get_credentials() -> Tuple[int, str]:
    session_mgr = SessionManager()
    saved_creds = session_mgr.load_credentials()

    if saved_creds and all(saved_creds):
        print("\n🔄 Using saved credentials...")
        return saved_creds

    while True:
        try:
            print("\n🔑 Enter your Telegram API credentials:")
            api_id = input("📱 API ID: ").strip()
            if not api_id.isdigit():
                print("❌ API ID must be a number")
                continue
            api_hash = input("🔒 API Hash: ").strip()

            credentials = (int(api_id), api_hash)
            session_mgr.save_credentials(*credentials)
            return credentials

        except ValueError:
            print("❌ Invalid input. Please try again.")

async def get_group_link() -> str:
    return input("\n🔗 Enter group/channel link or ID: ")

async def main_scrape() -> None:
    try:
        clear_screen()
        print_header()
        
        print("\n🔄 Starting Telegram session...")
        session_mgr = SessionManager()
        client = await session_mgr.get_client('scraper_session')

        if not client:
            print("\n❌ Failed to initialize session. Please try again.")
            return
            
        print("✅ Successfully connected to Telegram!")
        group = await get_group_link()
        await scrape_users(client, group)

        await client.disconnect()

    except Exception as e:
        log_error(e)
        print(f"\n❌ Error: {str(e)}")

    input("\n🔄 Press Enter to return to main menu...")

def start_scrape() -> None:
    if not check_session():
        print("\n❌ Error: Please login first!")
        input("\n🔄 Press Enter to return to main menu...")
        return
    try:
        clear_screen()
        print_header()
        asyncio.run(main_scrape())
    except KeyboardInterrupt:
        print("\n\n👋 Scraping cancelled by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")

if __name__ == "__main__":
    start_scrape()