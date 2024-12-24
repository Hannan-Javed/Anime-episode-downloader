import requests, re, time, os
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome, ChromeOptions
from PyInquirer import prompt
import time
import sys
import threading

def loading_animation(message, stop_event):
    while not stop_event.is_set():
        for dots in range(4):  # 0 to 3 dots
            sys.stdout.write("\r" + message + " " * 4)
            sys.stdout.flush()
            sys.stdout.write("\r" + message + "." * dots)
            sys.stdout.flush()
            time.sleep(0.5)
    print()

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

def list_menu_selector(qprompt, anime_list):
    menu = prompt(
            [
                {
                    'type': 'list',
                    'name': 'name',
                    'message': qprompt,
                    'choices': anime_list,
                }
            ]
        )
    return menu['name']

def get_anime():
    anime_name = input("Enter the name of the anime you want to download: ")
    page = 1
    base_url = "https://s3embtaku.pro/search.html?keyword={anime_name}&page={page}"

    anime_data = []

    stop_event = threading.Event()
    animation_thread = threading.Thread(target=loading_animation, args=("fetching search results", stop_event))
    animation_thread.start()

    try:
        while True:
            response = requests.get(base_url.format(anime_name=anime_name, page=page))
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find the anime listings
            anime_list = soup.find_all('li', class_='video-block')

            while not anime_list:
                anime_name = input("No anime found with the name: "+anime_name+". Please enter the name of the anime you want to download: ")
                response = requests.get(base_url.format(anime_name=anime_name, page=page))
                soup = BeautifulSoup(response.text, 'html.parser')
                anime_list = soup.find_all('li', class_='video-block')
            
            for anime in anime_list:
                # Find the anchor tag
                link = anime.find('a')
                if link:
                    # Extract href and name
                    href = link['href']
                    name = link.find('div', class_='name').text.strip()
                    name = ' '.join(name.split()[:-2])  # Strip the last two words which are always "episode xx"
                    anime_data.append({'name': name, 'href': href})
            # Check for pagination to see if there are more pages
            pagination = soup.find('ul', class_='pagination')
            if not pagination:
                break # No pagination
            next_page = pagination.find('li', class_='next')
            if not next_page:
                break  # No more pages
            page += 1 

            if len(anime_data) == 0:
                print("No anime found with the name: "+anime_name)
                anime_name = input("Please enter the name of the anime you want to download: ")
                page = 1
    finally:
        stop_event.set()
        animation_thread.join()
    
    anime = list_menu_selector("Select the anime you want to download:", [a['name'] for a in anime_data])
    url = anime_data[[a['name'] for a in anime_data].index(anime)]['href']
    # return the anime name and url after removing episode number from it
    return anime, url[:-len(re.findall("[0-9]+", url)[-1])]
        
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
    
    message = f"Downloading episode {i}"
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=loading_animation, args=(message, stop_event))
    animation_thread.start()

    try:
        while (".crdownload" in "".join(files)) and totaltime < time_limit:
            time.sleep(1)
            totaltime += 1
            # update file list to see if it is downloaded
            files = os.listdir(current_download_directory)
    finally:
        stop_event.set()
        animation_thread.join()
        print("\n")

    # wait two and a half minutes before returning false
    return totaltime < time_limit

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
        downloadpagelink = "https://s3embtaku.pro/download?"+id+title+str(current_episode)+"&typesub=" + episode_type

        # start simulating chrome
        driver.get(downloadpagelink)

        # wait for page to load
        time.sleep(3)

        # find number of download links, assuming last is the best quality
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        link_download_section = soup.find('div', class_='mirror_link')
        links = link_download_section.find_all('div')

        successful = False
        # Iterate through all links (1080p, 720p, 480p, 360p) starting from highest quality
        for link_div in reversed(links):
            # Clear undownloaded files before starting download
            clear_undownloaded_files()
            # Find download link
            downloadlink_tag = link_div.find('a')
            if downloadlink_tag and 'href' in downloadlink_tag.attrs:
                downloadlink = downloadlink_tag['href']
                download_element = driver.find_element(By.XPATH, f'//a[@href="{downloadlink}"]')
            driver.execute_script("arguments[0].click();", download_element)
            # Wait for download to start
            time.sleep(2)
            successful = download_episode(current_episode)
            if successful:
                break
            else:
                # Close any new tabs and retry with next link
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[1])
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                print(f"Restarting download with another link for episode {current_episode}...")
                # either time limit exceeded or link is invalid
                driver.get(downloadpagelink)
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
        anime_name, url = get_anime()
        url = "https://s3embtaku.pro/" + url
        # make a directory for the anime
        os.makedirs(os.path.join(download_directory, anime_name), exist_ok=True)
        current_download_directory = os.path.join(download_directory, anime_name)
        
        download_option = list_menu_selector("Select the number of episodes you want to download:", [
            'All - From episode 1 until final episode',
            'm - Episode m',
            'm,n - From episode m to n (m <= n)',
            'm,-1 - From episode m to final',
            'm,n,o..... - episode m, n, o, ....',
            '1 - do this if it\'s a movie'
        ])

        if download_option.startswith('All'):
            download_episodes(url, list(range(1, 10000)))
        elif download_option.startswith('m,n,o'):
            episodes = input("Enter the episode numbers separated by commas: ")
            episodes_list = list(map(int, episodes.split(',')))
            download_episodes(url, episodes_list)
        elif download_option.startswith('m,n'):
            m = int(input("Enter the starting episode number (m): "))
            n = int(input("Enter the ending episode number (n): "))
            episodes_list = list(range(m, n + 1)) if n != -1 else list(range(m, 10000))
            download_episodes(url, episodes_list)
        elif download_option.startswith('m,-1'):
            m = int(input("Enter the starting episode number (m): "))
            download_episodes(url, list(range(m, 10000)))
        elif download_option.startswith('m'):
            m = int(input("Enter the episode number (m): "))
            download_episodes(url, [m])
        elif download_option.startswith('1'):
            download_episodes(url, [1])
        
        continue_download = input("Do you want to download another anime? (y/n): ").lower() == 'y'
