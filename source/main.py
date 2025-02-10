import sys
import os


# Create logs directory
os.makedirs('logs', exist_ok=True)

# Original content below
import os
import sys
import asyncio
from datetime import datetime
from typing import NoReturn
from login import check_session, start_login



def log_error(error: Exception) -> None:
    """Log errors to errors.txt"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("errors.txt", "a") as f:
        f.write(f"[{timestamp}] {str(error)}\n")

def clear_screen() -> None:
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header() -> None:
    """Display TELETY ASCII header"""
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

def check_dependencies():
    try:
        import telethon
        import telegram
        import qrcode
        return True
    except ImportError:
        print("📦 Required packages not found.")
        print("⚙️ Please run: pip install -r requirements.txt")
        return False

def handle_logout():
    """Handle user logout"""
    try:
        if os.path.exists('telety_session.session'):
            os.remove('telety_session.session')
            print("\n✅ Successfully logged out!")
        else:
            print("\n⚠️ No active session found")
    except Exception as e:
        log_error(e)
        print(f"\n❌ Error during logout: {str(e)}")
    input("\n🔄 Press Enter to continue...")

async def handle_login():
    """Handle login process"""
    try:
        if await start_login():
            input("\n✅ Login successful! Press Enter to continue...")
            return True
        else:
            input("\n❌ Login failed. Press Enter to continue...")
            return False
    except Exception as e:
        log_error(e)
        input(f"\n❌ Login error: {str(e)}\nPress Enter to continue...")
        return False

def print_menu(is_logged_in: bool):
    """Print appropriate menu based on login status"""
    print("\n🎯 Main Menu:")
    
    if is_logged_in:
        print("1. 🔍 Scrape Users      - Extract users from groups")
        print("2. ➕ Add Members       - Add users to your group")
        print("3. 📢 Post Messages     - Send to multiple groups")
        print("4. 🚪 Logout           - Clear active session")
        print("5. 🚫 Exit             - Close application")
    else:
        print("1. 🔑 Login            - Login with Telegram")
        print("2. 🚫 Exit             - Close application")

def main_menu():
    """Display and handle main menu"""
    if not check_dependencies():
        sys.exit(1)
        
    while True:
        try:
            clear_screen()
            print_header()
            
            # Check session status
            is_logged_in = check_session()
            print_menu(is_logged_in)
            
            if is_logged_in:
                choice = input("\n⌨️  Enter your choice (1-5): ").strip()
                
                if choice == "1":
                    from scrape import start_scrape
                    start_scrape()
                elif choice == "2":
                    from add import start_add
                    start_add()
                elif choice == "3":
                    from post import start_post
                    start_post()
                elif choice == "4":
                    handle_logout()
                elif choice == "5":
                    print("\n✨ Thanks for using TELETY!")
                    print("👋 Goodbye!")
                    sys.exit(0)
                else:
                    input("\n❌ Invalid choice. Press Enter to continue...")
            else:
                choice = input("\n⌨️  Enter your choice (1-2): ").strip()
                
                if choice == "1":
                    asyncio.run(handle_login())
                elif choice == "2":
                    print("\n✨ Thanks for using TELETY!")
                    print("👋 Goodbye!")
                    sys.exit(0)
                else:
                    input("\n❌ Invalid choice. Press Enter to continue...")
                
        except Exception as e:
            log_error(e)
            input(f"\n❌ An error occurred: {str(e)}\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main_menu()
    except Exception as e:
        log_error(e)
        print(f"\n❌ Fatal error: {str(e)}")
        input("\nPress Enter to exit...")
    finally:
        # Clean up streams if we created them
        if hasattr(sys, 'frozen'):
            sys.stdin.close()
            sys.stdout.close()
            sys.stderr.close()