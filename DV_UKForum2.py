import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException

# 1. Configure Chrome Options (you can remove headless mode to see the browser)
chrome_options = Options()
chrome_options.add_argument("--headless")

# 2. Set up ChromeDriver using webdriver_manager
service = ChromeService(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Base URL and output container
base_url = "https://survivorsforum.womensaid.org.uk/topics/"
forum_data = []

try:
    # Create a wait object for explicit waits
    wait = WebDriverWait(driver, 15)
    
    # Manually iterate through pages 1 to 5
    for page_number in range(1, 20):
        # Construct the URL: for page 1 use base_url, otherwise add /page/<number>/.
        if page_number == 1:
            url = base_url
        else:
            url = f"{base_url}page/{page_number}/"
            
        print(f"\n=== SCRAPING PAGE {page_number} ===\nURL: {url}\n")
        driver.get(url)
        
        # Wait for the forum topics container to load
        wait.until(EC.presence_of_element_located((By.ID, "bbpress-forums")))
        time.sleep(1)  # Small additional delay to help with dynamic content
        
        # Find all the topic elements on the current page
        topics_selector = "ul[id^='bbp-topic-'].topic.type-topic"
        topics = driver.find_elements(By.CSS_SELECTOR, topics_selector)
        print(f"Found {len(topics)} topic(s) on page {page_number}.")
        
        # Loop through each topic on the page
        for topic in topics:
            try:
                # Locate the topic title element and its link
                title_li = topic.find_element(By.CSS_SELECTOR, "li.bbp-topic-title")
                title_link = title_li.find_element(By.TAG_NAME, "a")
                title_text = title_link.text.strip()
                
                print("--------------------------------------------------")
                print(f"Processing topic: {title_text}")
                
                # Scroll the element into view and click
                driver.execute_script("arguments[0].scrollIntoView(true);", title_link)
                try:
                    title_link.click()
                except Exception as e:
                    print(f"Normal click failed for '{title_text}' ({e}), using JS click.")
                    driver.execute_script("arguments[0].click();", title_link)
                
                # Wait for the topic page to load replies
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.bbp-reply-content")))
                time.sleep(1)  # Optional delay to ensure dynamic content loads
                
                # Extract reply elements and filter out empty ones
                reply_elements = driver.find_elements(By.CSS_SELECTOR, "div.bbp-reply-content")
                reply_texts = [elem.text.strip() for elem in reply_elements if elem.text.strip()]
                
                if not reply_texts:
                    print(f"No reply text found for '{title_text}', skipping this topic.")
                    driver.back()
                    wait.until(EC.presence_of_element_located((By.ID, "bbpress-forums")))
                    continue
                
                # Use the first non-empty reply as the main content and the rest as comments
                content_text = reply_texts[0]
                comments_text = reply_texts[1:]
                
                print(f"Title: {title_text}")
                print("Content:")
                print(content_text)
                print("Comments:")
                for c in comments_text:
                    print(c)
                print("--------------------------------------------------\n")
                
                # Save the topic data
                forum_data.append({
                    "title": title_text,
                    "content": content_text,
                    "comments": comments_text
                })
                
            except Exception as e:
                print(f"Error processing topic '{title_text if 'title_text' in locals() else 'unknown'}': {e}")
            finally:
                # Navigate back to the current page listing topics
                driver.back()
                wait.until(EC.presence_of_element_located((By.ID, "bbpress-forums")))
                time.sleep(1)
finally:
    driver.quit()

# Save the scraped data to a JSON file.
output_filename = "forum_data5.json"
with open(output_filename, "w", encoding="utf-8") as outfile:
    json.dump(forum_data, outfile, ensure_ascii=False, indent=2)

print(f"Saved scraped data to {output_filename}.")
