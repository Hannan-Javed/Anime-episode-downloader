import requests, re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time, os
import os

def get_download_directory():
    home_directory = os.path.expanduser("~")  # Get user's home directory
    
    # Check the operating system to determine the download directory
    if os.name == 'posix':  # Linux or macOS
        download_directory = os.path.join(home_directory, 'Downloads')
    elif os.name == 'nt':  # Windows
        download_directory = os.path.join(home_directory, 'Downloads')
    else:
        download_directory = None  # Unsupported operating system
    
    return download_directory

download_directory = get_download_directory()

def clear_undownloaded_files():
    # get all the files
    file_list = os.listdir(download_directory)

    # Iterate over the files and delete .crdownload files
    for file_name in file_list:
        if file_name.endswith(".crdownload"):
            file_path = os.path.join(download_directory, file_name)
            os.remove(file_path)

def download_episode(i):
    
    totaltime = 0
    files = os.listdir(download_directory)

    if ".crdownload" not in "".join(files):
        # Episode did not start downloading
        return False
    while (".crdownload" in "".join(files)) and totaltime<150:
        # print every five seconds
        if totaltime%15==0:
            print("Downloading episode "+str(i)+".......")

        time.sleep(1)
        totaltime+=1

        # update file list to see if it is downloaded
        files = os.listdir(download_directory)

    # wait two and a half minutes before returning false
    return totaltime<150

def download_episodes(url, start_episode, end_episode):

    current_episode = start_episode
    if end_episode == -1:
        end_episode = 10000
    response = requests.get(url+str(current_episode))
    soup = BeautifulSoup(response.text, 'html.parser')
    videosource_link = soup.findAll('iframe')

    if not videosource_link:
        print("Cannot find download link for episode "+str(current_episode))
        current_episode+=1
    try:
        # title is fixed so find outside loop
        title = "&"+re.findall("title=[A-Za-z+]*",str(videosource_link[0]))[0]
    except IndexError:
        print("No such episode exists!")

    driver = webdriver.Chrome()
    
    while current_episode < end_episode+1:
        
        # find episode download page id
        try:
            id = re.findall("id=[0-9A-Za-z]*",str(videosource_link[0]))[0]
        except IndexError:
            print("No more episodes to download!")
            break
        downloadpagelink = "https://embtaku.pro/download?"+id+title+str(current_episode)+"&typesub=SUB"

        # start simulating chrome
        
        driver.get(downloadpagelink)

        # wait for page to load
        time.sleep(3)

        # main loop to iterate through all links (1080p, 720p, 480p, 360p) starting from highest if any link fails
        j=3
        while True:

            # clear undownloaded files before starting download
            clear_undownloaded_files()
            # find download link
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            downloadlink = re.findall("https[A-Za-z0-9-=:/.?]*",str(soup.find_all('a')[j+1]))[0]
            downloadlink = driver.find_element(By.XPATH,'//a[@href="'+downloadlink+'"]')
            driver.execute_script("arguments[0].click();", downloadlink)
            # wait for download to start
            time.sleep(2)
            successful = download_episode(current_episode)
            j-=1

            if successful or j==-1:
                break
            else:
                # relaunch for next page if this one was unsuccessful and still links left
                if ".crdownload" in "".join(os.listdir(download_directory)):
                    driver.quit()
                    driver = webdriver.Chrome()
                print("Restarting download with another link.....")
                driver.get(downloadpagelink)
                # wait for page to load
                time.sleep(3)
        if successful:
            print("Successfully downloaded episode "+str(current_episode)+"!")
        else:
            # cannot download from any link
            print("Error! Cannot downloaded episode "+str(current_episode))
    
        # go to next page
        current_episode+=1
        if current_episode >= end_episode+1:
            break
        response = requests.get(url+str(current_episode))
        soup = BeautifulSoup(response.text, 'html.parser')
        videosource_link = soup.findAll('iframe')
        if not videosource_link:
            print("Cannot find download link for episode "+str(current_episode))
            continue
    driver.quit()
    print("All episodes downloaded!")
            

if __name__ == "__main__":

    continue_download = True

    while continue_download:
        url = input('''Go to this website and paste the link of any episode of the anime you would like to download:
    https://goone.pro
    ''')
        ep = re.findall("[0-9]+",url)
        while len(ep)==0:
            url = input("Invalid URL! Please enter a valid URL: ")
            ep = re.findall("[0-9]+",url)
        ep = len(ep[-1])
        url = url[:-ep]
    
        valid_link = episodes.lower()[0] == 'a' or len(episodes.split(','))>1 or type(episodes)==int 

        while not valid_link:
            print("Invalid input! Please enter a valid range: ")
            episodes = input('''Enter the number of episodes you want to download
                                m - Episode m
                                m,n - From episode m to n (m <= n)
                                m,-1 - From episode m to final
                                All - From episode 1 until final episode
                                (Enter 1 if its a movie)
                                ''')
            
        if episodes.lower()[0] == 'a':
            download_episodes(url, 1, -1)
        elif len(episodes.split(','))>1:
            download_episodes(url, int(episodes.split(',')[0]), int(episodes.split(',')[1]))
        else:
            download_episodes(url, int(episodes), int(episodes))
        
        continue_download = input("Do you want to download another anime? (y/n): ").lower() == 'y'
