# University of Toronto ACORN Academic History Bot
This simple Python program scrapes your Academic History from ACORN and notifies you of any updates in marks, grades, GPA, etc.

Using the `smtplib` and `requests` libraries, the program detects changes in your Academic History and optionally, sends you an email to notify you.
## Usage
Make sure you have the `requests` library installed. Use `pip install requests` if it is not already installed.

- To run this program you can either run it through the terminal with `python main.py` or in an IDE.
- Then, follow the prompts, entering your UTORid and password.
    - If you want email notifications, then enter your email and password.
        - Note: in order for your email to be able to send, search "how to send from (your email type) using SMTP" and follow the appropriate steps.
        - For Gmail this involves generating an app password which is used instead of your normal account password.
        - Note also: the email will be sent and received by the email you enter.
    - You can also enter your credentials at the top of the Python file to avoid typing it each time the program is ran.
- Your complete academic history will appear in the output, and every 10 minutes, the program will check for any changes.
