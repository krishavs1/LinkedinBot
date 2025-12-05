#!/usr/bin/env python3
"""
LinkedIn Job Scraper
Scrapes LinkedIn job postings and returns job titles with their links.
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import List, Dict


def setup_driver():
    """Setup Selenium WebDriver with Chrome."""
    chrome_options = Options()
    # Remove headless mode so you can see what's happening (comment out if you want headless)
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def scrape_linkedin_jobs(url: str) -> List[Dict[str, str]]:
    """
    Scrape LinkedIn jobs from the given URL.
    
    Args:
        url: LinkedIn jobs search URL
    
    Returns:
        List of dictionaries with 'title' and 'link' keys
    """
    jobs = []
    driver = None
    
    try:
        driver = setup_driver()
        print(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(5)
        
        # Scroll down multiple times to load all lazy-loaded jobs
        print("Scrolling to load all jobs (LinkedIn uses lazy loading)...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scrolls = 10
        
        while scroll_attempts < max_scrolls:
            # Scroll to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for content to load
            
            # Calculate new scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                # No new content loaded, try scrolling by smaller increments
                driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(1)
                break
            
            last_height = new_height
            scroll_attempts += 1
            print(f"  Scroll {scroll_attempts}: Found {new_height}px height")
        
        # Wait a bit more for any remaining content
        time.sleep(2)
        
        # Primary approach: Find all job links directly (most reliable)
        print("\nSearching for job links...")
        job_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/jobs/view/']")
        print(f"Found {len(job_links)} job link elements")
        
        seen_links = set()
        
        for link_elem in job_links:
            try:
                href = link_elem.get_attribute('href')
                if not href or href in seen_links:
                    continue
                
                # Clean the link (remove query parameters that might make it look different)
                clean_href = href.split('?')[0] if '?' in href else href
                if clean_href in seen_links:
                    continue
                
                seen_links.add(clean_href)
                seen_links.add(href)  # Also track the original
                
                # Try to get title and company from various locations with improved methods
                title = None
                company = None
                link_text = None
                
                # Method 1: Extract title and company from URL (very reliable, doesn't depend on page structure!)
                try:
                    # LinkedIn URL format: /jobs/view/job-title-slug-at-company-name-jobid
                    # Example: /jobs/view/software-engineer-intern-at-docusign-4322361530
                    if '/jobs/view/' in href:
                        # Extract the slug part (everything after /jobs/view/ and before ?)
                        slug_part = href.split('/jobs/view/')[1].split('?')[0]
                        # Remove the job ID at the end (trailing numbers after last dash)
                        slug_clean = re.sub(r'-\d+$', '', slug_part)
                        # Split by "at" to separate title from company
                        if '-at-' in slug_clean.lower():
                            parts = slug_clean.rsplit('-at-', 1)
                            title_part = parts[0]
                            company_part = parts[1] if len(parts) > 1 else None
                            # Replace dashes with spaces and title case it
                            title_from_url = title_part.replace('-', ' ').title()
                            if title_from_url and len(title_from_url) > 3:
                                title = title_from_url
                            # Extract company name
                            if company_part:
                                company_from_url = company_part.replace('-', ' ').title()
                                if company_from_url and len(company_from_url) > 1:
                                    company = company_from_url
                        else:
                            # No company in URL, just extract title
                            title_part = slug_clean
                            title_from_url = title_part.replace('-', ' ').title()
                            if title_from_url and len(title_from_url) > 3:
                                title = title_from_url
                except:
                    pass
                
                # Method 2: Try to get title from the link element itself
                if not title:
                    try:
                        link_text = link_elem.text.strip()
                        if link_text and len(link_text) > 3 and link_text.lower() != "view job":
                            title = link_text
                    except:
                        pass
                
                # Method 3: Try specific LinkedIn selectors in parent container
                if not title:
                    try:
                        # Find the parent container (job card) - try multiple levels
                        parent = None
                        try:
                            parent = link_elem.find_element(By.XPATH, "./ancestor::div[contains(@class, 'job') or contains(@class, 'card') or contains(@class, 'result') or contains(@class, 'base-card')][1]")
                        except:
                            try:
                                parent = link_elem.find_element(By.XPATH, "./ancestor::li[contains(@class, 'job') or contains(@class, 'result')][1]")
                            except:
                                parent = link_elem.find_element(By.XPATH, "./..")
                        
                        if parent:
                            # Try specific LinkedIn title selectors
                            title_selectors = [
                                "h3.base-search-card__title",
                                "h3.job-search-card__title",
                                "h3.job-result-card__title",
                                "h2.job-result-card__title",
                                "h3[class*='title']",
                                "h2[class*='title']",
                                "a.job-search-card__title-link",
                                "span.job-search-card__title",
                                "h3",
                                "h2"
                            ]
                            
                            for selector in title_selectors:
                                try:
                                    title_elem = parent.find_element(By.CSS_SELECTOR, selector)
                                    text = title_elem.text.strip()
                                    if text and len(text) > 3 and text != link_text and text.lower() not in ['view job', 'apply', 'save']:
                                        title = text
                                        break
                                except:
                                    continue
                            
                            # If still no title, try to find any heading element
                            if not title:
                                try:
                                    headings = parent.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4")
                                    for heading in headings:
                                        text = heading.text.strip()
                                        if text and len(text) > 3 and text != link_text:
                                            title = text
                                            break
                                except:
                                    pass
                            
                            # Also try spans and divs that might contain the title
                            if not title:
                                try:
                                    # Look for spans/divs with title-like classes or attributes
                                    title_candidates = parent.find_elements(By.CSS_SELECTOR, "span[class*='title'], div[class*='title'], span[aria-label], div[aria-label]")
                                    for candidate in title_candidates:
                                        text = candidate.text.strip()
                                        if text and len(text) > 3 and text != link_text and text.lower() not in ['view job', 'apply', 'save']:
                                            title = text
                                            break
                                except:
                                    pass
                    except Exception as e:
                        pass
                
                # Method 4: Try to find title by looking at aria-label
                if not title:
                    try:
                        aria_label = link_elem.get_attribute('aria-label')
                        if aria_label and len(aria_label) > 3:
                            title = aria_label
                    except:
                        pass
                    
                    # Also try aria-label from parent
                    if not title:
                        try:
                            parent = link_elem.find_element(By.XPATH, "./ancestor::div[contains(@class, 'job') or contains(@class, 'card')][1]")
                            aria_elements = parent.find_elements(By.CSS_SELECTOR, "[aria-label]")
                            for elem in aria_elements:
                                aria_text = elem.get_attribute('aria-label')
                                if aria_text and len(aria_text) > 3 and 'job' in aria_text.lower():
                                    title = aria_text
                                    break
                        except:
                            pass
                
                # Method 5: Try to get from the first substantial text line in parent
                if not title:
                    try:
                        parent = link_elem.find_element(By.XPATH, "./ancestor::div[contains(@class, 'job') or contains(@class, 'card') or contains(@class, 'result')][1]")
                        all_text = parent.text
                        if all_text:
                            lines = [line.strip() for line in all_text.split('\n') if line.strip() and len(line.strip()) > 3]
                            # Filter out common non-title text
                            skip_words = ['view job', 'apply', 'save', 'company', 'location', 'ago', 'minute', 'hour']
                            for line in lines:
                                line_lower = line.lower()
                                if not any(skip in line_lower for skip in skip_words):
                                    title = line
                                    break
                    except:
                        pass
                
                # Method 6: Try to extract from data attributes or other attributes
                if not title:
                    try:
                        parent = link_elem.find_element(By.XPATH, "./ancestor::div[contains(@class, 'job') or contains(@class, 'card')][1]")
                        # Try data attributes
                        data_title = parent.get_attribute('data-job-title')
                        if data_title:
                            title = data_title
                    except:
                        pass
                
                
                # Try to get company from page elements if not found in URL
                if not company:
                    try:
                        parent = link_elem.find_element(By.XPATH, "./ancestor::div[contains(@class, 'job') or contains(@class, 'card') or contains(@class, 'result') or contains(@class, 'base-card')][1]")
                        company_selectors = [
                            "h4.base-search-card__subtitle",
                            "h4.job-search-card__subtitle",
                            "a.job-search-card__subtitle-link",
                            "h4[class*='subtitle']",
                            "span[class*='company']",
                            "div[class*='company']"
                        ]
                        for selector in company_selectors:
                            try:
                                company_elem = parent.find_element(By.CSS_SELECTOR, selector)
                                company_text = company_elem.text.strip()
                                if company_text and len(company_text) > 1:
                                    company = company_text
                                    break
                            except:
                                continue
                    except:
                        pass
                
                # If we still don't have a title, use a placeholder
                if not title:
                    title = "Job Listing (Title not found)"
                
                # If we still don't have a company, use a placeholder
                if not company:
                    company = "Company not found"
                
                jobs.append({
                    'title': title,
                    'company': company,
                    'link': href
                })
                
            except Exception as e:
                print(f"  Error processing link: {e}")
                continue
        
        # Secondary approach: Also try container-based extraction to catch any we missed
        print("\nTrying container-based extraction as backup...")
        job_selectors = [
            "li.jobs-search-results__list-item",
            "div.job-search-card",
            "div.base-card",
            "div[data-job-id]",
            "div.job-result-card"
        ]
        
        for selector in job_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"  Found {len(elements)} elements with selector: {selector}")
                    for element in elements:
                        try:
                            # Try to find link in this element
                            link_elem = element.find_element(By.CSS_SELECTOR, "a[href*='/jobs/view/']")
                            href = link_elem.get_attribute('href')
                            if href:
                                clean_href = href.split('?')[0] if '?' in href else href
                                # Check if we already have this job
                                if clean_href not in [j['link'].split('?')[0] if '?' in j['link'] else j['link'] for j in jobs]:
                                    # Try to get title with improved selectors
                                    title = None
                                    title_selectors = [
                                        "h3.base-search-card__title",
                                        "h3.job-search-card__title",
                                        "h3.job-result-card__title",
                                        "h2.job-result-card__title",
                                        "a.job-search-card__title-link",
                                        "h3[class*='title']",
                                        "h2[class*='title']",
                                        "h3",
                                        "h2"
                                    ]
                                    for title_sel in title_selectors:
                                        try:
                                            title_elem = element.find_element(By.CSS_SELECTOR, title_sel)
                                            title = title_elem.text.strip()
                                            if title and len(title) > 3:
                                                break
                                        except:
                                            continue
                                    
                                    # If still no title, try getting first substantial line of text
                                    if not title:
                                        try:
                                            all_text = element.text
                                            if all_text:
                                                lines = [line.strip() for line in all_text.split('\n') if line.strip() and len(line.strip()) > 3]
                                                skip_words = ['view job', 'apply', 'save', 'company', 'location', 'ago', 'minute', 'hour']
                                                for line in lines:
                                                    line_lower = line.lower()
                                                    if not any(skip in line_lower for skip in skip_words):
                                                        title = line
                                                        break
                                        except:
                                            pass
                                    
                                    if not title:
                                        title = "Job Listing (Title not found)"
                                    
                                    # Try to get company
                                    company = None
                                    company_selectors = [
                                        "h4.base-search-card__subtitle",
                                        "h4.job-search-card__subtitle",
                                        "a.job-search-card__subtitle-link"
                                    ]
                                    for company_sel in company_selectors:
                                        try:
                                            company_elem = element.find_element(By.CSS_SELECTOR, company_sel)
                                            company = company_elem.text.strip()
                                            if company:
                                                break
                                        except:
                                            continue
                                    
                                    if not company:
                                        company = "Company not found"
                                    
                                    jobs.append({
                                        'title': title,
                                        'company': company,
                                        'link': href
                                    })
                        except:
                            continue
            except:
                continue
        
        # Remove duplicates based on link
        seen_links = set()
        unique_jobs = []
        for job in jobs:
            if job['link'] not in seen_links:
                seen_links.add(job['link'])
                unique_jobs.append(job)
        
        jobs = unique_jobs
        print(f"\nSuccessfully scraped {len(jobs)} unique job postings!")
        
    except Exception as e:
        print(f"Error scraping jobs: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
    
    return jobs


def main():
    """Main function."""
    # Default URL - can be changed via command line or environment variable
    import sys
    import os
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = os.getenv('LINKEDIN_URL', 
            'https://www.linkedin.com/jobs/search/?keywords=software%20engineer%20intern&f_TPR=r8600&f_E=1')
    
    print("=" * 60)
    print("LinkedIn Job Scraper")
    print("=" * 60)
    print(f"URL: {url}\n")
    
    jobs = scrape_linkedin_jobs(url)
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if jobs:
        for i, job in enumerate(jobs, 1):
            print(f"\n{i}. {job['title']}")
            if 'company' in job:
                print(f"   Company: {job['company']}")
            print(f"   Link: {job['link']}")
    else:
        print("\nNo jobs found. This could be because:")
        print("1. LinkedIn requires login")
        print("2. The page structure has changed")
        print("3. No jobs match the search criteria")
        print("\nTry running with a visible browser (headless mode disabled) to debug.")
    
    print("\n" + "=" * 60)
    
    return jobs


if __name__ == "__main__":
    main()



