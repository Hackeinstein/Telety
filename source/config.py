import json
import os
import sys

def get_config_path():
    """Get config.json path with fallback locations"""
    # Check in the same directory as the executable
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        exe_config = os.path.join(exe_dir, 'config.json')
        if os.path.exists(exe_config):
            return exe_config

    # Check in current working directory
    cwd_config = os.path.join(os.getcwd(), 'config.json')
    if os.path.exists(cwd_config):
        return cwd_config

    # Check in script directory as last resort
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_config = os.path.join(script_dir, 'config.json')
    if os.path.exists(default_config):
        return default_config

    return None

def create_default_config(path):
    """Create a default config.json file"""
    default_config = {
        "api_id": None,  # Need to be filled by user
        "api_hash": "",  # Need to be filled by user
        "session_files": {
            "scraper_session": "scraper_session",
            "adder_session": "adder_session"
        }
    }
    
    try:
        with open(path, 'w') as f:
            json.dump(default_config, f, indent=4)
        print(f"\n✨ Created default config at: {path}")
        print("⚠️ Please edit config.json and add your API credentials")
    except Exception as e:
        print(f"\n❌ Error creating default config: {str(e)}")

def load_config():
    """Load configuration from config.json"""
    config_path = get_config_path()
    
    # If no config exists, create default in exe/cwd directory
    if not config_path:
        target_path = os.path.join(os.getcwd(), 'config.json')
        create_default_config(target_path)
        return None, None, "scraper_session", "adder_session"
        
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Validate API credentials
        if not config['api_id'] or not config['api_hash']:
            print("\n❌ API credentials not set in config.json")
            print(f"📝 Please edit: {config_path}")
            return None, None, "scraper_session", "adder_session"
            
        return (
            config['api_id'],
            config['api_hash'],
            config['session_files']['scraper_session'],
            config['session_files']['adder_session']
        )
    except Exception as e:
        print(f"\n❌ Error loading config: {str(e)}")
        print(f"📝 Please check: {config_path}")
        return None, None, "scraper_session", "adder_session"

# Load and export config values
API_ID, API_HASH, SCRAPER_SESSION, ADDER_SESSION = load_config()