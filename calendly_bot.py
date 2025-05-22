from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import chromedriver_autoinstaller
from selenium.webdriver.chrome.options import Options
import time

def book_slot(name, email, guests, note, month, day, time_str):
    chromedriver_autoinstaller.install()

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)
    driver.get("https://calendly.com/johngvm20/30min")

    try:
        try:
            close_cookie_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "onetrust-close-btn-handler")))
            close_cookie_btn.click()
        except:
            pass

        # Navigate to desired month
        while True:
            current_month_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="title"]')))
            if current_month_el.text.strip() == month:
                break
            driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Go to next month"]').click()
            time.sleep(1)

        # Click day
        buttons = driver.find_elements(By.CSS_SELECTOR, "table[aria-label='Select a Day'] button")
        for btn in buttons:
            try:
                if btn.find_element(By.TAG_NAME, "span").text.strip() == day:
                    ActionChains(driver).move_to_element(btn).click(btn).perform()
                    break
            except:
                continue

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-component="spotpicker-times-list"]')))
        time.sleep(1)

        def scroll_and_click_time():
            scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[data-component="spot-list"]')
            for _ in range(20):
                buttons = scrollable_div.find_elements(By.CSS_SELECTOR, 'button[data-container="time-button"]')
                for btn in buttons:
                    try:
                        txt = btn.find_element(By.CSS_SELECTOR, 'div.vXODG3JdP3dNSMN_2yKi').text.strip().lower()
                        if txt == time_str.lower():
                            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                            wait.until(EC.element_to_be_clickable(btn))
                            btn.click()
                            return True
                    except:
                        continue
                driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", scrollable_div)
                time.sleep(0.5)
            return False

        if not scroll_and_click_time():
            raise Exception("Time slot not found")

        # Click Next
        next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label^="Next"]')))
        next_btn.click()

        # Fill form
        wait.until(EC.presence_of_element_located((By.ID, "full_name_input"))).send_keys(name)
        driver.find_element(By.ID, "email_input").send_keys(email)

        # Add guests
        if guests:
            driver.find_element(By.XPATH, '//button[span[text()="Add Guests"]]').click()
            guest_input = wait.until(EC.presence_of_element_located((By.ID, "invitee_guest_input")))
            for g in guests:
                guest_input.send_keys(g + " ")
                time.sleep(0.5)

        # Add note
        try:
            textarea = driver.find_element(By.CSS_SELECTOR, 'textarea[name="question_0"]')
            textarea.send_keys(note)
        except:
            pass

        # Submit
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        print("Booking submitted.")

    finally:
        time.sleep(5)
        driver.quit()