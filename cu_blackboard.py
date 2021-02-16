from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from os.path import join, dirname
from bs4 import BeautifulSoup as bs4
from datetime import datetime, timedelta
import os, re, csv ,time, requests, socket
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



# global variables
global FILEPATH, USERNAME, PASSWORD, DRIVERLOADED
FILEPATH = "rptStudentTimeTable.csv"
DRIVERLOADED = False
print("Enter Username: ")
USERNAME = input()
print("Enter Password: ")
PASSWORD = input()



# check if device is connected to internet
def is_connected():
    try:
        socket.create_connection(("1.1.1.1", 53))
        return True
    except OSError:
        pass
    return False



# getting time table from CUIMS
def getDetailsFromUIMS(driver):
    is_connected_1 = True
    is_connected_2 = True
    is_connected_3 = True
    
    # entering username and password in CUIMS
    while(is_connected_1):
        if(is_connected()):
            driver.get('https://uims.cuchd.in/uims/')
            driver.find_element_by_name('txtUserId').send_keys(USERNAME)
            driver.find_element_by_name('btnNext').click()
            driver.find_element_by_name('txtLoginPassword').send_keys(PASSWORD)
            driver.find_element_by_name('btnLogin').click()
            is_connected_1 = False
        else:
            time.sleep(2)
            driver.refresh()

    # going to time table page
    while(is_connected_2):
        if(is_connected()):
            driver.get('https://uims.cuchd.in/UIMS/frmMyTimeTable.aspx')
            is_connected_2 = False
        else:
            time.sleep(2)
            driver.refresh()

    html = driver.page_source
    soup = BeautifulSoup(html,"lxml")
    soup = str(soup(text=re.compile('ControlID')))[1722:1754]

    # downloading time table csv file
    while(is_connected_3):
        if(is_connected()):
            driver.get(f'https://uims.cuchd.in/UIMS/Reserved.ReportViewerWebControl.axd?ReportSession=ycmrf5jtz5d1gjjcfk4bleib&Culture=1033&CultureOverrides=True&UICulture=1033&UICultureOverrides=True&ReportStack=1&ControlID={soup}&OpType=Export&FileName=rptStudentTimeTable&ContentDisposition=OnlyHtmlInline&Format=CSV')
            is_connected_3 = False
        else:
            time.sleep(2)
            driver.refresh()
    
    time.sleep(2)
    download_folder_path = str(os.path.join(Path.home(), "Downloads"))
    file_path = download_folder_path + "/"  + "rptStudentTimeTable.csv"

    # copying the same file in current directory
    with open(file_path,'r') as f:
        with open("rptStudentTimeTable.csv",'w') as file_to_write:
            file_to_write.writelines(f)
    
    time.sleep(2)



# filtering data and extracting necessary details
def loadDetailsFromFIle():
    file_path = "rptStudentTimeTable.csv"
    Empty = ""

    now = datetime.now()
    day = str(now.strftime("%A"))[:3]
    join = []
    to_join = []
    all_course_name = []
    unique_course_name = []

    # finding time and course code
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if(len(row)==3):
                if(row[2]!='CourseCode'):
                    if(row[2]!=Empty):
                        if(row[1]==day):
                            to_join.append([row[0].split(" ")[0] + " " + row[0].split(" ")[3],row[2].split(':')[0]])

    # finding all course code and course name
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if(len(row)==2):
                if(row[1]!='Title'):
                    all_course_name.append(row)

    # finding unique course code and course name
    for x in all_course_name: 
        if x not in unique_course_name: 
            unique_course_name.append(x) 

    # joining time and course name
    for i in to_join:
        for j in unique_course_name:
            if(i[1]==j[0]):
                join.append([i[0],j[1].lstrip()])
                
    return join



# logging into BB account
def loginBB(DRIVERLOADED,driver):
    is_connected_1 = True

    if(not DRIVERLOADED):
        DRIVERLOADED = True
        chrome_options = Options()
        chrome_options.add_argument("--use-fake-ui-for-media-stream")
        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()
    
    # entering username and password in BB
    while(is_connected_1):
        if(is_connected()):
            driver.get('https://cuchd.blackboard.com/')
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='button-1']"))).click()
            driver.find_element_by_name('user_id').send_keys(USERNAME)
            driver.find_element_by_name('password').send_keys(PASSWORD)
            driver.find_element_by_id('entry-login').click()
            is_connected_1 = False
        else:
            time.sleep(2)
            driver.refresh()

    return driver



# substracting 15 minutes from class joining time
def joinClassDetails(data):
    time12H = datetime.strptime(f"{data[0]}", "%I:%M %p")
    classAttendTime = time12H - timedelta(minutes=15)

    return classAttendTime



# adding 45 minutes to class joining time
def nextClassDetails(data):
    time12H = datetime.strptime(f"{data[0]}", "%I:%M %p")
    classAttendTime = time12H + timedelta(minutes=45)

    return classAttendTime



# comparing current and class join time
def compareTime(classJoinTime):
    currentTime = datetime.now()
    classEndTime = classJoinTime + timedelta(minutes=60)

    if (currentTime.time()>=classJoinTime.time()) and (currentTime.time()<=classEndTime.time()):
        return True
    else:
        return False



# finding the joining link for particular class
def checkLinkAvailability(driver, classJoinName, nextJoinClassTime, classJoinTime):
    spanToBeOpened = ""
    linkNotAvailable = True
    timeRemainsForNextClass = True
    firstTime = True

    while(linkNotAvailable and timeRemainsForNextClass):
        is_connected_1 = True
        is_connected_2 = True
        if firstTime:
            firstTime=False

            # finding which class to join
            while(is_connected_1):
                if(is_connected()):
                    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, f"//h4[@title='{classJoinName.upper()}']"))).click()
                    is_connected_1 = False
                else:
                    time.sleep(2)
                    driver.refresh()
        else:
            driver.refresh()
        
        # opening dropdown to find class joining button
        while(is_connected_2):
            if(is_connected()):
                try:
                    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='sessions-list-dropdown']"))).click()
                    is_connected_2 = False
                except:
                    driver.refresh()
            else:
                time.sleep(2)
                driver.refresh()
        
        html_page = driver.page_source
        classes_avaliable = list()
        soup = bs4(html_page,features="lxml")

        # finding class joining button
        for tag in soup.findAll("a",{"role":"menuitem"}):
            span_text = (str(tag.text))[1:-1]
            if (str(span_text)!=str('Course Room')) and ('Visible to students' not in span_text) and ('Hidden from students' not in span_text):
                classes_avaliable.append(span_text)  

        currentTime = datetime.now()

        if len(classes_avaliable)>=1:
            linkNotAvailable = False
            spanToBeOpened = classes_avaliable[0]

        if(currentTime.time()>=nextClassJoinTime.time()):
            timeRemainsForNextClass = False
        
        time.sleep(30)

    if not linkNotAvailable:
        return [True,spanToBeOpened]
    else:
        return [False,""]



if __name__ == '__main__':

    # check if file that contains online session info is available or not
    driver = ""
    if not os.path.isfile(FILEPATH): 
        if not DRIVERLOADED:
            DRIVERLOADED = True
            chrome_options = Options()
            chrome_options.add_argument("--use-fake-ui-for-media-stream")
            driver = webdriver.Chrome(options=chrome_options)
            driver.maximize_window()

        # getting data from CUIMS
        getDetailsFromUIMS(driver)
    
    # loading details from csv file
    allData = loadDetailsFromFIle()

    # displaying all lectures of the day
    print("Total Lectures Today: ")
    for i in range(len(allData)):
        print(str(i+1) + ": " + allData[i][0] + " " + allData[i][1])
    print()

    # asking user from which lecture he/she wants to join
    # keeps on asking till the right input is given
    lec = True
    while(lec):
        # if int input is given or not
        try:
            print("Enter from which Lecture you want to Attend: ")
            lectureNumber = int(input())
            print()
            # if wrong input is given
            if((lectureNumber>len(allData)) or (lectureNumber<=0)):
                print("There are only " + str(len(allData)) + " Lectures Today")
            else:
                lec = False
        except:
            print("Invalid Input !!!")
            print()

    # logging into BB account
    driver = loginBB(DRIVERLOADED,driver)

    IsLastClass = False
    nextClassJoinTime = ""
    bb_permission_flag = False

    # attending all classes one by one
    for index in range(lectureNumber-1,len(allData)):

        classJoinTime = joinClassDetails(allData[index])
        classJoinName = (allData[index])[1]
        nextClassJoinTime = nextClassDetails(allData[index])

        # joining class
        classtojoin = True
        
        while(classtojoin):
            is_connected_course = True
            is_connected_link = True
            is_connected_driver = True

            # opening course page
            while(is_connected_course):
                if(is_connected()):
                    driver.get('https://cuchd.blackboard.com/ultra/course')
                    is_connected_course = False
                else:
                    time.sleep(2)
                    driver.refresh()
            
            print("Going to Attend " + classJoinName + " Lecture at: " + str(classJoinTime.time()))

            # checking if class joining link is available or not
            IsLinkAvailable = checkLinkAvailability(driver, classJoinName, nextClassJoinTime, classJoinTime)

            # checking if class time is less than next class time
            IsTimeToJoinClass = compareTime(classJoinTime)

            # check if class time is less than next class time and class joining link is available
            if IsTimeToJoinClass and IsLinkAvailable[0]:
                classtojoin = False
                currentTime = datetime.now()

                print("Attending " + classJoinName + " Lecture at: " + str(currentTime.time()))

                while(is_connected_link):
                    if(is_connected()):
                        WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, f"//span[text()='{IsLinkAvailable[1]}']"))).click()
                        is_connected_link = False
                    else:
                        time.sleep(2)
                        driver.refresh()

                driver.switch_to.window(driver.window_handles[len(driver.window_handles)-1])

                # check if audio and video persmissions are given or not
                if(not bb_permission_flag):
                    bb_permission_flag = True

                    while(is_connected_driver):
                        if(is_connected()):
                            try:
                                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Yes. Audio is working.']"))).click()
                            except:
                                print("Exception occured in Audio Testing.")
                                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Skip audio test']"))).click()

                            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Yes. Video is working.']"))).click()
                            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Later']"))).click()
                            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Close']"))).click()
                            is_connected_driver = False
                        else:
                            time.sleep(2)
                            driver.refresh()

                # waiting in class till next class and minimum 50 minutes
                wait_in_class = True
                while(wait_in_class):
                    currentTime = datetime.now()
                    
                    # check if last lecture or not
                    # if not last lecture
                    if(index!=(lectureNumber-1)):
                        # check if current time is greater than next class time and minimum time in class is greater than 50 minutes
                        if(currentTime.time()>=nextClassJoinTime.time()):
                            if(total_class_time<=3000):
                                wait_in_class = False
                            else:
                                wait_in_class = False
                                driver.close()
                        else:
                            is_connected_again = True

                            while(is_connected_again):
                                if(is_connected()):
                                    is_connected_again = False
                                    time.sleep(60)
                                    total_class_time = total_class_time + 60
                                else:
                                    time.sleep(2)
                                    driver.refresh()

                    # if last lecture
                    else:
                        # check if minimum time in class is greater than 50 minutes
                        # if minimum time is less than 50 minutes
                        if(total_class_time<=3000):
                            is_connected_again = True

                            while(is_connected_again):
                                if(is_connected()):
                                    is_connected_again = False
                                    time.sleep(60)
                                    total_class_time = total_class_time + 60
                                else:
                                    time.sleep(2)
                                    driver.refresh()
                        
                        # if minimum time is greater than 50 minutes
                        else:
                            if(currentTime.time()>=nextClassJoinTime.time()):
                                wait_in_class = False
                                driver.close()
                            time.sleep(30)

                # converting total class joined seconds to minutes
                total_class_time_min = total_class_time /60
                print("Attended " + classJoinName + " Lecture for: " + str(total_class_time_min) + " minutes")

                driver.switch_to.window(driver.window_handles[0])

            # if time to attend lecture is gone and link is not available    
            elif not IsLinkAvailable[0]:
                print("Class Joining Link for " + classJoinName + " Lecture Not Found !!!")
                classtojoin = False
            
            # if time to attend lecture is gone
            elif not IsTimeToJoinClass:
                print("Time for " + classJoinName + " Lecture Gone !!!")
                classtojoin = False
                
    driver.quit()
