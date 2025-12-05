#!/usr/bin/env python3
"""
LinkedIn Internship Bot
Runs scrape.py every 5 minutes and sends email notifications for new job postings.
"""

import os
import json
import time
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
import schedule

# Import the scraping function from scrape.py
from scrape import scrape_linkedin_jobs


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
    
    def _get_job_id(self, job: Dict) -> str:
        """Generate a unique ID for a job based on its link."""
        link = job.get('link', '')
        # Use the job ID from the URL if available, otherwise use the full link
        if '/jobs/view/' in link:
            # Extract job ID from URL like: https://www.linkedin.com/jobs/view/1234567890/
            parts = link.split('/jobs/view/')
            if len(parts) > 1:
                job_id = parts[1].split('/')[0].split('?')[0]
                return job_id
        # Fallback: use cleaned link as ID
        return link.split('?')[0] if '?' in link else link
    
    def filter_new_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Filter jobs to only include those not yet sent.
        
        Args:
            jobs: List of all scraped jobs
        
        Returns:
            List of new jobs that haven't been sent yet
        """
        new_jobs = []
        
        for job in jobs:
            job_id = self._get_job_id(job)
            
            # Skip if we've already sent this job
            if job_id in self.sent_job_ids:
                continue
            
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
                <h2>New LinkedIn Internship Postings</h2>
                <p>Found <strong>{len(jobs)}</strong> new internship posting(s):</p>
                <ul>
            """
            
            for job in jobs:
                title = job.get('title', 'Unknown Job')
                company = job.get('company', 'Company not found')
                link = job.get('link', '#')
                # Debug: print job data
                print(f"  Adding job: {title} at {company}")
                body += f"""
                    <li style="margin-bottom: 15px;">
                        <strong>{title}</strong><br>
                        <strong>Company:</strong> {company}<br>
                        <a href="{link}">View Job on LinkedIn</a>
                    </li>
                """
            
            body += """
                </ul>
                <p>Happy job hunting!</p>
                <p><small>This is an automated message from your LinkedIn Internship Bot.</small></p>
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
            
            print(f"✓ Email sent successfully with {len(jobs)} jobs!")
            self._save_sent_jobs()
            
        except Exception as e:
            print(f"✗ Error sending email: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Run one iteration of the bot: scrape, filter, and send email."""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting LinkedIn bot run...")
        
        try:
            # Scrape jobs
            print("Scraping LinkedIn for new jobs...")
            jobs = scrape_linkedin_jobs(self.linkedin_url)
            print(f"Found {len(jobs)} total jobs")
            
            # Filter for new jobs
            new_jobs = self.filter_new_jobs(jobs)
            
            if new_jobs:
                print(f"Found {len(new_jobs)} new jobs!")
                self.send_email(new_jobs)
            else:
                print("No new jobs found.")
        
        except Exception as e:
            print(f"✗ Error during bot run: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bot run complete.\n")
    
    def start_scheduler(self):
        """Start the 5-minute scheduler."""
        print("=" * 60)
        print("LinkedIn Internship Bot - Starting Scheduler")
        print("=" * 60)
        print("Bot will run every 5 minutes.")
        print("Press Ctrl+C to stop.")
        print("=" * 60)
        
        # Schedule to run every 5 minutes
        schedule.every(5).minutes.do(self.run)
        
        # Run immediately on start
        print("\nRunning initial scrape...")
        self.run()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds


def main():
    """Main function to run the bot."""
    # Load configuration from environment variables
    email_config = {
        'sender': os.getenv('EMAIL_SENDER', ''),
        'password': os.getenv('EMAIL_PASSWORD', ''),
        'recipient': os.getenv('EMAIL_RECIPIENT', ''),
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', '587'))
    }
    
    linkedin_url = os.getenv('LINKEDIN_URL', 
        'https://www.linkedin.com/jobs/search/?keywords=software%20engineer%20intern&f_TPR=r8600&f_E=1')
    
    # Validate configuration
    if not email_config['sender'] or not email_config['password'] or not email_config['recipient']:
        print("Error: Email configuration missing!")
        print("\nPlease set the following environment variables:")
        print("  - EMAIL_SENDER: Your email address")
        print("  - EMAIL_PASSWORD: Your email password or app password")
        print("  - EMAIL_RECIPIENT: Recipient email address")
        print("\nOptional:")
        print("  - SMTP_SERVER: SMTP server (default: smtp.gmail.com)")
        print("  - SMTP_PORT: SMTP port (default: 587)")
        print("  - LINKEDIN_URL: LinkedIn jobs URL to scrape")
        print("\nExample:")
        print("  export EMAIL_SENDER='your-email@gmail.com'")
        print("  export EMAIL_PASSWORD='your-app-password'")
        print("  export EMAIL_RECIPIENT='recipient@gmail.com'")
        print("  python bot.py")
        return
    
    # Create and run bot
    bot = LinkedInBot(email_config, linkedin_url)
    
    try:
        bot.start_scheduler()
    except KeyboardInterrupt:
        print("\n\nStopping bot...")
        print("Goodbye!")


if __name__ == "__main__":
    main()

