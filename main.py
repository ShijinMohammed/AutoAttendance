from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException
from threading import Thread
from datetime import datetime, time

import os
import yaml
import time as t
import sys

conf = yaml.safe_load(open('Resources/loginDetail.yml'))
tt = yaml.safe_load(open('Resources/timeTable.yml'))

email = conf['moodle_user']['email']
password = conf['moodle_user']['password']

driver = webdriver.Chrome()

loggedIn = False
attendanceMarked = False

#Checks if a partial hyper link text exists in the page
def check_exists_by_partial_link_text(text):
    try:
        driver.find_element_by_partial_link_text(text)
    except NoSuchElementException:
        return False
    return True

#Checks if a n element with the given css selector exists in the page
def check_exists_by_css_selector(selector):
    try:
        driver.find_element_by_css_selector(selector)
    except NoSuchElementException:
        return False
    return True

#Checks if a text exists in the page
def check_exists_by_text(text):
    return (text in driver.page_source)

#Checks if an element with given id exists in the page
def check_exists_by_id(x):
    try:
        driver.find_element_by_id(x)
    except NoSuchElementException:
        return False
    return True

def login():
    #If login page gives error, reload after 5 seconds
    try:
        driver.get("http://moodle.mec.ac.in/login/index.php")
    except:
        t.sleep(5)
        login()
        return
    
    driver.find_element_by_id("username").send_keys(email)
    driver.find_element_by_id("password").send_keys(password)
    driver.find_element_by_id("loginbtn").click()



def markAttendance(url):
    #Checks for network errors, if found, Calls the function again recursively
    try:
        driver.get(url)
    except:
        t.sleep(5)
        markAttendance(url)
        return
    
    global attendanceMarked
    
    if not url == tt['mentoring']:
        attendanceMarked = True

    #Checks if submit link is available, if not, reloads every 60 seconds until found
    while not check_exists_by_partial_link_text("Submit attendance"):
        driver.get(url)
        t.sleep(60)
        
    driver.find_element_by_partial_link_text("Submit attendance").click()

    #Check if the radio button is available, if not, reload every 10 seconds, exits loop whenever radio button is found
    startTime = t.time()
    while not check_exists_by_css_selector("#fgroup_id_statusarray .form-check-input"):
        if((t.time() - startTime) > 10):
            startTime = t.time()
            driver.refresh() 
        continue
    
    driver.find_elements_by_css_selector("#fgroup_id_statusarray .form-check-input")[0].click()
    driver.find_element_by_name("submitbutton").click()

    #If failed to mark attendance, attempt again after 20 seconds
    startTime = t.time()
    while not check_exists_by_text("Your attendance in this session has been recorded"):
        if((t.time() - startTime) > 20):
            markAttendance(url)
            break
        continue
    
    if not url == tt['mentoring']:
        markAttendance(tt['mentoring'])


    
#checks if the given time is between the begin time and the end time
def is_time_between(begin_time, end_time, check_time=None):
    check_time = check_time or datetime.now().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: 
        return check_time >= begin_time or check_time <= end_time

#returns the period index for the current time if exists, else, -1
def getPeriod():
    if(datetime.today().weekday() < 4):
        if is_time_between(time(8,30),time(9,20)):
            return 1
        elif is_time_between(time(9,30),time(10,20)):
            return 2
        elif is_time_between(time(10,30),time(11,20)):
            return 3
        elif is_time_between(time(11,30),time(12,20)):
            return 4
        elif is_time_between(time(13,30),time(15,30)):
            return 5
        else:
            return -1
    else:
        if is_time_between(time(8,0),time(9,10)):
            return 1
        elif is_time_between(time(9,20),time(10,00)):
            return 2
        elif is_time_between(time(10,10),time(10,50)):
            return 3
        elif is_time_between(time(11,00),time(11,40)):
            return 4
        elif is_time_between(time(14,00),time(16,00)):
            return 5
        else:
            return -1

#checks if the browser is closed
def isBrowserClosed():
    isClosed = False
    try:
        driver.find_element_by_tag_name("html")
    except NoSuchWindowException:
        isClosed = True

    return isClosed

     
prevPeriod = getPeriod()

while(True):
    t.sleep(3)
    period = getPeriod()
    day = datetime.today().weekday()

    #if period exists for the current time
    if(period != -1 and day <= 4):
        #get the url for the present subject from the tt file
        subjectPath = tt[day][period]
        
        if not loggedIn:
            login()
            loggedIn = True
            th = Thread(target = markAttendance,args=(tt['mentoring'],))
            th.start()
        else:
            th = Thread(target = markAttendance, args=(subjectPath,))
            if not attendanceMarked:
                #Run function in thread so that period change will continue to be noticed
                th.start()
            else:
                #check for period change
                if(prevPeriod != period):
                    th.cancel()
                    attendanceMarked = False
                
    else:
        attendanceMarked = False
        driver.get(os.getcwd()+"/Resources/NoPeriod.html")

    #Exit application if browser is closed
    if isBrowserClosed():
        exit()
        
    prevPeriod = getPeriod()







