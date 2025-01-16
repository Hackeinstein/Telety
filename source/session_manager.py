import os
import json
import qrcode
from typing import Tuple, Optional
from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from config import API_ID, API_HASH, SCRAPER_SESSION, ADDER_SESSION

class SessionManager:
    def __init__(self):
        self.config_file = 'telety_config.json'
        self.session_files = [SCRAPER_SESSION + '.session', ADDER_SESSION + '.session']

    async def generate_qr_login(self, client: TelegramClient) -> bool:
        """Generate and display QR code for login"""
        try:
            print("\n📱 Generating QR code for login...")
            qr_login = await client.qr_login()
            
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

    async def get_client(self, session_name: str = 'telety_session') -> Optional[TelegramClient]:
        """Get TelegramClient with QR login if needed"""
        try:
            client = TelegramClient(session_name, API_ID, API_HASH)
            await client.connect()
            
            if not await client.is_user_authorized():
                print("\n🔄 No active session found")
                if not await self.generate_qr_login(client):
                    await client.disconnect()
                    return None
            
            return client
            
        except Exception as e:
            print(f"\n❌ Error initializing client: {str(e)}")
            return None

    def logout(self) -> bool:
        """Logout by removing session files"""
        try:
            logged_out = False
            for session_file in self.session_files:
                if os.path.exists(session_file):
                    os.remove(session_file)
                    logged_out = True
            
            if logged_out:
                print("\n✅ Successfully logged out!")
            else:
                print("\n⚠️ No active sessions found")
            return True
        except Exception as e:
            print(f"\n❌ Error during logout: {str(e)}")
            return False