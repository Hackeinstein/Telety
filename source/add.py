import os
import asyncio
from datetime import datetime
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputPeerUser
from typing import List, Tuple
from session_manager import SessionManager
from session_manager import check_session

# Constants
DELAY = 60  # seconds between adds
DAILY_LIMIT = 50  # Telegram's approximate daily limit
ADD_BATCH = 10  # Users to add before showing progress

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

def log_error(error: Exception, module: str = 'add') -> None:
    """Log errors to add_errors.txt"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("errors.txt", "a") as f:
        f.write(f"[{timestamp}] {str(error)}\n")

async def get_credentials() -> Tuple[int, str]:
    """Get API credentials with session management"""
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

async def get_user_file() -> str:
    """Get path to file containing usernames"""
    while True:
        filepath = input("\n📁 Enter path to username file: ")
        if os.path.exists(filepath):
            return filepath
        print("❌ File not found. Please try again.")

async def get_target_group() -> str:
    """Get target group link/ID"""
    return input("\n🎯 Enter target group link or ID: ")

async def load_users(filepath: str) -> List[str]:
    """Load usernames from file with validation"""
    users = []
    try:
        print("📖 Loading users from file...")
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                username = line.strip()
                if username and not username.startswith('#'):
                    if username.startswith('@'):
                        username = username[1:]
                    if 5 <= len(username) <= 32 and username.isalnum():
                        users.append(username)
        print(f"✅ Loaded {len(users)} valid usernames")
        return users
    except UnicodeDecodeError:
        print("❌ Error: File must be in UTF-8 encoding")
        return []

async def add_members(client: TelegramClient, group: str, users: List[str]) -> None:
    """Main adding function"""
    try:
        print("🎯 Getting target group information...")
        target_group = await client.get_entity(group)
        
        total_users = len(users)
        successful_adds = 0
        failed_adds = 0
        
        print(f"\n🚀 Starting to add {total_users} users...")
        print("⚠️ This process will take time due to Telegram's rate limits.")
        print(f"📊 Maximum daily limit: {DAILY_LIMIT} users\n")

        for i, username in enumerate(users, 1):
            try:
                print(f"👤 Adding user: {username}")
                user = await client.get_entity(username)
                
                await client(InviteToChannelRequest(
                    channel=target_group,
                    users=[user]
                ))
                
                successful_adds += 1
                print("✅ Success!")
                
                if i % ADD_BATCH == 0:
                    print(f"\n📊 Progress: {i}/{total_users} processed")
                    print(f"✅ Success: {successful_adds}, ❌ Failed: {failed_adds}")
                
                if successful_adds >= DAILY_LIMIT:
                    print("\n⚠️ Daily limit reached. Please try again tomorrow.")
                    break
                
                print(f"⏳ Waiting {DELAY} seconds...\n")
                await asyncio.sleep(DELAY)

            except errors.FloodWaitError as e:
                failed_adds += 1
                wait_time = e.seconds
                print(f"\n⚠️ Rate limit hit. Waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)

            except Exception as e:
                failed_adds += 1
                log_error(e)
                print(f"❌ Error adding {username}: {str(e)}")
                await asyncio.sleep(DELAY)

        total = successful_adds + failed_adds
        success_rate = (successful_adds / total * 100) if total > 0 else 0
        
        print("\n🎉 Operation completed!")
        print(f"📊 Total processed: {total}")
        print(f"✅ Successfully added: {successful_adds}")
        print(f"❌ Failed: {failed_adds}")
        print(f"📈 Success rate: {success_rate:.2f}%")

    except Exception as e:
        log_error(e)
        print(f"\n❌ Error: {str(e)}")

async def main_add() -> None:
    """Main adding coordinator"""
    try:
        clear_screen()
        print_header()
        
        print("\n🔄 Starting Telegram session...")
        session_mgr = SessionManager()
        client = await session_mgr.get_client('adder_session')

        if not client:
            print("\n❌ Failed to initialize session. Please try again.")
            return
            
        print("✅ Successfully connected to Telegram!")

        user_file = await get_user_file()
        target_group = await get_target_group()

        users = await load_users(user_file)
        if not users:
            print("\n❌ No valid users found in file.")
            return

        await add_members(client, target_group, users)
        
        await client.disconnect()

    except Exception as e:
        log_error(e)
        print(f"\n❌ Error: {str(e)}")

    input("\n🔄 Press Enter to return to main menu...")

def start_add() -> None:
    """Entry point for adding members"""
    if not check_session():
        print("\n❌ Error: Please login first!")
        input("\n🔄 Press Enter to return to main menu...")
        return
    try:
        asyncio.run(main_add())
    except KeyboardInterrupt:
        print("\n\n👋 Adding process cancelled by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")

if __name__ == "__main__":
    start_add()