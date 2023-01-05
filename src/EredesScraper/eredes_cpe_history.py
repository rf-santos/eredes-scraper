
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By





def login_private_user(driver, user, password):
    # Select Private User login
    wait(driver, 10).until(EC.element_to_be_clickable((By.XPATH,
                                                       "/html/body/app-root/nz-layout/app-default/main/nz-content/div"
                                                       "/div[2]/section[1]/div[2]/div/div/ul/li[1]/div[2]"))).click()

    # User and Password elements defined by XPATH
    uname = driver.find_element(By.XPATH,
                                "/html/body/app-root/nz-layout/app-default/main/nz-content/div/div[2]/section["
                                "1]/app-sign-in/div/div/form/nz-form-item[1]/nz-form-control/div/div/div/input")
    passwd = driver.find_element(By.XPATH,
                                 "/html/body/app-root/nz-layout/app-default/main/nz-content/div/div[2]/section["
                                 "1]/app-sign-in/div/div/form/nz-form-item["
                                 "2]/nz-form-control/div/div/div/nz-input-group/input")

    # Send login credentials
    uname.send_keys(user)
    passwd.send_keys(password)

    wait(driver, 10)

    # Click Login button
    driver.find_element(By.XPATH,
                        "/html/body/app-root/nz-layout/app-default/main/nz-content/div/div[2]/section["
                        "1]/app-sign-in/div/div/form/div[2]/div/button/span").click()

    wait(driver, 10).until(
        lambda x: x.execute_script("return document.readyState === 'complete'")
    )
    # Verify that the login was successful.
    error_message = "Incorrect username or password."
    # Retrieve any errors found.
    errors = driver.find_elements(By.CLASS_NAME, "flash-error")

    # When errors are found, the login will fail.
    if any(error_message in e.text for e in errors):
        print("[!] Login failed")
    else:
        print("[+] Login successful")


login_private_user(driver, globals()['EREDES_USER'], globals()['EREDES_PASSWORD'])
