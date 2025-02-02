import time
import schedule
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options

# Make selenium run in headless mode
options = Options()
options.add_argument("--headless")

# Telegram bot details
TOKEN = "7621055077:AAFlTucHTKpowBHF-MnqKoXBlTE_PAT1YIs"
CHAT_ID = "7570431772"

tasks = {}
old_tasks = {}
delete = {}

def get_new_tasks():
    # Create Edge driver
    driver = webdriver.Edge(options=options)
    time.sleep(2)
    
    # Go to Uplearn
    driver.get("https://web.uplearn.co.uk/login")
    time.sleep(2)
    
    # Wait until element exists
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "input-1"))
    )
    
    # Enter username and password
    input_username = driver.find_element(By.ID, "input-1")
    input_username.clear()
    input_username.send_keys("b.hassanhussain@astreasheffield.org")
    time.sleep(2)
    
    input_password = driver.find_element(By.ID, "input-2")
    input_password.clear()
    input_password.send_keys("tempPassword1!" + Keys.ENTER)
    time.sleep(2)
    
    # Go to assignments
    href_value = "/assignments"
    assignments_button = driver.find_element(By.XPATH, f"//a[@href='{href_value}']")
    assignments_button.click()
    time.sleep(2)
    
    # Locate all assignment elements
    
    # Find all <a> elements that match the given criteria
    a_elements = driver.find_elements(By.XPATH, "//div[@id='react-content']/div//a")
    
    # Loop through each <a> element
    for a in a_elements:
        # Extract the nested <p> elements inside each <a>
        p_elements = a.find_elements(By.TAG_NAME, "p")
    
        x = {p_elements[0].text: p_elements[1].text}
        tasks.update(x)    
    driver.quit()
    
def process_tasks():    
    # Get tasks from file
    with open("uplearn_assignments.json", "r") as f:
        data = json.load(f)
        for key, value in data.items():
            x = {key:value}
            old_tasks.update(x)

    # Loop through new tasks and compare with old tasks
    for key,value in tasks.items():
        if key in old_tasks:
            pass
        else:
            print(key, "added to old tasks\n")
            x = {key:value}
            old_tasks.update(x)
            message = "NEW UPLEARN TASK: " + key + ": " + value   # SEND TELEGRAM AN UPDATE
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
            requests.get(url)

    # Loop through old tasks and compare with new tasks
    for key,value in old_tasks.items():
        if key in tasks:
            pass
        else:
            print(key, "deleted from old tasks\n")
            x = {key:value}
            delete.update(x)
            message = "UPLEARN TASK REMOVED: " + key + ": " + value    # SEND TELEGRAM AN UPDATE
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
            requests.get(url)

    # Remove deleted tasks from old tasks
    for key, value in delete.items():
        del old_tasks[key]

    # Empty json file and upload all tasks in old tasks
    with open("uplearn_assignments.json", "w") as f:
        f.truncate()
        json.dump(old_tasks, f)


get_new_tasks()
process_tasks()


schedule.every().day.at("18:00").do(get_new_tasks)
schedule.every().day.at("18:00").do(process_tasks)

while True:
    schedule.run_pending()
    time.sleep(1)
