Collecting workspace informationFiltering to most relevant information`@workspace` accuracy and speed can be improved by building a remote workspace index. [Learn More](https://aka.ms/vscode-copilot-workspace-remote-index)

Build remote workspace index

```markdown
# Telety - Automation Script

## Description

Telety is a Python script designed to automate tasks, primarily focused on Telegram-related activities such as scraping users and adding members to groups.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Main Menu](#main-menu)
  - [Login](#login)
  - [Scraping Users](#scraping-users)
  - [Adding Members](#adding-members)
  - [Posting Bot](#posting-bot)
  - [Resetting Sessions](#resetting-sessions)
- [Error Handling](#error-handling)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

Before using Telety, ensure you have the following:

- Python 3.7+ installed
- `pip` package installer
- A Telegram account
- API ID and API Hash from Telegram (obtained through [Telegram's developer resources](https://core.telegram.org/api/obtaining_api_id))

## Installation

1.  Clone the repository:

```sh
git clone <repository_url>
cd Telety
```

2.  Install the required Python packages:

```sh
pip install -r requirements.txt
```

## Configuration

1.  Obtain your Telegram API ID and API Hash from Telegram's developer resources.
2.  Locate the `config.json` file. If it doesn't exist, run the script once to generate a default configuration.
3.  Edit `config.json` to include your API ID and API Hash:

```json
{
  "api_id": YOUR_API_ID,
  "api_hash": "YOUR_API_HASH",
  "session_files": {
    "scraper_session": "scraper_session",
    "adder_session": "adder_session"
  }
}
```

## Usage

### Main Menu

The main.py script serves as the entry point for Telety. Run it from the command line:

```sh
python main.py
```

This will display the main menu with the following options:

1.  Login
2.  Scrape Users from Group
3.  Add Members to Group
4.  Start Posting Bot
5.  Logout
6.  Exit

### Login

-   Select option `1` from the main menu.
-   The script will attempt to log you in using QR code authentication. Follow the prompts to scan the QR code using your Telegram mobile app (Settings -> Devices -> Link Desktop Device).
-   A session file (`telety_session.session`) will be created to store your login information for future use.

### Scraping Users

1.  Select option `2` from the main menu.
2.  Enter the target group link or ID when prompted.
3.  The script will scrape user information from the specified group and save it to a text file (`users_<group_name>_<timestamp>.txt`).

### Adding Members

1.  Select option `3` from the main menu.
2.  Enter the path to the username file (a text file with one username per line).
3.  Enter the target group link or ID when prompted.
4.  The script will add users from the file to the specified group, respecting Telegram's rate limits and daily limits.

### Posting Bot

1.  Select option `4` from the main menu.
2.  Enter the bot token when prompted.
3.  The bot will start and you can use the following commands in Telegram:
    -   `/addgroup`: Add a group to the bot's list.
    -   `/removegroup`: Remove a group from the bot's list.
    -   `/groups`: List all saved groups.
    -   `/post`: Post the stored message to all saved groups.
    -   `/cancel`: Cancel the current operation and clear the stored message.

### Resetting Sessions

To clear existing session files and avoid potential clashes, run the reset.py script:

```sh
python reset.py
```

This will remove all `.session` and `.session-journal` files in the current directory.

## Error Handling

The script includes error handling and logging mechanisms. Errors are logged to `errors.txt` with timestamps.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License.
```
