import sys
import time
import smtplib
import pickle
import os
import requests
import getpass
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.align import Align
from plyer import notification

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
COOKIES_FILE = "cookies.pkl"
CHECK_INTERVAL_SECONDS = 600 # 10 minutes
URLS = {
    'acorn': 'https://acorn.utoronto.ca/',
    'complete_academic_history': 'https://acorn.utoronto.ca/sws/rest/history/academic/complete',
    'logout': 'https://acorn.utoronto.ca/sws/auth/logout'
}

console = Console()

class AcornBot:
    def __init__(self):
        self.session = requests.Session()
        self.email_config = {}
        self.current_courses = {}
        self.last_check_time = "Never"
        self.next_check_time = None
        self.status_message = "Initializing..."

    def load_cookies(self):
        if os.path.exists(COOKIES_FILE):
            try:
                with open(COOKIES_FILE, 'rb') as f:
                    cookies = pickle.load(f)
                    self.session.cookies.update(cookies)
                return True
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load cookies: {e}[/yellow]")
        return False

    def save_cookies(self):
        try:
            with open(COOKIES_FILE, 'wb') as f:
                pickle.dump(self.session.cookies, f)
        except Exception as e:
            console.print(f"[red]Error saving cookies: {e}[/red]")

    def login(self):
        if self.load_cookies():
            self.status_message = "Restoring session..."
            if self.test_session():
                self.status_message = "Session restored."
                return

        self.status_message = "Auth required (Browser opening...)"
        self.perform_selenium_login()

    def perform_selenium_login(self):
        chrome_options = Options()
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get(URLS['acorn'])
            wait_long = WebDriverWait(driver, 300)
            wait_long.until(EC.url_contains("acorn.utoronto.ca/sws"))
            
            selenium_cookies = driver.get_cookies()
            self.session = requests.Session()
            for cookie in selenium_cookies:
                self.session.cookies.set(cookie['name'], cookie['value'])
            self.save_cookies()
            self.status_message = "Login successful."
        except Exception as e:
            self.status_message = f"Login failed: {e}"
            sys.exit(1)
        finally:
            if driver:
                driver.quit()

    def test_session(self):
        try:
            r = self.session.get(URLS['complete_academic_history'], allow_redirects=False, timeout=10)
            return r.status_code == 200 and "courses blok" in r.text
        except:
            return False

    def fetch_grades(self):
        try:
            response = self.session.get(URLS['complete_academic_history'], timeout=15)
            if response.status_code != 200 or "courses blok" not in response.text:
                return None
            return self.parse_grades(response.text)
        except Exception as e:
            self.status_message = f"Fetch error: {e}"
            return None

    def parse_grades(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        courses = {}
        course_divs = soup.find_all('div', class_=lambda x: x and 'courses' in x and 'blok' in x)
        for div in course_divs:
            text = div.get_text(strip=True)
            courses[text] = {'raw': text}
        return courses

    def check_for_changes(self, new_courses):
        if not self.current_courses:
            self.current_courses = new_courses
            return []

        changes = []
        for course_id, data in new_courses.items():
            if course_id not in self.current_courses:
                changes.append(f"New update/grade: {data['raw']}")
        return changes

    def send_notification(self, changes):
        msg_text = "\n".join(changes)
        
        # Desktop Notification
        try:
            # Try plyer first
            notification.notify(
                title='ACORN Grade Update!',
                message=msg_text[:256],
                app_name='ACORN Bot'
            )
        except Exception:
            # Fallback for macOS native notifications via AppleScript
            if sys.platform == "darwin":
                try:
                    title = "ACORN Grade Update!"
                    # Escape double quotes for AppleScript
                    clean_msg = msg_text.replace('"', '\\"')
                    os.system(f'osascript -e "display notification \\"{clean_msg}\\" with title \\"{title}\\""')
                except:
                    pass

        if self.email_config:
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(self.email_config['user'], self.email_config['pass'])
                msg = f"Subject: ACORN Grade Update\n\nChanges:\n{msg_text}"
                server.sendmail(self.email_config['user'], self.email_config['user'], msg)
                server.quit()
            except: pass

    def setup_email(self):
        console.print(Panel("[bold]Optional Email Notifications[/bold]\nLeave blank to skip."))
        user = console.input("Email (Gmail): ")
        if user:
            pw = getpass.getpass("App Password: ")
            self.email_config = {'user': user, 'pass': pw}

    def make_layout(self, countdown_str):
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )

        table = Table(expand=True, title="[bold cyan]Current Academic Records[/bold cyan]")
        table.add_column("Course / Grade Entry", style="white")
        for course in self.current_courses.values():
            table.add_row(course['raw'])

        layout["header"].update(Panel(Align.center(f"[bold blue]ACORN Monitor[/bold blue] | Last Checked: [yellow]{self.last_check_time}[/yellow]"), style="blue"))
        layout["main"].update(table)
        
        status_color = "green" if "successful" in self.status_message or "records" in self.status_message.lower() else "yellow"
        footer_content = f"Status: [{status_color}]{self.status_message}[/{status_color}] | Next check in: [bold white]{countdown_str}[/bold white]"
        layout["footer"].update(Panel(footer_content, style="white"))
        
        return layout

    def run(self):
        console.clear()
        console.print(Panel.fit("[bold blue]ACORN Grade Bot 2.0[/bold blue]\nMonitoring for ACORN record updates..."))
        
        self.setup_email()
        self.login()
        
        initial_data = self.fetch_grades()
        if initial_data:
            self.current_courses = initial_data
            self.last_check_time = datetime.now().strftime("%H:%M:%S")
            self.status_message = "Initial records loaded."
        else:
            console.print("[red]Failed to fetch initial data. Check your connection.[/red]")
            return

        while True:
            self.next_check_time = datetime.now() + timedelta(seconds=CHECK_INTERVAL_SECONDS)
            
            # Countdown Loop
            with Live(self.make_layout("..."), refresh_per_second=1, screen=True) as live:
                while datetime.now() < self.next_check_time:
                    remaining = int((self.next_check_time - datetime.now()).total_seconds())
                    mins, secs = divmod(remaining, 60)
                    live.update(self.make_layout(f"{mins:02d}:{secs:02d}"))
                    time.sleep(0.5)
                
                # Perform Check
                self.status_message = "Checking for updates..."
                live.update(self.make_layout("Now!"))
                
                new_data = self.fetch_grades()
                if new_data is None:
                    self.status_message = "Session expired. Re-logging..."
                    live.update(self.make_layout("Wait..."))
                    self.login()
                    new_data = self.fetch_grades()

                if new_data:
                    changes = self.check_for_changes(new_data)
                    self.last_check_time = datetime.now().strftime("%H:%M:%S")
                    if changes:
                        self.current_courses = new_data
                        self.status_message = f"[bold red]NEW GRADE DETECTED![/bold red]"
                        self.send_notification(changes)
                    else:
                        self.status_message = "No new grades detected."
                    live.update(self.make_layout("Done"))

if __name__ == "__main__":
    bot = AcornBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        console.print("\n[bold]Monitoring stopped.[/bold]")
