import requests, re, time, os
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from exceptions import InvalidLinkError
from utils import setup_driver, get_file_size, list_menu_selector, manage_download, with_loading_animation, clear_undownloaded_files,DownloadState
from config import BASE_URL, DOWNLOAD_DIRECTORY, EPISODE_TYPE, INVALID_FILENAME_CHARS

@with_loading_animation(lambda: "Fetching Results")
def fetch_results(anime_name: str, page: int = 1) -> list:
    """
    Fetches the search results for the given anime name
    
    Args:
        anime_name: The name of the anime to search for
        page: The page number to start fetching results from. By default, it starts from page 1

    Returns:
        list: A list of dictionaries containing the anime name, href and the final episode number
    """
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
                name = name.split()
                final_episode_number = name[-1]
                name = ' '.join(name[:-2])  # Remove "episode xx"
                if "(Dub)" not in name[len(name) - 5:]:
                    anime_data.append({'name': name, 'href': href, 'range': final_episode_number})
        # Check for pagination
        pagination = soup.find('ul', class_='pagination')
        if not pagination or not pagination.find('li', class_='next'):
            break
        page += 1

    return anime_data

def get_anime() -> tuple:
    """
    Fetches the anime name and the final episode number from the user

    Returns:
        tuple: A tuple containing the anime name, the url and the final episode number
    """
    anime_name = input("Enter the name of the anime you want to download: ")

    anime_list = fetch_results(anime_name)

    while not anime_list:
        print(f"No anime found with the name: {anime_name}")
        anime_name = input("Please enter the name of the anime you want to download: ")
        anime_list = fetch_results(anime_name)
        
    
    anime = list_menu_selector("Select the anime you want to download:", [a['name'] for a in anime_list])
    url = next(a['href'] for a in anime_list if a['name'] == anime)
    range = next(a['range'] for a in anime_list if a['name'] == anime)
    return anime, url.rstrip(re.findall("[0-9]+", url)[-1]), range

def download_episode(driver: Chrome, download_page_link: str, episode_number: int) -> bool:
    """
    Downloads the episode from the download page link

    Args:
        driver: The selenium webdriver instance
        download_page_link: The download page link
        episode_number: The episode number

    Returns:
        bool: True if the episode was downloaded successfully, False otherwise
    """
    driver.get(download_page_link)
    WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.CLASS_NAME, 'mirror_link')))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    link_download_section = soup.find('div', class_='mirror_link')
    links = link_download_section.find_all('div')

    for link_div in reversed(links):
            clear_undownloaded_files(current_download_directory)
            download_link_tag = link_div.find('a')
            if download_link_tag and 'href' in download_link_tag.attrs:
                download_link = download_link_tag['href']
                download_element = driver.find_element(By.XPATH, f'//a[@href="{download_link}"]')
                try:
                    driver.execute_script("arguments[0].click();", download_element)
                    time.sleep(2)
                    files = os.listdir(current_download_directory)
                    # download did not start
                    if ".crdownload" not in "".join(files):
                        if len(driver.window_handles) == 2:
                                driver.switch_to.window(driver.window_handles[1])
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                        raise InvalidLinkError(f"Invalid download link for episode {episode_number}: {download_link}")
                except InvalidLinkError as e:
                    print(f"Error: {e}")
                    if link_div != links[0]:
                            print(f"Retrying download with another link...")
                            driver.get(download_page_link)
                            WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.CLASS_NAME, 'mirror_link')))
                            continue
                    else:
                        return False
                file_size = get_file_size(download_link)
                file_path = os.path.join(current_download_directory, next(f for f in files if f.endswith(".crdownload")))
                quality_match = re.search(r'[SD0-9]{2,4}P', download_link_tag.text[11:].strip())
                quality = quality_match.group(0) if quality_match else "Unknown"
                print(f"Downloading episode {episode_number}, Quality: {quality}")
                download_state = manage_download(driver, current_download_directory, file_path, file_size, True if link_div == links[0] else False)
                if download_state == DownloadState.SKIPPED:
                    driver.get(download_page_link)
                    WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.CLASS_NAME, 'mirror_link')))
                else:
                    return download_state

def download_episodes(url: str, episode_list: list):
    """
    Downloads the episodes from the episode list. Fetches title (and episode id) from the first episode in the list
    and uses it for the rest of the episodes, since title is fixed. Then automatically downloads by finding id
    of other episodes.

    Args:
        url: The base url of the anime
        episode_list: The list of episodes to download
    """
    response = requests.get(f"{url}{episode_list[0]}")
    soup = BeautifulSoup(response.text, 'html.parser')
    videosource_link = soup.find_all('iframe')

    if not videosource_link:
        print(f"Cannot find download link for episode {episode_list[0]}!")
        return

    title = f"&{re.findall('title=[A-Za-z+]*', str(videosource_link[0]))[0]}"

    driver = setup_driver(current_download_directory)
    
    for current_episode in episode_list:
        if current_episode != episode_list[0]:
            response = requests.get(f"{url}{current_episode}")
            soup = BeautifulSoup(response.text, 'html.parser')
            videosource_link = soup.find_all('iframe')
    
        
        episode_id = re.findall("id=[0-9A-Za-z]*", str(videosource_link[0]))[0]

        download_page_link = f"{BASE_URL}/download?{episode_id}{title}{current_episode}&typesub={EPISODE_TYPE}"

        successful = download_episode(driver, download_page_link, current_episode)
        
        if successful == DownloadState.SUCCESS:
            print(f"Successfully downloaded episode {current_episode}!")
        elif successful == DownloadState.FAILED:
            print(f"Error! Cannot download episode {current_episode}")
        
    driver.quit()
    print("All episodes downloaded!")

if __name__ == "__main__":
    continue_download = True

    while continue_download:
        anime_name, url, episode_range = get_anime()
        url = f"{BASE_URL}/{url}"
        if any(char in anime_name for char in INVALID_FILENAME_CHARS):
            for char in INVALID_FILENAME_CHARS:
                anime_name = anime_name.replace(char, '')
        os.makedirs(os.path.join(DOWNLOAD_DIRECTORY, anime_name), exist_ok=True)
        current_download_directory = os.path.join(DOWNLOAD_DIRECTORY, anime_name)
        print(f"Range of episodes: 1 - {episode_range}")

        if episode_range == '1':
            print("Only 1 episode found. Downloading episode 1...")
            download_episodes(url, [1])
        else:
            download_option = list_menu_selector("Select the number of episodes you want to download:", [
                'All - From episode 1 until final episode',
                'm - Episode m',
                'm,n - From episode m to n (m <= n)',
                'm,-1 - From episode m to final',
                'm,n,o..... - Episodes m, n, o, ....',
            ])

            if download_option.startswith('All'):
                download_episodes(url, list(range(1, int(episode_range) + 1)))
            elif download_option.startswith('m,n,o'):
                episodes = input("Enter the episode numbers separated by commas: ")
                episodes = list(map(int, episodes.split(',')))
                while any(episode > int(episode_range) or episode < 1 for episode in episodes):
                    print(f"Invalid episode number! The range is 1 - {episode_range}.")
                    episodes = input("Enter the episode numbers separated by commas: ")
                    episodes = list(map(int, episodes.split(',')))
                download_episodes(url, episodes)
            elif download_option.startswith('m,n'):
                m = int(input("Enter the starting episode number (m): "))
                while m > int(episode_range) or m < 1:
                    print(f"Invalid episode number! The range is 1 - {episode_range}.")
                    m = int(input("Enter the starting episode number (m): "))
                if m == int(episode_range):
                    download_episodes(url, [m])
                    continue
                else:
                    n = int(input("Enter the ending episode number (n): "))
                    while n > int(episode_range) or n < m:
                        if n < m:
                            print("Ending episode number should be greater than or equal to the starting episode number.")
                        else:
                            print(f"Invalid episode number! The range is 1 - {episode_range}.")
                        n = int(input("Enter the ending episode number (n): "))
                    download_episodes(url, list(range(m, n + 1)))
            elif download_option.startswith('m,-1'):
                m = int(input("Enter the starting episode number (m): "))
                while m > int(episode_range) or m < 1:
                    print(f"Invalid episode number! The range is 1 - {episode_range}.")
                    m = int(input("Enter the starting episode number (m): "))
                download_episodes(url, list(range(m, int(episode_range) + 1)))
            elif download_option.startswith('m'):
                m = int(input("Enter the episode number (m): "))
                while m > int(episode_range) or m < 1:
                    print(f"Invalid episode number! The range is 1 - {episode_range}.")
                    m = int(input("Enter the episode number (m): "))
                download_episodes(url, [m])
            elif download_option.startswith('1'):
                download_episodes(url, [1])
            
        continue_download = input("Do you want to download another anime? (y/n): ").lower() == 'y'
