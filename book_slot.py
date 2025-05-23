from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time

app = FastAPI()

class BookingRequest(BaseModel):
    name: str
    email: str
    guests: List[str]
    note: str
    month: str
    day: str
    time_str: str

def safe_quit(driver, msg):
    print(msg)
    driver.quit()
    raise Exception(msg)

def book_slot(name, email, guests, note, month, day, time_str):
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    driver.get("https://calendly.com/johngvm20/30min")

    try:
        try:
            wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "onetrust-close-btn-handler"))).click()
        except:
            pass

        while True:
            current = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="title"]'))).text.strip()
            if current == month:
                break
            next_btn = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Go to next month"]')
            if next_btn.get_attribute("disabled"):
                safe_quit(driver, f"Target month '{month}' not available.")
            next_btn.click()
            time.sleep(1)

        day_clicked = False
        buttons = driver.find_elements(By.CSS_SELECTOR, "table[aria-label='Select a Day'] button")
        for btn in buttons:
            try:
                if btn.find_element(By.TAG_NAME, "span").text.strip() == day:
                    if btn.get_attribute("disabled"):
                        safe_quit(driver, f"Day {day} is disabled.")
                    ActionChains(driver).move_to_element(btn).click(btn).perform()
                    day_clicked = True
                    break
            except:
                continue

        if not day_clicked:
            safe_quit(driver, f"Day {day} not found or clickable.")

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-component="spotpicker-times-list"]')))
        time.sleep(1)

        def scroll_and_click_time():
            scroll_div = driver.find_element(By.CSS_SELECTOR, 'div[data-component="spot-list"]')
            for _ in range(20):
                for btn in scroll_div.find_elements(By.CSS_SELECTOR, 'button[data-container="time-button"]'):
                    try:
                        txt = btn.find_element(By.CSS_SELECTOR, 'div.vXODG3JdP3dNSMN_2yKi').text.strip().lower()
                        if txt == time_str.lower():
                            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                            wait.until(EC.element_to_be_clickable(btn)).click()
                            return True
                    except:
                        continue
                driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", scroll_div)
                time.sleep(0.5)
            return False

        if not scroll_and_click_time():
            safe_quit(driver, f"Time '{time_str}' not found.")

        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label^="Next"]'))).click()

        wait.until(EC.presence_of_element_located((By.ID, "full_name_input"))).send_keys(name)
        driver.find_element(By.ID, "email_input").send_keys(email)

        if guests:
            try:
                wait.until(EC.element_to_be_clickable((By.XPATH, '//button[.//span[text()="Add Guests"]]'))).click()
                guest_input = wait.until(EC.presence_of_element_located((By.ID, "invitee_guest_input")))
                for g in guests:
                    guest_input.send_keys(g)
                    guest_input.send_keys(Keys.ENTER)
                    time.sleep(0.5)
            except:
                print("Could not add guests.")

        try:
            driver.find_element(By.CSS_SELECTOR, 'textarea[name="question_0"]').send_keys(note)
        except:
            print("Note input not found.")

        driver.find_element(By.XPATH, '//button[.//span[text()="Schedule Event"]]').click()
        print("Booking submitted.")
    finally:
        time.sleep(3)
        driver.quit()

@app.post("/book")
def book_endpoint(data: BookingRequest):
    try:
        book_slot(data.name, data.email, data.guests, data.note, data.month, data.day, data.time_str)
        return {"status": "success", "message": "Booking completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
