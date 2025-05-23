from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import uuid
import tempfile
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_chrome_driver():
    """Create a Chrome driver with robust containerized environment options"""
    chrome_options = Options()
    
    # Core headless and security options
    chrome_options.add_argument("--headless=new")  # Use new headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # User data directory with unique path
    temp_dir = tempfile.mkdtemp()
    user_data_dir = os.path.join(temp_dir, f"chrome_user_data_{uuid.uuid4().hex[:8]}")
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    
    # Comprehensive stability options for containers
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-javascript")  # Remove this if you need JS
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--silent")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--start-maximized")
    
    # Memory optimizations
    chrome_options.add_argument("--memory-pressure-off")
    chrome_options.add_argument("--max_old_space_size=4096")
    chrome_options.add_argument("--single-process")  # Use single process mode
    
    # Additional crash prevention
    chrome_options.add_argument("--disable-crash-reporter")
    chrome_options.add_argument("--disable-in-process-stack-traces")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    # Set up service with explicit path
    service = Service("/usr/local/bin/chromedriver")
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Chrome driver created successfully")
        return driver, temp_dir
    except Exception as e:
        logger.error(f"Failed to create Chrome driver: {e}")
        # Cleanup temp dir if driver creation fails
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass
        raise

def book_slot(name, email, guests, note, month, day, time_str):
    driver = None
    temp_dir = None
    
    try:
        logger.info(f"Starting booking process for {name} on {month} {day} at {time_str}")
        driver, temp_dir = create_chrome_driver()
        wait = WebDriverWait(driver, 15)  # Increased timeout
        
        # Navigate to the page with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to load Calendly page (attempt {attempt + 1})")
                driver.get("https://calendly.com/johngvm20/30min")
                # Wait for page to load
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                logger.info("Page loaded successfully")
                break
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to load page after {max_retries} attempts")
                time.sleep(2)

        # Close cookie popup with better error handling
        try:
            logger.info("Looking for cookie popup")
            close_cookie_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "onetrust-close-btn-handler")))
            close_cookie_btn.click()
            logger.info("Cookie popup closed")
        except TimeoutException:
            logger.info("No cookie popup found or already closed")
        except Exception as e:
            logger.warning(f"Error handling cookie popup: {e}")

        # Navigate to target month with better error handling
        logger.info(f"Navigating to month: {month}")
        month_attempts = 0
        max_month_attempts = 12  # Prevent infinite loops
        
        while month_attempts < max_month_attempts:
            try:
                current_month_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="title"]')))
                current_month = current_month_el.text.strip()
                logger.info(f"Current month: {current_month}")
                
                if current_month == month:
                    logger.info("Found target month")
                    break
                    
                next_btn = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Go to next month"]')
                driver.execute_script("arguments[0].click();", next_btn)  # Use JS click for reliability
                time.sleep(2)  # Increased wait time
                month_attempts += 1
                
            except Exception as e:
                logger.error(f"Error navigating months: {e}")
                break
        
        if month_attempts >= max_month_attempts:
            raise Exception(f"Could not find month '{month}' after {max_month_attempts} attempts")

        # Click target day with better error handling
        logger.info(f"Looking for day: {day}")
        day_found = False
        try:
            buttons = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table[aria-label='Select a Day'] button")))
            logger.info(f"Found {len(buttons)} day buttons")
            
            for i, btn in enumerate(buttons):
                try:
                    span_element = btn.find_element(By.TAG_NAME, "span")
                    button_text = span_element.text.strip()
                    logger.info(f"Button {i}: '{button_text}'")
                    
                    if button_text == day:
                        logger.info(f"Found target day button: {day}")
                        # Use JavaScript click for better reliability
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", btn)
                        day_found = True
                        logger.info("Day clicked successfully")
                        break
                except Exception as e:
                    logger.warning(f"Error checking button {i}: {e}")
                    continue
                    
            if not day_found:
                raise Exception(f"Could not find day '{day}' in calendar")
                
        except Exception as e:
            logger.error(f"Error finding day buttons: {e}")
            raise

        # Wait for time slots to load
        logger.info("Waiting for time slots to load")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-component="spotpicker-times-list"]')))
        time.sleep(2)  # Give extra time for dynamic content

        # Scroll and click time with enhanced error handling
        logger.info(f"Looking for time slot: {time_str}")
        def scroll_and_click_time():
            try:
                scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[data-component="spot-list"]')
                logger.info("Found scrollable time list")
                
                for scroll_attempt in range(25):  # Increased attempts
                    buttons = scrollable_div.find_elements(By.CSS_SELECTOR, 'button[data-container="time-button"]')
                    logger.info(f"Scroll attempt {scroll_attempt + 1}: Found {len(buttons)} time buttons")
                    
                    for btn_idx, btn in enumerate(buttons):
                        try:
                            time_element = btn.find_element(By.CSS_SELECTOR, 'div.vXODG3JdP3dNSMN_2yKi')
                            txt = time_element.text.strip().lower()
                            logger.info(f"Time button {btn_idx}: '{txt}'")
                            
                            if txt == time_str.lower():
                                logger.info(f"Found matching time slot: {txt}")
                                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                                time.sleep(1)
                                driver.execute_script("arguments[0].click();", btn)
                                logger.info("Time slot clicked successfully")
                                return True
                        except Exception as e:
                            logger.warning(f"Error checking time button {btn_idx}: {e}")
                            continue
                    
                    # Scroll down for more time slots
                    driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", scrollable_div)
                    time.sleep(1)  # Increased wait time
                    
                logger.warning("Exhausted all scroll attempts")
                return False
                
            except Exception as e:
                logger.error(f"Error in scroll_and_click_time: {e}")
                return False

        if not scroll_and_click_time():
            raise Exception(f"Time slot '{time_str}' not found after extensive search")

        # Click Next with better error handling
        logger.info("Looking for Next button")
        try:
            next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label^="Next"]')))
            driver.execute_script("arguments[0].click();", next_btn)
            logger.info("Next button clicked")
        except Exception as e:
            logger.error(f"Error clicking Next button: {e}")
            raise

        # Fill form with enhanced error handling
        logger.info("Filling out booking form")
        try:
            name_input = wait.until(EC.presence_of_element_located((By.ID, "full_name_input")))
            name_input.clear()
            name_input.send_keys(name)
            logger.info("Name entered")
            
            email_input = driver.find_element(By.ID, "email_input")
            email_input.clear()
            email_input.send_keys(email)
            logger.info("Email entered")
        except Exception as e:
            logger.error(f"Error filling basic form fields: {e}")
            raise

        # Add guests with better error handling
        if guests:
            logger.info(f"Adding {len(guests)} guests")
            try:
                add_guests_btn = driver.find_element(By.XPATH, '//button[span[text()="Add Guests"]]')
                driver.execute_script("arguments[0].click();", add_guests_btn)
                
                guest_input = wait.until(EC.presence_of_element_located((By.ID, "invitee_guest_input")))
                for i, guest in enumerate(guests):
                    logger.info(f"Adding guest {i + 1}: {guest}")
                    guest_input.send_keys(guest)
                    guest_input.send_keys(Keys.ENTER)
                    time.sleep(1)
                logger.info("All guests added")
            except Exception as e:
                logger.warning(f"Error adding guests: {e}")

        # Add note with better error handling  
        if note:
            logger.info("Adding note")
            try:
                textarea = driver.find_element(By.CSS_SELECTOR, 'textarea[name="question_0"]')
                textarea.clear()
                textarea.send_keys(note)
                logger.info("Note added")
            except Exception as e:
                logger.warning(f"Error adding note: {e}")

        # Submit with better error handling
        logger.info("Submitting form")
        try:
            submit_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            driver.execute_script("arguments[0].click();", submit_btn)
            logger.info("Form submitted successfully")
            
            # Wait a bit to see if submission was successful
            time.sleep(3)
            
        except Exception as e:
            logger.error(f"Error submitting form: {e}")
            raise

    except Exception as e:
        logger.error(f"Booking process failed: {e}")
        # Take a screenshot for debugging if possible
        try:
            if driver:
                screenshot_path = f"/tmp/error_screenshot_{uuid.uuid4().hex[:8]}.png"
                driver.save_screenshot(screenshot_path)
                logger.info(f"Error screenshot saved to {screenshot_path}")
        except:
            pass
        raise
        
    finally:
        # Cleanup
        if driver:
            try:
                driver.quit()
                logger.info("Chrome driver closed")
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
        
        # Cleanup temporary directory
        if temp_dir:
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info("Temporary directory cleaned up")
            except Exception as e:
                logger.warning(f"Error cleaning up temp directory: {e}")