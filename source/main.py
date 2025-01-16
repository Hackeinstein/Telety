# main.py
import os
import sys
from datetime import datetime
from typing import NoReturn

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
████████╗███████╗██╗     ███████╗████████╗██╗   ██╗
╚══██╔══╝██╔════╝██║     ██╔════╝╚══██╔══╝╚██╗ ██╔╝
   ██║   █████╗  ██║     █████╗     ██║    ╚████╔╝ 
   ██║   ██╔══╝  ██║     ██╔══╝     ██║     ╚██╔╝  
   ██║   ███████╗███████╗███████╗   ██║      ██║   
   ╚═╝   ╚══════╝╚══════╝╚══════╝   ╚═╝      ╚═╝   
    """
    print(header)

def main_menu() -> None:
    """Display and handle main menu"""
    while True:
        try:
            clear_screen()
            print_header()
            print("\nMain Menu:")
            print("1. Scrape Users")
            print("2. Add Members")
            print("3. Post to Multiple Groups")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ")
            
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
                print("\nThanks for using TELETY!")
                sys.exit(0)
            else:
                input("\nInvalid choice. Press Enter to continue...")
                
        except Exception as e:
            log_error(e)
            input(f"\nAn error occurred: {str(e)}\nPress Enter to continue...")

if __name__ == "__main__":
    main_menu()