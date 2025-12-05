# LinkedIn Internship Bot

A Python bot that automatically scrapes LinkedIn for new internship postings and sends email notifications.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install ChromeDriver:
   - Make sure you have Google Chrome installed
   - Download ChromeDriver from https://chromedriver.chromium.org/ (match your Chrome version)
   - Or install via Homebrew on macOS: `brew install chromedriver`

3. Set up email configuration:
   - For Gmail, you'll need to use an [App Password](https://support.google.com/accounts/answer/185833)
   - Set environment variables:
```bash
export EMAIL_SENDER="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password"
export EMAIL_RECIPIENT="recipient@gmail.com"
```

## Usage

### Automated Bot (Recommended)
Run the bot that automatically checks every 5 minutes and sends emails:

```bash
python bot.py
```

The bot will:
- Run `scrape.py` every 5 minutes
- Track which jobs have already been sent (stored in `sent_jobs.json`)
- Send email notifications only for new jobs
- Run continuously until you stop it (Ctrl+C)

### Manual Scraping
Run the scraper manually to see results in the terminal:

```bash
python scrape.py
```

Or with a custom URL:
```bash
python scrape.py "https://www.linkedin.com/jobs/search/?keywords=software%20engineer%20intern&f_TPR=r600&f_E=1"
```

### Environment Variables

Optional environment variables:
```bash
export LINKEDIN_URL="https://www.linkedin.com/jobs/search/?keywords=software%20engineer%20intern&f_TPR=r600&f_E=1"
export SMTP_SERVER="smtp.gmail.com"  # Default
export SMTP_PORT="587"  # Default
```

## Files

- `bot.py` - Main bot that runs on a schedule and sends emails
- `scrape.py` - Scraper that extracts job postings from LinkedIn
- `sent_jobs.json` - Tracks which jobs have been sent (created automatically)

## Notes

- The bot uses Selenium to handle JavaScript-rendered content
- By default, the browser runs in visible mode (you can see it working)
- If you want headless mode, uncomment the headless option in `scrape.py`
- LinkedIn may require login for some searches - if you see a login page, you may need to add authentication
- The bot tracks sent jobs to avoid duplicate emails



