import os, logging, coloredlogs, time
from pathlib import Path
from datetime import datetime
from packages.miscellaneous import GetUserDetails,is_connected, connectionCheck
from packages.uims import UimsManagement
from packages.BB import ClassManagement, LoginBB, JoinOnlineClass
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)

# global variables
global USERDATAFILENAME, TIMETABLE, CHROMEPATH

USERDATAFILENAME = "userData.txt"
TIMETABLE = "rptStudentTimeTable.csv"

temp = str(os.path.normpath("\\AppData\\local\\Google\\Chrome\\User Data\\Default"))
CHROMEPATH = str(Path.home()) + temp





if __name__ == '__main__':

    # Geting user details
    getDetailsOBJ = GetUserDetails(USERDATAFILENAME)
    userDetails = getDetailsOBJ.getDetails()
    userName = userDetails['username']
    password = userDetails['password']

    # Getting details from UIMS
    uimsManagementOBJ = UimsManagement(TIMETABLE,userName,password,CHROMEPATH)
    if not os.path.isfile(TIMETABLE):
        uimsManagementOBJ.getDetailsFromUIMS()

    # Reading all user details from csv file
    allDetails = uimsManagementOBJ.loadDetailsFromFIle()

    BbClassManagementOBJ = ClassManagement()
    lecturesToAttend = BbClassManagementOBJ.fromWhichLecture(allDetails)

    # Logging into BB Account
    BbLoginOBJ = LoginBB(userName,password,CHROMEPATH)
    driver = BbLoginOBJ.loginBB()

    IsLastClass = False
    # Looping through all Lectures
    for index in range(lecturesToAttend-1,len(allDetails)):
        classJoinTime = BbClassManagementOBJ.joinClassDetails(allDetails[index], IsLastClass)
        classJoinName = (allDetails[index])[1]

        # check if the class is last one
        if(index+1<len(allDetails)):
            nextClassJoinTime = BbClassManagementOBJ.joinClassDetails(allDetails[index+1],IsLastClass)
        else:
            IsLastClass=True
            nextClassJoinTime = BbClassManagementOBJ.joinClassDetails(allDetails[index],IsLastClass)

        # checking if class time is less than next class time
        IsTimeToJoinClass = BbClassManagementOBJ.compareTime(classJoinTime)

        # check if time for class is gone or not
        if not IsTimeToJoinClass:
            logger.critical(f"You missed lecture for: {classJoinName}")
        else:
            # checking if class joining link is available or not
            IsLinkAvailable = BbClassManagementOBJ.checkLinkAvailability(driver, classJoinName, nextClassJoinTime, classJoinTime)

        
        if IsTimeToJoinClass and IsLinkAvailable[0]:
            # Checking if connection is Available or not
            networkAvaliable = connectionCheck()
            if not networkAvaliable:
                is_connected()

            while(networkAvaliable):
                try:
                    WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, f"//span[text()='{IsLinkAvailable[1]}']"))).click()
                    break
                except:
                    logger.error(f"Unabale to join class: {classJoinName}. Retrying ....")
                    is_connected()
            
            joinClassOBJ = JoinOnlineClass(driver.window_handles[-1],driver.window_handles[0],driver,classJoinName,nextClassJoinTime)
            joinClassOBJ.start()

            currentTime = datetime.strptime(f"{datetime.now().time()}","%H:%M:%S.%f")
            timeTowait = nextClassJoinTime - currentTime
            timeTowait = timeTowait.total_seconds()
            logger.info(f"Next class in {timeTowait} seconds.....")
            time.sleep(timeTowait)
        
    driver.close()
    exit()


            
        