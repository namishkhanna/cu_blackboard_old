from selenium import webdriver
from .miscellaneous import is_connected, connectionCheck, LOCK, bbPermissionFlag
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
from bs4 import BeautifulSoup as bs4
from threading import Thread
import logging, coloredlogs, time

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)


class LoginBB():
    """
        This class handels logging into Black Board (BB)

        Attributes:
            userName: UID of student.
            password: password of student.
            chromePath: path to default chrome profile
    """

    def __init__(self, userName, password, chromePath):
        self.userName = userName
        self.password = password
        self.chromePath = chromePath

    # logging into BB account
    def loginBB(self):

        # declaring chrome drivers
        try:
            chrome_options = Options()
            chrome_options.add_argument("--use-fake-ui-for-media-stream")
            #chrome_options.add_argument(f"user-data-dir={self.chromePath}")
            chrome_options.add_argument('log-level=3')
            driver = webdriver.Chrome(options=chrome_options)
            driver.maximize_window()
        except:
            logger.error("Check if chromedrivers are in path.")
            logger.info("Exiting the program .....")
            exit()

        networkAvaliable = connectionCheck()
        if not networkAvaliable:
            is_connected()
        
        # entering username and password in BB
        while(networkAvaliable):
            try:
                driver.get('https://cuchd.blackboard.com/')
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='button-1']"))).click()
                driver.find_element_by_name('user_id').send_keys(self.userName)
                driver.find_element_by_name('password').send_keys(self.password)
                driver.find_element_by_id('entry-login').click()
                break
            except:
                logger.error("Unable to login BB")
                is_connected()

        return driver


class ClassManagement():
    def __init__(self):
        pass

    def fromWhichLecture(self,allDetails):
        # asking user from which lecture he/she wants to join
        # keeps on asking till the right input is given
        while(True):
            # if int input is given or not
            try:
                lectureNumber = int(input("Enter from which Lecture you want to Attend: "))
                print()
                # if wrong input is given
                if((lectureNumber>len(allDetails)) or (lectureNumber<=0)):
                    logger.warning("There are only " + str(len(allDetails)) + " Lectures Today")
                else:
                    break
            except:
                logger.error("Invalid Input!!")
                logger.info("Input can only be a number.")
        return lectureNumber


    # changing time from 12 to 24 hours
    def joinClassDetails(self,data, IsLastClass):
        if IsLastClass:
            time12H = datetime.strptime(f"{data[0]}", "%I:%M %p")
            classAttendTime = time12H + timedelta(minutes=45)
        else:
            time12H = datetime.strptime(f"{data[0]}", "%I:%M %p")
            classAttendTime = time12H - timedelta(minutes=15)

        return classAttendTime


    # comparing current and class join time
    def compareTime(self,classJoinTime):
        currentTime = datetime.now()
        classEndTime = classJoinTime + timedelta(minutes=60)

        if (currentTime.time()>=classJoinTime.time()) and (currentTime.time()<=classEndTime.time()):
            return True
        else:
            return False

    # finding the joining link for particular class
    def checkLinkAvailability(self,driver, classJoinName, nextClassJoinTime, classJoinTime):
        spanToBeOpened = ""
        linkNotAvailable = True
        timeRemainsForNextClass = True
        firstTime = True

        while(linkNotAvailable and timeRemainsForNextClass):

            # Checking if connection is Available or not
            networkAvaliable = connectionCheck()
            if not networkAvaliable:
                is_connected()

            if firstTime:
                firstTime=False

                # finding which class to join
                while(networkAvaliable):
                    try:
                        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, f"//h4[@title='{classJoinName.upper()}']"))).click()
                        break
                    except:
                        logger.error("Unable to open the current Lecture")
                        is_connected()
                        driver.refresh()
            else:
                is_connected()
                driver.refresh()

            # Checking if connection is Available or not
            networkAvaliable = connectionCheck()
            if not networkAvaliable:
                is_connected()
            
            # opening dropdown to find class joining button
            while(networkAvaliable):
                try:
                    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='sessions-list-dropdown']"))).click()
                    break
                except:
                    logger.error("Unable to Locate the session")
                    is_connected()
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



class JoinOnlineClass(Thread):
    def __init__(self, tabId, defaultTabId, driver, lectureName, nextClassJoinTime):
        Thread.__init__(self)
        self.tabId = tabId
        self.defaultTabId = defaultTabId
        self.driver = driver
        self.lectureName = lectureName
        self.nextClassJoinTime = nextClassJoinTime

    def run(self):
        global LOCK, bbPermissionFlag
        timeElapsed = 0

        # Switching to the class tab
        self.driver.switch_to.window(self.tabId)


        # Checking if connection is Available or not
        networkAvaliable = connectionCheck()
        if not networkAvaliable:
            is_connected()

        # check if audio and video persmissions are given or not
        if(not bbPermissionFlag):
            bbPermissionFlag = True
            audioTestFlag=False

            while(networkAvaliable):
                    try:
                        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Yes. Audio is working.']"))).click()
                        audioTestFlag = True
                    except:
                        logger.error("Exception 1 occured in Audio Testing.")
                        
                    if not audioTestFlag:
                        try:
                            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Skip audio test']"))).click()
                        except:
                            logger.error("Exception 2 occured in Audio Testing.")
                            continue
                         
                    try:
                        WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Yes. Video is working.']"))).click()
                        WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Later']"))).click()
                        WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Close']"))).click()
                        break
                    except:
                        logger.error("Error in providing permission to BB")
                        is_connected()
                        self.driver.refresh()

        # waiting in class till next class and minimum 50 minutes
        while(True):
            timeSpentInWait = 0
            currentTime = datetime.now()
            
            # check if current time is greater than next class time and minimum time in class is greater than 60 minutes
            if(currentTime.time()>=self.nextClassJoinTime.time()):
                if(timeElapsed<=3600):
                    break
                else:
                    self.driver.close()
                    break  
            else:
                # Checking if connection is Available or not
                networkAvaliable = connectionCheck()
                if not networkAvaliable:
                    is_connected()
                    while(True):
                        if not LOCK:
                            LOCK = True
                            self.driver.switch_to.window(self.tabId)
                            self.driver.refresh()
                            break
                        else:
                            logging.info("Waiting for other tabs to finish their task")
                            time.sleep(2)
                            timeSpentInWait+2

                time.sleep(60)
                timeElapsed+=60

        # converting total class joined seconds to minutes
        total_class_time_min = timeElapsed /60
        logger.warning("Attended " + self.lectureName + " Lecture for: " + str(total_class_time_min) + " minutes")
                    
