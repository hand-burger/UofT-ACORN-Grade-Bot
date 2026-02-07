# ACORN Monitor 2.0 🎓

A modern CLI tool for UofT students to monitor ACORN for grade updates and record changes in real-time.

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

-   **Duo 2FA Support:** Uses Selenium to handle UofT's modern WebLogin and Duo Security.
-   **Live Dashboard:** A beautiful, terminal-based UI using `rich` that shows a countdown to the next check.
-   **Session Persistence:** Saves your session cookies securely to `cookies.pkl` so you don't have to log in every time.
-   **Smart Notifications:**
    -   **Desktop:** Native Mac/Windows/Linux notifications via `plyer`.
    -   **Email:** Optional Gmail notifications (requires an App Password).
-   **Robust Monitoring:** Automatically re-authenticates if your session expires.

## Installation

1. **Clone the repository**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Chromedriver:**
   The bot uses `webdriver-manager` to automatically download the correct version of Chromedriver for your system.

## Usage

Run the bot:
```bash
python3 main.py
```

1.  **Login:** A Chrome window will open. Log in to ACORN normally and complete the Duo 2FA.
2.  **Monitor:** Once the bot detects a successful login, it will close the browser and start the CLI dashboard.
3.  **Stay Informed:** Keep the terminal running. It will check for updates every 10 minutes and notify you if anything changes.

## Development & Testing

We use `unittest` for verifying the parsing and change detection logic.

**Run tests:**
```bash
python3 tests/test_bot.py
# OR
pytest
```

## Security Note

-   **Cookies:** Your session is stored locally in `cookies.pkl`. This file is ignored by git via `.gitignore` to keep your session private.
-   **Credentials:** This bot **never** asks for or stores your UTORid/Password. You enter them directly into the official UofT login page in the browser window.

## Disclaimer

This tool is for educational purposes only. Use it responsibly and adhere to UofT's IT policies.