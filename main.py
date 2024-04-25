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
    
    # keep open until downloaded
    totaltime = 0
    files = os.listdir(download_directory)
    if ".crdownload" in "".join(files) == False:
        # Episode didnt start downloading
        return False
    while(".crdownload" in "".join(files)) and totaltime<=150:
        print("Downloading episode "+str(i)+".......")
        time.sleep(5)
        totaltime+=5
        files = os.listdir(download_directory)
    # wait two and a half minutes before returning false
    if totaltime > 30:
        return False
    return True

def download_episodes(url, start_episode, end_episode):

    i = start_episode
    if end_episode == -1:
        end_episode = 10000
    while i < end_episode+1:
        response = requests.get(url+str(i))
        soup = BeautifulSoup(response.text, 'html.parser')
        videosource_link = soup.findAll('iframe')
        if not videosource_link:
            break
        # find episode download page id
        id = re.findall("id=[0-9A-Za-z]*",str(videosource_link[0]))[0]
        downloadpagelink = "https://embtaku.pro/download?"+id+"&title=Psycho-Pass+3+Episode+"+str(i)+"&typesub=SUB&mip=0.0.0.0&refer=https://goone.pro/&ch=d41d8cd98f00b204e9800998ecf8427e&token2=4J8hKUzBdsRuuak9VRDseg&expires2=1713795921&op=1"
    
        driver = webdriver.Chrome()
        driver.get(downloadpagelink)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        downloadlinks = []

        # find links for all 1inks - 1080p, 720p, 480p and 360p
        for j in range(4):
            downloadlinks.append([soup.find_all('a')[j+1].text] + [re.findall("https[A-Za-z0-9-=:/.?]*",str(soup.find_all('a')[j+1]))[0]])
        
        successful = False
        while len(downloadlinks)!=0:

            if successful:
                print("Successfully downloaded episode "+str(i)+"!")
                break
            else:
                # check if its one of 1080p, 720p, 480p or 360p link
                if ")" not in downloadlinks[-1][0]:
                    downloadlinks.pop()
                    continue

                # start driver again
                driver.quit()
                 # start simulating chrome
                driver = webdriver.Chrome()
                driver.get(downloadpagelink)

                # wait for page to load
                time.sleep(3)

                # clean directory by deleting undownloaded files
                clear_undownloaded_files()

                # click on the link in reverse order (e.g. 1080p is the last link)
                downloadlink = driver.find_element(By.XPATH,'//a[@href="'+downloadlinks[-1][1]+'"]')
                driver.execute_script("arguments[0].click();", downloadlink)
                time.sleep(2)

                successful = download_episode(i)
        
        # cannot download from any link
        if len(downloadlinks)==0:
            print("Error! Cannot downloaded episode "+str(i))
        driver.quit()
        i+=1
    print("All episodes downloaded!")
            

if __name__ == "__main__":

    url = input('''Go to this website and paste the link of the first episode of the anime you would like to download:
https://goone.pro
''')
    url = url[:-1]
    
    episodes = input('''Enter the number of episodes you want to download
m - From episode 1 until episode m
m,n - From episode m to n (m < n)
m,-1 - From episode m to final
All - From episode 1 until final episode
(Just enter 1 if its a movie)
''')
    
    if episodes.lower() == 'all':
        download_episodes(url, 1, -1)
    elif len(episodes.split(','))>1:
        download_episodes(url, int(episodes.split(',')[0]), int(episodes.split(',')[1]))
    else:
        download_episodes(url, 1, episodes)
