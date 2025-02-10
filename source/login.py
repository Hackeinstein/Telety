
import os
import qrcode
from telethon import TelegramClient
from config import API_ID, API_HASH

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

async def handle_qr_login(client: TelegramClient) -> bool:
    """Handle QR code login process"""
    try:
        print("\n📱 Generating QR code for login...")
        qr_login = await client.qr_login()
        
        clear_screen()
        print_header()
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=2, border=1)
        qr.add_data(qr_login.url)
        qr.make(fit=True)
        
        # Display instructions
        print("\n🔐 Login with QR Code:")
        print("1️⃣ Open Telegram on your phone")
        print("2️⃣ Go to Settings → Devices → Link Desktop Device")
        print("3️⃣ Point your phone's camera at this QR code\n")
        
        # Display QR code
        qr.print_ascii()
        print("\n⏳ Waiting for you to scan... (60 seconds)")
        
        try:
            await qr_login.wait(timeout=60)
            print("\n✅ Successfully logged in!")
            return True
        except Exception as e:
            print("\n❌ QR code expired or login failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during QR login: {str(e)}")
        return False

async def start_login() -> bool:
    """Initialize login process"""
    try:
        client = TelegramClient('telety_session', API_ID, API_HASH)
        await client.connect()
        
        if await client.is_user_authorized():
            print("\n✅ Already logged in!")
            await client.disconnect()
            return True
            
        success = await handle_qr_login(client)
        await client.disconnect()
        return success
        
    except Exception as e:
        print(f"\n❌ Login error: {str(e)}")
        return False

def check_session() -> bool:
    """Check if a valid session exists"""
    try:
        return os.path.exists('telety_session.session')
    except:
        return False