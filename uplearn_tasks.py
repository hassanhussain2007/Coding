import requests
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
from pathlib import Path
import time


# ------------------------------
# CONFIG
# ------------------------------
accounts = {
    "maths_physics_chemistry_uplearn": {
        "username": "b.hassanhussain@astreasheffield.org",
        "password": "tempPassword1!",
        "assignments_file": Path("assignments_maths_phy_chem.json"),
        "ntfy_url": "https://ntfy.sh/maths_physics_chemistry_uplearn"
    },
    "biology_chemistry_psychology":{
        "username": "b.azaanparwez@astreasheffield.org",
        "password": "AzaanP4rwez",
        "assignments_file": Path("assignments_chem_bio_psyc"),
        "ntfy_url": "https://ntfy.sh/biology_chemistry_psychology_uplearn"
    }
}


def get_assignments(username, password, EDGE_DRIVER_PATH, URL, ASSIGNMENTS_FILE, ntfy_url):
    # ------------------------------
    # SETUP EDGE
    # ------------------------------
    options = Options()

    # Run Edge in headless mode (no visible browser)
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")


    service = Service(EDGE_DRIVER_PATH)
    driver = webdriver.Edge(service=service, options=options)
    wait = WebDriverWait(driver, 30)


    # ------------------------------
    # STEP 1: OPEN LOGIN PAGE
    # ------------------------------
    print("Opening Uplearn login page...")
    driver.get(URL)

    # Wait for the page body to load first
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except TimeoutException:
        print("Warning: Page body didn't fully load, continuing anyway...")

    # Give a short fixed delay to allow scripts to render dynamic content
    time.sleep(2)

    # Wait for assignments link to appear and be clickable
    try:
        assignments_link = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='/assignments']"))
        )
        print("Assignments link found. Clicking...")
        assignments_link.click()
    except TimeoutException:
        print("Error: Assignments link not found or page didn't load properly.")



    # ------------------------------
    # STEP 2: ENTER EMAIL
    # ------------------------------
    email_input = wait.until(
        EC.visibility_of_element_located((By.ID, "input-1"))
    )
    email_input.send_keys(username)


    # ------------------------------
    # STEP 3: CLICK NEXT
    # ------------------------------
    next_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Next']]"))
    )
    next_button.click()


    # ------------------------------
    # STEP 4: ENTER PASSWORD
    # ------------------------------
    password_input = wait.until(
        EC.visibility_of_element_located((By.ID, "input-2"))
    )
    password_input.send_keys(password)


    # ------------------------------
    # STEP 5: SIGN IN
    # ------------------------------
    sign_in_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Sign in']]"))
    )
    sign_in_button.click()

    print("Login successful.")


    # ------------------------------
    # STEP 6: GO TO ASSIGNMENTS
    # ------------------------------
    assignments_link = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//a[@href='/assignments']"))
    )
    assignments_link.click()


    # ------------------------------
    # STEP 7: FETCH ASSIGNMENTS
    # ------------------------------
# ------------------------------
# STEP 7: FETCH ASSIGNMENTS (SAFE)
# ------------------------------
    print("\nFetching assignments...\n")

    # Wait until either assignments exist OR the empty-state message appears
    wait.until(
        EC.any_of(
            EC.presence_of_element_located(
                (By.XPATH, "//a[starts-with(@data-testid, 'assignment-subsection-')]")
            ),
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), 'No assignments to complete')]")
            )
        )
    )

    # Now safely fetch assignments (returns [] if none exist)
    assignment_elements = driver.find_elements(
        By.XPATH,
        "//a[starts-with(@data-testid, 'assignment-subsection-')]"
    )

    current_assignments = []


    for i, a in enumerate(assignment_elements, start=1):
        assignment_id = a.get_attribute("data-testid")

        title = a.find_element(
            By.XPATH, ".//p[@weight='semiBold']"
        ).text.strip()

        due = a.find_element(
            By.XPATH, ".//p[contains(text(), 'Due')]"
        ).text.strip()

        current_assignments.append({
            "id": assignment_id,
            "title": title,
            "due": due
        })

    # ------------------------------
    # STEP 8: TOMORROW WARNING
    # ------------------------------

    for a in current_assignments:
        if "tomorrow" in a["due"].lower():
            requests.post(ntfy_url, data=(f"{a['title']} is due tomorrow").encode("utf-8"), timeout=5)


    # ------------------------------
    # STEP 9: LOAD SAVED ASSIGNMENTS
    # ------------------------------
    if ASSIGNMENTS_FILE.exists():
        try:
            with open(ASSIGNMENTS_FILE, "r") as f:
                saved_assignments = json.load(f)
                if not isinstance(saved_assignments, list):
                    saved_assignments = []
        except json.JSONDecodeError:
            saved_assignments = []
    else:
        saved_assignments = []


    # ------------------------------
    # STEP 10: COMPARE & SYNC
    # ------------------------------
    current_ids = {a["id"] for a in current_assignments}
    saved_ids = {a["id"] for a in saved_assignments}

    new_assignments = [
        a for a in current_assignments if a["id"] not in saved_ids
    ]

    removed_assignments = [
        a for a in saved_assignments if a["id"] not in current_ids
    ]

    if new_assignments:
        for a in new_assignments:
            requests.post(ntfy_url, data=(f"ASSIGNMENT ADDED:  {a['title']} ({a['due']})"), timeout=5)

    if removed_assignments:
        for a in removed_assignments:
            requests.post(ntfy_url, data=(f"ASSIGNMENT REMOVED:   {a['title']} ({a['due']})"), timeout=5)


    # ------------------------------
    # STEP 11: WRITE JSON (SYNC STATE)
    # ------------------------------
    with open(ASSIGNMENTS_FILE, "w") as f:
        json.dump(current_assignments, f, indent=2)

    print("\nAssignments file synced.")


    # ------------------------------
    # DONE
    # ------------------------------
    driver.quit()


for key, value in accounts.items():
    EDGE_DRIVER_PATH = r"C:\Users\hassa\Downloads\edgedriver_win64\msedgedriver.exe"
    url = "https://web.uplearn.co.uk/login"
    get_assignments(value["username"], value["password"], EDGE_DRIVER_PATH, url,value["assignments_file"], value["ntfy_url"])
