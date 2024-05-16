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
    while (".crdownload" in "".join(files)) and totaltime<160:
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

    i = start_episode
    if end_episode == -1:
        end_episode = 10000
    response = requests.get(url+str(i))
    soup = BeautifulSoup(response.text, 'html.parser')
    videosource_link = soup.findAll('iframe')
    if not videosource_link:
        print("Cannot find download link for episode "+str(i))
        i+=1
    
    # title is fixed so find outside loop
    title = "&"+re.findall("title=[A-Za-z+]*",str(videosource_link[0]))[0]

    while i < end_episode+1:
        
        # find episode download page id
        id = re.findall("id=[0-9A-Za-z]*",str(videosource_link[0]))[0]
        downloadpagelink = "https://embtaku.pro/download?"+id+title+str(i)+"&typesub=SUB"
        downloadlinks = []

        # start simulating chrome
        driver = webdriver.Chrome()
        driver.get(downloadpagelink)

        # wait for page to load
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # find links for all 1inks - 1080p, 720p, 480p and 360p
        for j in range(4):
            downloadlinks.append([soup.find_all('a')[j+1].text] + [re.findall("https[A-Za-z0-9-=:/.?]*",str(soup.find_all('a')[j+1]))[0]])
        
        # clean directory by deleting undownloaded files
        clear_undownloaded_files()

        # remove external links
        while ")" not in downloadlinks[-1][0]:
            downloadlinks.pop()

        # click on the link in reverse order (e.g. 1080p is the last link)
        while True:

            # click on the link in reverse order (e.g. 1080p is the last link)
            downloadlink = driver.find_element(By.XPATH,'//a[@href="'+downloadlinks[-1][1]+'"]')
            driver.execute_script("arguments[0].click();", downloadlink)
            time.sleep(2)

            successful = download_episode(i)

            # pop this used link
            downloadlinks.pop()

            if successful or len(downloadlinks)==0:
                break
            else:
                # relaunch for next page if this one was unsuccessful and still links left
                driver.quit()
                print("Restarting download with another link.....")
                driver = webdriver.Chrome()
                driver.get(downloadpagelink)

                # wait for page to load
                time.sleep(3)

        if successful:
            print("Successfully downloaded episode "+str(i)+"!")
        else:
            # cannot download from any link
            print("Error! Cannot downloaded episode "+str(i))
    
        driver.quit()
        # go to next page
        i+=1
        if i >= end_episode+1:
            break
        response = requests.get(url+str(i))
        soup = BeautifulSoup(response.text, 'html.parser')
        videosource_link = soup.findAll('iframe')
        if not videosource_link:
            print("Cannot find download link for episode "+str(i))
            continue
    print("All episodes downloaded!")
            

if __name__ == "__main__":

    url = input('''Go to this website and paste the link of any episode of the anime you would like to download:
https://goone.pro
''')
    ep = len(re.findall("[0-9]+",url)[-1])
    url = url[:-ep]
    episodes = input('''Enter the number of episodes you want to download
m - From episode 1 until episode m
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
        download_episodes(url, 1, int(episodes))
