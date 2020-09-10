from selenium.webdriver import ChromeOptions
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import json
import re

SEARCH_BAR_ELEMENT_ID = "code_number"
TARGET_CLASS_NAME = "desc"
REMOVE_BUTTON_XPATH = "//*[@id=\"requirements\"]/div[3]/div[2]/div[1]/a"
WARNING_CLASS_NAME = "warningNoteBad note30"


def extract_prereq(desc):
  prereq = []
  prereq_desc_search = re.search("Prerequisite.+?(?=\.)", desc)
  # Check if the course has pre-requisite
  if prereq_desc_search is not None: 
    prereq_desc = prereq_desc_search.group()
  else:
    return prereq

  course_file = open("./courses-base.json", "r")
  data = json.load(course_file)
  course_file.close()
  for course in data["COURSES"]:
    course_code_split = re.split("(\d+)", course["CODE"])
    course_code = course_code_split[0] + " " + course_code_split[1]
    if course_code in prereq_desc:
      prereq.append(course["CODE"])

  return prereq


def search_all_courses(driver):
  course_file = open("./courses-base.json", "r")
  data = json.load(course_file)
  course_file.close()
  courses = []
  for course in data["COURSES"]:
    print("Searchng " + course["CODE"] + "...")
    search_bar = driver.find_element(By.ID, SEARCH_BAR_ELEMENT_ID)
    search_bar.send_keys(course["CODE"])
    time.sleep(1)
    search_bar.send_keys(Keys.ENTER)
    time.sleep(2)
    targets = driver.find_elements(By.CLASS_NAME, TARGET_CLASS_NAME)
    # Check if the course is offered in the selected term
    if len(driver.find_elements(By.XPATH, REMOVE_BUTTON_XPATH)) != 0:
      remove_button = driver.find_elements(By.XPATH, REMOVE_BUTTON_XPATH)
      remove_button[0].click()
      desc = targets[1].get_attribute("innerHTML")
      prereq = extract_prereq(desc)
      course_data = {
        "CODE": course["CODE"],
        "PREREQ": prereq
      }
      courses.append(course_data)
    else:
      prereq = []

  json_obj = {
    "COURSES": courses
  }
  output_file = open("./courses.json", "w")
  json.dump(json_obj, output_file, sort_keys=True, indent=4)


def mining():
  start_time = time.time()
  chrome_options = ChromeOptions()
  chrome_options.add_argument("--incognito")
  chrome_options.add_experimental_option("detach", True)
  browser = Chrome(executable_path="./chromedriver", options=chrome_options)
  browser.get("https://myschedule.sfu.ca/")

  # Wait for manual input
  print("Selected Term? (y/n)")
  cmd = raw_input()
  if cmd == "y" or cmd == "Y":
    search_all_courses(browser)
    elapsed_time = time.time() - start_time
    print("Search Completed in " + str(elapsed_time) + "s. Script ends.")
  else:
    print("Script ends.")
  browser.close()


if __name__ == "__main__":
  mining()
