import time
import json
import re
import sys
import http.client
import traceback
import math
import xml.etree.ElementTree as ElementTree
from urllib.parse import urlparse, unquote


class MySchedule:
  """
  A class for interacting with the MySchedule API.
  """
  DOMAIN = "myschedule.erp.sfu.ca"

  def __init__(self, cookie):
    self.__cookie = cookie
    self.__http_client = http.client.HTTPSConnection(MySchedule.DOMAIN, timeout=30)
    self.__http_headers = {
      "Cookie": cookie,
    }

  def __request(self, path, method="GET", body=None, override_content_type=None, allow_html=False):
    """
    Peforms an HTTP request on the MySchedule website.
    The response will be returned as a parsed JSON or XML object if possible.
    """
    # Make the HTTP request.
    self.__http_client.request(method, path, body=body, headers=self.__http_headers)
    response = self.__http_client.getresponse()
    response_headers = {k.lower(): v for (k,v) in response.getheaders()}
    response_text = response.read().decode('utf-8')

    if response.status != 200:
      raise Exception(f"Request failed: {response.status} - {response.reason}")

    if allow_html is False and response_headers.get('content-type', "") == "text/html;charset=UTF-8":
      raise Exception(f"Request returned a web page. Your auth token is probably invalid.")

    # Determine the response content type.
    content_type = response_headers.get('content-type', None)
    if override_content_type is not None:
      content_type = override_content_type

    # Parse the response content type and return it.
    if content_type == 'application/json':
      return json.loads(response_text)

    if content_type == 'text/xml;charset=UTF-8':
      return ElementTree.fromstring(response_text)

    return response_text

  def __calculate_nwindow(self):
    """
    Calculate the `e` and `t` parameters used for verification.
    This is ported from the following JavaScript code ripped off of the site:

    ```
      function nWindow() {
      	var f8b0=["\x26\x74\x3D","\x26\x65\x3D"] // ["&t=", "&e="]
      	var t=(Math.floor((new Date())/60000))%1000;
	      var e=t%3+t%39+t%42;
	      return f8b0[0]+t+f8b0[1]+e;
      }
    """
    now = math.floor(time.time() * 1000)
    t = math.floor(now/60000)%1000
    e = (t%3)+(t%39)+(t%42)
    return f"&t={t}&e={e}"

  def __parse_api_classdata_course(self, el):
    """
    Parses MySchedule's course XML tag.
    """
    info = {
      "key": el.attrib["key"],
      "class_code": el.attrib["code"],
      "class_num": el.attrib["number"],
    }

    for el2 in el:
      if el2.tag == 'offering':
        info['title'] = el2.attrib['title']
        info['desc']  = el2.attrib['desc']

    return info

  def query_term_list(self):
    """
    Returns a list of term information.
    Data will be a list of dicts with `{id, name}`.
    """
    data = self.__request("/api/getAcademicPlans")
    return [{"id": item['termCode'], "name": item['termDescription']} for item in data]

  def query_class_data(self, term, classes):
    """
    Returns info for a class.
    Data will be a dict of classes in the format of:

    """
    # Fetch the class info.
    course_params = [f"course_{i}_0={code}" for (i, code) in enumerate(classes)]
    course_params_str = '&'.join(course_params)
    term_id = term['id']
    nwindow = self.__calculate_nwindow()
    data = self.__request(f"/getclassdata.jsp?term={term_id}&{course_params_str}{nwindow}")

    # Parse the response.
    classes = {}
    for el in data:
      if el.tag == "classdata":
        for el2 in el:
          if el2.tag == "course":
            class_info = self.__parse_api_classdata_course(el2)
            classes[class_info['key']] = class_info

    return classes


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


def search_all_courses_in_term(api, term, log):
  course_file = open("./courses-base.json", "r")
  data = json.load(course_file)
  course_file.close()
  courses = []
  for course in data["COURSES"]:
    log(f"Searchng {course['CODE']} in term {term['name']}...")

    course_key = re.sub(r'^([A-Z]+)(\d+)$', r'\1-\2', course['CODE'])
    response_all = api.query_class_data(term, [course_key])

    # Check if the course is offered in the selected term
    if course_key in response_all:
      response = response_all[course_key]
      prereq = extract_prereq(response['desc'])
      course_data = {
        "CODE": course["CODE"],
        "PREREQ": prereq
      }
      courses.append(course_data)
    else:
      prereq = []

  return courses


def __mining_log(msg):
  print(f"[log] {msg}")

def __mining_do(cookie, log=__mining_log):
  api = MySchedule(cookie)

  log("Fetching term IDs...")
  terms = api.query_term_list()

  courses = []
  for term in terms:
    courses += search_all_courses_in_term(api, term, log)

  json_obj = {
    "COURSES": courses
  }
  output_file = open("./courses.json", "w")
  json.dump(json_obj, output_file, sort_keys=True, indent=4)


def __read_headers_and_get_cookie():
  """
  Read the user's session cookie from the pasted headers.
  This will eat the rest of the input until a blank line is sent.
  """
  cookie = None
  while True:
    line = input().strip()

    if cookie is None and line.startswith('Cookie: '):
      cookie = line[8:]

    if line == "":
      break

  if cookie is None:
    raise Exception("Coult not find Cookie.")

  return cookie


def mining():
  """
  Main function for the get-courses script.
  Uses the MySchedule API to query all the class codes and save them as JSON.
  """
  print("In order to use the MySchedule API, you need to be logged in to myschedule.sfu.ca")
  print("To do this, go to go.sfu.ca and click on 'My Schedule' under the 'Academics' panel.")
  print("")
  print("Once you are on the welcome screen, open the browser developer tools and look for 'criteria.jsp' under the Network tab. Copy the Request Headers.")
  print("  Chrome: Right Click on 'criteria.jsp' => Copy => Copy request headers")
  print("")
  print("Paste the headers below:")
  print("\x1B[36m")
  auth = __read_headers_and_get_cookie()
  print("\x1B[0m")

  # Start scraping the course data.
  print("Starting to scrape data...")
  print("")
  start_time = time.time()
  __mining_do(auth)
  end_time = time.time()


if __name__ == "__main__":
  if sys.version_info < (3, 6):
    print("Requires Python 3.6.")
    print("Try using the python3 command if it's installed.")
    sys.exit(1)

  try:
    mining()  
  except Exception as ex:
    print("")
    print("\x1B[31mSomething went wrong.\x1B[0m")
    print(f"\x1B[31mMessage:\x1B[0m {str(ex)}")
    print("")
    print(traceback.format_exc())

