# SFU-CMPT-Prereq-Tree
This Python automation tool uses to draw all computing science pre-requsite courses in Simon Fraser University in a form of tree.
### Prerequisites
This tool is developed under the following environment
```
google-chrome --version
>> Google Chrome 85.0.4183.102
python --version
>> Python 2.7.18rc1
```
If your chrome version is different from above, please download and replace the chromedriver accordingly.
https://sites.google.com/a/chromium.org/chromedriver/home
### Installing dependencies and required libraries (Debian/Ubuntu)
```
sudo ./setup.sh
```
### Running
To get all available courses and each pre-requsite courses available on myschedule.sfu.ca (in a selected term),
```
python get-courses.py
```
it will create a json file which is required in order to run the next step.
To get produced tree vector image,
```
python main.py
```
the created image will be available in result/.
