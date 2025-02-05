import os
import sys
import time
import re
import threading
import msvcrt
from enum import Enum

import requests
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup

from exceptions import InvalidLinkError
from utils.file_utils import clear_undownloaded_files, get_file_size
from utils.animation_utils import with_loading_animation
from utils.driver_utils import setup_driver
from config import BASE_URL, EPISODE_TYPE

class DownloadState(Enum):
    SUCCESS = "success"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    FAILED = "failed"

def download_episode(driver: Chrome, download_page_link: str, episode_number: int, download_directory: str) -> bool:
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
            clear_undownloaded_files(download_directory)
            download_link_tag = link_div.find('a')
            if download_link_tag and 'href' in download_link_tag.attrs:
                download_link = download_link_tag['href']
                download_element = driver.find_element(By.XPATH, f'//a[@href="{download_link}"]')
                try:
                    driver.execute_script("arguments[0].click();", download_element)
                    time.sleep(2)
                    files = os.listdir(download_directory)
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
                file_path = os.path.join(download_directory, next(f for f in files if f.endswith(".crdownload")))
                quality_match = re.search(r'[SD0-9]{2,4}P', download_link_tag.text[11:].strip())
                quality = quality_match.group(0) if quality_match else "Unknown"
                print(f"Downloading episode {episode_number}, Quality: {quality}")
                download_state = manage_download(driver, download_directory, file_path, file_size, True if link_div == links[0] else False)
                if download_state == DownloadState.SKIPPED:
                    driver.get(download_page_link)
                    WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.CLASS_NAME, 'mirror_link')))
                else:
                    return download_state

def download_episodes(url: str, episode_list: list, download_directory: str) -> None:
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

    driver = setup_driver(download_directory)
    
    for current_episode in episode_list:
        if current_episode != episode_list[0]:
            response = requests.get(f"{url}{current_episode}")
            soup = BeautifulSoup(response.text, 'html.parser')
            videosource_link = soup.find_all('iframe')
    
        
        episode_id = re.findall("id=[0-9A-Za-z]*", str(videosource_link[0]))[0]

        download_page_link = f"{BASE_URL}/download?{episode_id}{title}{current_episode}&typesub={EPISODE_TYPE}"

        successful = download_episode(driver, download_page_link, current_episode, download_directory)
        
        if successful == DownloadState.SUCCESS:
            print(f"Successfully downloaded episode {current_episode}!")
        elif successful == DownloadState.FAILED:
            print(f"Error! Cannot download episode {current_episode}")
        
    driver.quit()
    print("All episodes downloaded!")


global progress_data
progress_data = {'progress': 0.0, 'progress_size': 0.0, 'file_size': 0.0}
@with_loading_animation(lambda: f"{progress_data['progress']:.1f}% downloaded, {progress_data['progress_size']:.2f}MB/{progress_data['file_size']:.2f}MB")
def track_download(download_directory: str, file_path: str, file_size: float, stop_event: threading.Event, download_completed_event: threading.Event, resume_event: threading.Event):
    """
    Track the download progress of a file in the download directory.

    Args:
        download_directory: The directory where downloads are saved.
        file_path: The path to the downloading file.
        file_size: The expected final size of the file being downloaded in MB.
        stop_event: An event to stop the download tracking.
        download_completed_event: An event to signal the download completion.
        resume_event: An event to pause the download tracking.

    """
    progress_data['file_size'] = file_size
    total_time = 0
    files = os.listdir(download_directory)
    while ".crdownload" in "".join(files):
        resume_event.wait() # Wait if resume_event is cleared
        if stop_event.is_set():
            break  # Exit if stop_event is set
        progress_data['progress_size'] = os.path.getsize(file_path) / 1024 / 1024
        progress_data['progress'] = progress_data['progress_size'] * 100 / file_size

        total_time += 0.1
        time.sleep(0.1)

        files = os.listdir(download_directory)
    if ".crdownload" not in "".join(files):
        download_completed_event.set()
    print()

def manage_download(driver: Chrome, download_directory: str, file_path: str, file_size: float, last_link: bool = False) -> bool:
    """
    Manages the download process by starting the download tracking thread and input monitoring thread.
    
    Args:
        driver: The Selenium WebDriver instance.
        download_directory: The directory where downloads are saved.
        file_path: The path to the downloading file.
        file_size: The expected final size of the file being downloaded in MB.

    Returns:
        bool: True if download completed successfully, False if skipped.
    """
    stop_event = threading.Event()
    resume_event = threading.Event()
    download_completed = threading.Event()

    resume_event.set()
    def monitor_input(q_result: list):
        """
        Monitor the keyboard input to pause the download and prompt the user for confirmation.
        """
        while not stop_event.is_set() and not download_completed.is_set():
            if msvcrt.kbhit():
                msvcrt.getch()  # Consume the key press
                
                # signal to pause the download tracking
                resume_event.clear()

                # pause the download
                driver.get("chrome://downloads/")
                driver.execute_script("document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector(\"button[id='pause-or-resume']\").click()")

                def ask_confirmation():
                    """
                    Prompt the user for confirmation to skip or cancel the current episode.

                    Args:
                        q_result: A list to store the user's response ('s' or 'c').
                    """
                    if last_link:
                        sys.stdout.write("\nThis is the last quality. Pressing s or c will cancel the download: ")
                    else:
                        sys.stdout.write("\nPress 's' to skip this quality or 'c' to cancel this episode: ")
                    sys.stdout.flush()
                    while True:
                        if msvcrt.kbhit():
                            key = msvcrt.getch().decode().lower()
                            if key in ('s', 'c'):
                                q_result.append(key)
                                break

                prompt_thread = threading.Thread(target=ask_confirmation)
                prompt_thread.start()
                prompt_thread.join(timeout=10)  # 10-second timeout

                if prompt_thread.is_alive():
                    # Timeout occurred - resume the download
                    sys.stdout.write(f"\nTimeout occurred. Resuming download...\n")
                    sys.stdout.flush()
                    resume_event.set()
                    driver.execute_script("document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector(\"button[id='pause-or-resume']\").click()")
                    continue

                if q_result:
                    driver.execute_script("document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector(\"button[id='cancel']\").click()")
                    resume_event.set()
                    stop_event.set()
                    if q_result[-1] == 's':
                        # Skip the download using Selenium
                        sys.stdout.write(f"\nCancelling download...\n") if last_link else sys.stdout.write(f"\nSkipping quality...\n")
                        sys.stdout.flush()
                        q_result.append(DownloadState.SKIPPED)
                    elif q_result[-1] == 'c':
                        # Cancel the download using Selenium
                        sys.stdout.write(f"\nCancelling download...\n")
                        sys.stdout.flush()
                        q_result.append(DownloadState.CANCELLED)
                    return

                else:
                    # Resume the download
                    sys.stdout.write(f"\nResuming download...{" "*100}\n")
                    sys.stdout.flush()
                    resume_event.set()
                    driver.execute_script("document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector(\"button[id='pause-or-resume']\").click()")
                    
            time.sleep(0.1)  # Prevent CPU overuse

    # Start the download tracking thread
    download_thread = threading.Thread(
        target=track_download, 
        args=(download_directory, file_path, file_size), 
        kwargs={
            'stop_event': stop_event, 
            'download_completed_event': download_completed, 
            'resume_event': resume_event
        }, 
        daemon=True
    )
    download_thread.start()
    q_result = []
    # Start the input monitoring thread
    input_thread = threading.Thread(target=monitor_input, args=(q_result,), daemon=True)
    input_thread.start()

    # Wait for the download thread to complete
    download_thread.join()

    # Ensure input_thread stops if it's waiting
    stop_event.set()
    resume_event.set()
    input_thread.join()
    if download_completed.is_set():
        return DownloadState.SUCCESS
    return q_result[-1] if q_result else DownloadState.FAILED