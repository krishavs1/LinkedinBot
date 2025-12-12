#!/usr/bin/env python3
"""
LinkedIn Internship Bot
Scrapes LinkedIn for new internship postings and sends hourly email updates.
"""

import os
import json
import time
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import schedule


class LinkedInBot:
    def __init__(self, email_config: Dict, linkedin_url: str):
        """
        Initialize the LinkedIn bot.
        
        Args:
            email_config: Dictionary with email settings (sender, password, recipient, smtp_server, smtp_port)
            linkedin_url: URL to scrape for jobs
        """
        self.email_config = email_config
        self.linkedin_url = linkedin_url
        self.sent_jobs_file = "sent_jobs.json"
        self.sent_job_ids = self._load_sent_jobs()
        self.driver = None
        
    def _load_sent_jobs(self) -> set:
        """Load previously sent job IDs from file."""
        if os.path.exists(self.sent_jobs_file):
            try:
                with open(self.sent_jobs_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('job_ids', []))
            except:
                return set()
        return set()
    
    def _save_sent_jobs(self):
        """Save sent job IDs to file."""
        with open(self.sent_jobs_file, 'w') as f:
            json.dump({'job_ids': list(self.sent_job_ids)}, f)
    
    def _setup_driver(self):
        """Setup Selenium WebDriver with Chrome."""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def _close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def _is_past_hour(self, time_text: str) -> bool:
        """
        Check if job posting time indicates it was posted in the past hour.
        
        Args:
            time_text: Text like "2 hours ago", "1 hour ago", "5 hours ago", etc.
        
        Returns:
            True if posted in the past hour, False otherwise
        """
        time_text = time_text.lower().strip()
        
        # Check for "hour ago" or "hours ago"
        if "hour ago" in time_text or "hours ago" in time_text:
            # Extract number
            try:
                # Handle "1 hour ago" or "2 hours ago"
                parts = time_text.split()
                if len(parts) >= 2:
                    num = int(parts[0])
                    return num == 1  # Only "1 hour ago" or "hour ago" (which we'll treat as 1)
            except:
                pass
        
        # Check for minutes (anything with "minute" is within the hour)
        if "minute" in time_text:
            return True
        
        # Check for "just now" or similar
        if "just now" in time_text or "now" in time_text:
            return True
        
        return False
    
    def scrape_jobs(self) -> List[Dict]:
        """
        Scrape LinkedIn jobs from the configured URL.
        
        Returns:
            List of job dictionaries with title, company, location, link, and time
        """
        jobs = []
        
        try:
            self._setup_driver()
            print(f"Navigating to: {self.linkedin_url}")
            self.driver.get(self.linkedin_url)
            
            # Wait for job listings to load
            time.sleep(5)  # Give page time to load
            
            # Try to find job cards - LinkedIn uses various selectors
            # Common selectors for job listings
            job_selectors = [
                "div.job-search-card",
                "div.base-card",
                "li.jobs-search-results__list-item",
                "div[data-job-id]"
            ]
            
            job_elements = []
            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        job_elements = elements
                        print(f"Found {len(elements)} jobs using selector: {selector}")
                        break
                except:
                    continue
            
            if not job_elements:
                print("No job elements found. Page might require login or have changed structure.")
                print("Trying alternative approach...")
                # Try to get all links that might be job postings
                job_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/jobs/view/']")
            
            for element in job_elements[:50]:  # Limit to first 50 to avoid timeout
                try:
                    # Extract job information
                    job_data = {}
                    
                    # Try to get job title
                    title_selectors = [
                        "h3.base-search-card__title",
                        "h3.job-search-card__title",
                        "a.job-search-card__title-link",
                        "span.job-search-card__title"
                    ]
                    
                    title = None
                    for title_sel in title_selectors:
                        try:
                            title_elem = element.find_element(By.CSS_SELECTOR, title_sel)
                            title = title_elem.text.strip()
                            break
                        except:
                            continue
                    
                    if not title:
                        # Try to get text from the element itself
                        title = element.text.split('\n')[0] if element.text else "Unknown"
                    
                    # Try to get company name
                    company_selectors = [
                        "h4.base-search-card__subtitle",
                        "h4.job-search-card__subtitle",
                        "a.job-search-card__subtitle-link"
                    ]
                    
                    company = "Unknown"
                    for company_sel in company_selectors:
                        try:
                            company_elem = element.find_element(By.CSS_SELECTOR, company_sel)
                            company = company_elem.text.strip()
                            break
                        except:
                            continue
                    
                    # Try to get location
                    location_selectors = [
                        "span.job-search-card__location",
                        "span.base-search-card__metadata"
                    ]
                    
                    location = "Unknown"
                    for loc_sel in location_selectors:
                        try:
                            loc_elem = element.find_element(By.CSS_SELECTOR, loc_sel)
                            location = loc_elem.text.strip()
                            break
                        except:
                            continue
                    
                    # Try to get job link
                    link = None
                    try:
                        link_elem = element.find_element(By.CSS_SELECTOR, "a[href*='/jobs/view/']")
                        link = link_elem.get_attribute('href')
                    except:
                        # Try to get href from the element itself
                        try:
                            link = element.get_attribute('href')
                        except:
                            pass
                    
                    # Try to get time posted
                    time_selectors = [
                        "time.job-search-card__listdate",
                        "time[datetime]",
                        "span.job-search-card__listdate"
                    ]
                    
                    time_posted = "Unknown"
                    for time_sel in time_selectors:
                        try:
                            time_elem = element.find_element(By.CSS_SELECTOR, time_sel)
                            time_posted = time_elem.text.strip() or time_elem.get_attribute('datetime')
                            break
                        except:
                            continue
                    
                    # If we couldn't find time, try looking for "ago" text in the element
                    if time_posted == "Unknown":
                        element_text = element.text
                        if "ago" in element_text.lower():
                            # Extract the time portion
                            lines = element_text.split('\n')
                            for line in lines:
                                if "ago" in line.lower():
                                    time_posted = line.strip()
                                    break
                    
                    if title and title != "Unknown":
                        # Create a unique ID for this job
                        job_id = f"{title}_{company}_{location}".replace(" ", "_").lower()
                        
                        job_data = {
                            'id': job_id,
                            'title': title,
                            'company': company,
                            'location': location,
                            'link': link or self.linkedin_url,
                            'time_posted': time_posted
                        }
                        
                        jobs.append(job_data)
                
                except Exception as e:
                    print(f"Error extracting job data: {e}")
                    continue
            
            print(f"Scraped {len(jobs)} jobs total")
            
        except Exception as e:
            print(f"Error scraping jobs: {e}")
        finally:
            self._close_driver()
        
        return jobs
    
    def filter_new_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Filter jobs to only include those posted in the past hour and not yet sent.
        
        Args:
            jobs: List of all scraped jobs
        
        Returns:
            List of new jobs posted in the past hour
        """
        new_jobs = []
        
        for job in jobs:
            job_id = job.get('id')
            time_posted = job.get('time_posted', '')
            
            # Skip if we've already sent this job
            if job_id in self.sent_job_ids:
                continue
            
            # Check if posted in the past hour
            if self._is_past_hour(time_posted):
                new_jobs.append(job)
                self.sent_job_ids.add(job_id)
        
        return new_jobs
    
    def send_email(self, jobs: List[Dict]):
        """
        Send email with new job listings.
        
        Args:
            jobs: List of job dictionaries to include in email
        """
        if not jobs:
            print("No new jobs to send.")
            return
        
        try:
            # Create email
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender']
            msg['To'] = self.email_config['recipient']
            msg['Subject'] = f"New LinkedIn Internships - {len(jobs)} New Posting(s)"
            
            # Create email body
            body = f"""
            <html>
            <head></head>
            <body>
                <h2>New LinkedIn Internship Postings (Past Hour)</h2>
                <p>Found <strong>{len(jobs)}</strong> new internship posting(s) in the past hour:</p>
                <ul>
            """
            
            for job in jobs:
                body += f"""
                    <li>
                        <strong>{job['title']}</strong><br>
                        Company: {job['company']}<br>
                        Location: {job['location']}<br>
                        Posted: {job['time_posted']}<br>
                        <a href="{job['link']}">View Job</a>
                    </li>
                    <br>
                """
            
            body += """
                </ul>
                <p>Happy job hunting!</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender'], self.email_config['password'])
            text = msg.as_string()
            server.sendmail(self.email_config['sender'], self.email_config['recipient'], text)
            server.quit()
            
            print(f"Email sent successfully with {len(jobs)} jobs!")
            self._save_sent_jobs()
            
        except Exception as e:
            print(f"Error sending email: {e}")
    
    def run(self):
        """Run one iteration of the bot: scrape, filter, and send email."""
        print(f"\n[{datetime.now()}] Starting LinkedIn bot run...")
        jobs = self.scrape_jobs()
        new_jobs = self.filter_new_jobs(jobs)
        
        if new_jobs:
            print(f"Found {len(new_jobs)} new jobs posted in the past hour!")
            self.send_email(new_jobs)
        else:
            print("No new jobs found in the past hour.")
        
        print(f"[{datetime.now()}] Bot run complete.\n")
    
    def start_scheduler(self):
        """Start the hourly scheduler."""
        print("Starting LinkedIn bot scheduler...")
        print("Bot will run every hour.")
        print("Press Ctrl+C to stop.")
        
        # Schedule to run every hour
        schedule.every().hour.do(self.run)
        
        # Run immediately on start
        self.run()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    """Main function to run the bot."""
    # Load configuration from environment variables or config file
    email_config = {
        'sender': os.getenv('EMAIL_SENDER', ''),
        'password': os.getenv('EMAIL_PASSWORD', ''),
        'recipient': os.getenv('EMAIL_RECIPIENT', ''),
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', '587'))
    }
    
    linkedin_url = os.getenv('LINKEDIN_URL', 
        'https://www.linkedin.com/jobs/search/?keywords=software%20engineer%20intern&f_TPR=r86400&f_E=1')
    
    # Validate configuration
    if not email_config['sender'] or not email_config['password'] or not email_config['recipient']:
        print("Error: Email configuration missing!")
        print("Please set the following environment variables:")
        print("  - EMAIL_SENDER: Your email address")
        print("  - EMAIL_PASSWORD: Your email password or app password")
        print("  - EMAIL_RECIPIENT: Recipient email address")
        print("\nOptional:")
        print("  - SMTP_SERVER: SMTP server (default: smtp.gmail.com)")
        print("  - SMTP_PORT: SMTP port (default: 587)")
        print("  - LINKEDIN_URL: LinkedIn jobs URL to scrape")
        return
    
    # Create and run bot
    bot = LinkedInBot(email_config, linkedin_url)
    
    try:
        bot.start_scheduler()
    except KeyboardInterrupt:
        print("\nStopping bot...")
        bot._close_driver()


if __name__ == "__main__":
    main()





