import requests, re, time, os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome, ChromeOptions

def get_default_download_directory():
    home_directory = os.path.expanduser("~")  # Get user's home directory
    
    # Check the operating system to determine the download directory
    if os.name == 'posix':  # Linux or macOS
        download_directory = os.path.join(home_directory, 'Downloads')
    elif os.name == 'nt':  # Windows
        download_directory = os.path.join(home_directory, 'Downloads')
    else:
        download_directory = None  # Unsupported operating system
    
    return download_directory

def clear_undownloaded_files():
    # get all the files
    file_list = os.listdir(current_download_directory)

    # Iterate over the files and delete .crdownload files
    for file_name in file_list:
        if file_name.endswith(".crdownload"):
            file_path = os.path.join(current_download_directory, file_name)
            os.remove(file_path)

def download_episode(i):
    
    totaltime = 0
    files = os.listdir(current_download_directory)

    if ".crdownload" not in "".join(files):
        # Episode did not start downloading
        return False
    while (".crdownload" in "".join(files)) and totaltime<time_limit:
        # print every fifteen seconds
        if totaltime%15==0:
            print("Downloading episode "+str(i)+"."*(totaltime//15+1))

        time.sleep(1)
        totaltime+=1

        # update file list to see if it is downloaded
        files = os.listdir(current_download_directory)

    # wait two and a half minutes before returning false
    return totaltime<time_limit

def download_episodes(url, episode_list):

    response = requests.get(url+str(episode_list[0]))
    soup = BeautifulSoup(response.text, 'html.parser')
    videosource_link = soup.findAll('iframe')

    if not videosource_link:
        print("Cannot find download link for episode "+str(episodes[0])+"!")
    try:
        # title is fixed so find outside loop
        title = "&"+re.findall("title=[A-Za-z+]*",str(videosource_link[0]))[0]
    except IndexError:
        print("No such episode exists!")

    prefs = {
    "download.default_directory": current_download_directory,
    "download.directory_upgrade": True,
    "download.prompt_for_download": False,
    }

    chromeOptions = ChromeOptions()
    chromeOptions.add_experimental_option("prefs", prefs)
    driver = Chrome(options=chromeOptions)
    
    for current_episode in episode_list:
        if current_episode!=episode_list[0]:
            response = requests.get(url+str(current_episode))
            soup = BeautifulSoup(response.text, 'html.parser')
            videosource_link = soup.findAll('iframe')
    
        # find episode download page id
        try:
            id = re.findall("id=[0-9A-Za-z]*",str(videosource_link[0]))[0]
        except IndexError:
            print("No more episodes to download!")
            break
        downloadpagelink = "https://embtaku.pro/download?"+id+title+str(current_episode)+"&typesub=" + episode_type

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
            downloadlink = re.findall("https[A-Za-z0-9-=:/.?]*",str(soup.find_all('a')[j+1]))
            if downloadlink:
                downloadlink = driver.find_element(By.XPATH,'//a[@href="'+downloadlink[0]+'"]')
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
                if len(driver.window_handles)>1:
                    driver.switch_to.window(driver.window_handles[1])
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                print("Restarting download with another link for episode"+str(current_episode)+"...")
                driver.get(downloadpagelink)
                # wait for page to load
                time.sleep(3)
        if successful:
            print("Successfully downloaded episode "+str(current_episode)+"!")
        else:
            # cannot download from any link
            print("Error! Cannot downloaded episode "+str(current_episode))
        
    driver.quit()
    print("All episodes downloaded!")

# choose default download directory or enter your own
download_directory = get_default_download_directory() # "/path/to/download/directory"            
time_limit = 150
episode_type = "SUB" 

if __name__ == "__main__":

    continue_download = True

    while continue_download:
        url = input('''Go to this website and paste the link of any episode of the anime you would like to download:
https://s3taku.com
''')
        ep = re.findall("[0-9]+",url)
        while len(ep)==0:
            url = input("Invalid URL! Please enter a valid URL: ")
            ep = re.findall("[0-9]+",url)
        ep = len(ep[-1])
        url = url[:-ep]

        episodes = input('''\n\nEnter the number of episodes you want to download
All - From episode 1 until final episode
m - Episode m
m,n - From episode m to n (m <= n)
m,-1 - From episode m to final
m,n,o..... - episode m, n, o, ....
(Enter 1 if its a movie)
''')
        # make a directory for the anime
        anime_name = url[url.rfind('/')+1:]
        anime_name = anime_name.replace('-', ' ').replace('episode', '').replace('dub', '').strip()
        anime_name = ' '.join(word.capitalize() for word in anime_name.split())
        os.makedirs(os.path.join(download_directory, anime_name), exist_ok=True)
        current_download_directory = os.path.join(download_directory, anime_name)

        valid_episodes = episodes.lower()[0] == 'a' or len(episodes.split(','))>1 or type(episodes)==int or '' not in episodes.split(',')

        while not valid_episodes:
            episodes = input("Invalid input! Please enter a valid input: ")
            valid_episodes = episodes.lower()[0] == 'a' or len(episodes.split(','))>1 or type(episodes)==int or '' not in episodes.split(',')

        if episodes.lower()[0] == 'a':
            download_episodes(url, list(range(1, 10000)))
        elif len(episodes.split(','))==2:
            episodes_list = list(range(int(episodes.split(',')[0]), (int(episodes.split(',')[1])+1) if int(episodes.split(',')[1])!=-1 else 10000))
            download_episodes(url, episodes_list)
        elif len(episodes.split(','))>2:
            download_episodes(url, list(map(int, episodes.split(','))))
        else:
            download_episodes(url, [int(episodes)])
        
        continue_download = input("Do you want to download another anime? (y/n): ").lower() == 'y'
