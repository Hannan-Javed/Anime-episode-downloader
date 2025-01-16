import requests, re, time, os, sys
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from utils import list_menu_selector, with_loading_animation, clear_undownloaded_files
from config import BASE_URL, DOWNLOAD_DIRECTORY, EPISODE_TYPE, INVALID_FILENAME_CHARS
from math import floor

@with_loading_animation("Fetching Results")
def fetch_results(anime_name, page=1):
    anime_data = []
    while True:
        base_url = f"{BASE_URL}/search.html?keyword={anime_name}&page={page}"
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find the anime listings
        anime_list = soup.find_all('li', class_='video-block')

        if not anime_list:
            break

        for anime in anime_list:
            link = anime.find('a')
            if link:
                href = link['href']
                name = link.find('div', class_='name').text.strip()
                name = ' '.join(name.split()[:-2])  # Remove "episode xx"
                if "(Dub)" not in name[len(name) - 5:]:
                    anime_data.append({'name': name, 'href': href})
        # Check for pagination
        pagination = soup.find('ul', class_='pagination')
        if not pagination or not pagination.find('li', class_='next'):
            break
        page += 1

    return anime_data

def get_anime():
    anime_name = input("Enter the name of the anime you want to download: ")

    anime_list = fetch_results(anime_name)

    while not anime_list:
        print(f"No anime found with the name: {anime_name}")
        anime_name = input("Please enter the name of the anime you want to download: ")
        anime_list = fetch_results(anime_name)
        
    
    anime = list_menu_selector("Select the anime you want to download:", [a['name'] for a in anime_list])
    url = next(a['href'] for a in anime_list if a['name'] == anime)
    return anime, url.rstrip(re.findall("[0-9]+", url)[-1])

def download_episode(driver, episode_number):
    files = os.listdir(current_download_directory)
    if ".crdownload" not in "".join(files):
        return False  # Episode did not start downloading
    
    print(f"Downloading episode {episode_number}")
    file_name = next(f for f in files if f.endswith(".crdownload"))

    driver.get("chrome://downloads/")
    progress = driver.execute_script("return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('cr-progress').value")
    while progress == 0:
        progress = driver.execute_script("return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('cr-progress').value")
    
    file_size = floor(os.path.getsize(os.path.join(current_download_directory, file_name)) * 100 / progress / 1024 / 1024)

    spinner = ['|', '/', '-', '\\']
    spinner_index = 0
    total_time = 0
    while ".crdownload" in "".join(files):
        progress_size = os.path.getsize(os.path.join(current_download_directory, file_name)) / 1024 / 1024
        progress = progress_size * 100 / file_size

        sys.stdout.write(f"\r{progress:.2f}% downloaded, {progress_size:.2f}MB/{file_size}MB {spinner[spinner_index]}")
        sys.stdout.flush()

        spinner_index = (spinner_index + 1) % len(spinner)

        total_time += 0.1
        time.sleep(0.1)

        files = os.listdir(current_download_directory)
    return True

def download_episodes(url, episode_list):
    response = requests.get(f"{url}{episode_list[0]}")
    soup = BeautifulSoup(response.text, 'html.parser')
    videosource_link = soup.find_all('iframe')

    if not videosource_link:
        print(f"Cannot find download link for episode {episode_list[0]}!")
        return

    try:
        title = f"&{re.findall('title=[A-Za-z+]*', str(videosource_link[0]))[0]}"
    except IndexError:
        print("No such episode exists!")
        return

    prefs = {
        "download.default_directory": current_download_directory,
        "download.directory_upgrade": True,
        "download.prompt_for_download": False,
    }

    chrome_options = ChromeOptions()
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = Chrome(options=chrome_options)
    
    for current_episode in episode_list:
        if current_episode != episode_list[0]:
            response = requests.get(f"{url}{current_episode}")
            soup = BeautifulSoup(response.text, 'html.parser')
            videosource_link = soup.find_all('iframe')
    
        try:
            episode_id = re.findall("id=[0-9A-Za-z]*", str(videosource_link[0]))[0]
        except IndexError:
            print("No more episodes to download!")
            break
        download_page_link = f"{BASE_URL}/download?{episode_id}{title}{current_episode}&typesub={EPISODE_TYPE}"

        driver.get(download_page_link)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'mirror_link')))

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        link_download_section = soup.find('div', class_='mirror_link')
        links = link_download_section.find_all('div')

        successful = False
        for link_div in reversed(links):
            clear_undownloaded_files(current_download_directory)
            download_link_tag = link_div.find('a')
            if download_link_tag and 'href' in download_link_tag.attrs:
                download_link = download_link_tag['href']
                download_element = driver.find_element(By.XPATH, f'//a[@href="{download_link}"]')
                driver.execute_script("arguments[0].click();", download_element)
                time.sleep(2)
                successful = download_episode(driver, current_episode)
                if successful:
                    break
                else:
                    if len(driver.window_handles) == 2:
                        driver.switch_to.window(driver.window_handles[1])
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    driver.get(download_page_link)
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'mirror_link')))
                    print(f"Retrying download with another link for episode {current_episode}...")
        if successful:
            print(f"Successfully downloaded episode {current_episode}!")
        else:
            print(f"Error! Cannot download episode {current_episode}")
        
    driver.quit()
    print("All episodes downloaded!")

if __name__ == "__main__":
    continue_download = True

    while continue_download:
        anime_name, url = get_anime()
        url = f"{BASE_URL}/{url}"
        if any(char in anime_name for char in INVALID_FILENAME_CHARS):
            for char in INVALID_FILENAME_CHARS:
                anime_name = anime_name.replace(char, '')
        os.makedirs(os.path.join(DOWNLOAD_DIRECTORY, anime_name), exist_ok=True)
        current_download_directory = os.path.join(DOWNLOAD_DIRECTORY, anime_name)
        
        download_option = list_menu_selector("Select the number of episodes you want to download:", [
            'All - From episode 1 until final episode',
            'm - Episode m',
            'm,n - From episode m to n (m <= n)',
            'm,-1 - From episode m to final',
            'm,n,o..... - Episodes m, n, o, ....',
            '1 - Download if it\'s a movie'
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
