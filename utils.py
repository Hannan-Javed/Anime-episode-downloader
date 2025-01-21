import os, threading, sys, time, requests, msvcrt, inspect
from PyInquirer import prompt
from functools import wraps
from typing import Callable
from selenium.webdriver import Chrome

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

from config import DOWNLOAD_DIRECTORY

def get_file_size(url):
        response = requests.head(url, allow_redirects=True)
        content_length = response.headers.get('Content-Length')
        if content_length is None:
            return 0.0
        return float(content_length) / (1024 * 1024)  # Convert bytes to MB

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
        
def clear_undownloaded_files(download_directory):
    # get all the files
    file_list = os.listdir(download_directory)

    # Iterate over the files and delete .crdownload files
    for file_name in file_list:
        if file_name.endswith(".crdownload"):
            file_path = os.path.join(download_directory, file_name)
            os.remove(file_path)

def loading_animation(message_func: Callable[[], str], stop_event: threading.Event, resume_event: threading.Event):
    spinner = ['|', '/', '-', '\\']
    spinner_index = 0
    while not stop_event.is_set():
        resume_event.wait()
        message = message_func()
        sys.stdout.write(f"\r{message} {spinner[spinner_index]}")
        sys.stdout.flush()
        spinner_index = (spinner_index + 1) % len(spinner)
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * (len(message_func()) + 2) + "\r")
    sys.stdout.flush()

def with_loading_animation(message_func: Callable[[], str]):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Inspect the function's signature
            sig = inspect.signature(func)
            parameters = sig.parameters
            if 'stop_event' in parameters:
                stop_event = kwargs.get('stop_event')
            else:
                stop_event = threading.Event()
            if 'resume_event' in parameters:
                resume_event = kwargs.get('resume_event')
            else:
                stop_event = threading.Event()
                resume_event = threading.Event()
            animation_thread = threading.Thread(
                target=loading_animation, 
                args=(message_func, stop_event, resume_event), 
                daemon=True
            )
            animation_thread.start()
            try:
                return func(*args, **kwargs)
            finally:
                stop_event.set()
                resume_event.set()
                animation_thread.join()
        return wrapper
    return decorator

global progress_data
progress_data = {'progress': 0.0, 'progress_size': 0.0, 'file_size': 0.0}
@with_loading_animation(lambda: f"{progress_data['progress']:.1f}% downloaded, {progress_data['progress_size']:.2f}MB/{progress_data['file_size']:.2f}MB")
def track_download(download_directory, file_path, file_size, stop_event, download_completed_event, resume_event):
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
    print()

def manage_download(driver: Chrome, download_directory, file_path, file_size):
 
    stop_event = threading.Event()
    resume_event = threading.Event()
    download_completed = threading.Event()

    resume_event.set()
    def monitor_input():
        while not stop_event.is_set() and not download_completed.is_set():
            if msvcrt.kbhit():
                msvcrt.getch()  # Consume the key press
                
                # signal to pause the download tracking
                resume_event.clear()

                # pause the download
                driver.get("chrome://downloads/")
                driver.execute_script("document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector(\"button[id='pause-or-resume']\").click()")

                def ask_confirmation(q_result):
                    sys.stdout.write("\nDo you want to cancel the download? (y/n): ")
                    sys.stdout.flush()
                    while True:
                        if msvcrt.kbhit():
                            key = msvcrt.getch().decode().lower()
                            q_result.append(key == 'y')
                            break

                q_result = []
                prompt_thread = threading.Thread(target=ask_confirmation, args=(q_result,))
                prompt_thread.start()
                prompt_thread.join(timeout=10)  # 10-second timeout

                if prompt_thread.is_alive():
                    # Timeout occurred - resume the download
                    sys.stdout.write(f"\nTimeout occurred. Resuming download...\n")
                    sys.stdout.flush()
                    resume_event.set()
                    driver.execute_script("document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector(\"button[id='pause-or-resume']\").click()")
                    continue

                if q_result and q_result[0]:
                    # Cancel the download using Selenium
                    sys.stdout.write(f"\nCancelling download...\n")
                    sys.stdout.flush()
                    driver.execute_script("document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector(\"button[id='cancel']\").click()")
                    resume_event.set()
                    stop_event.set()
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

    # Start the input monitoring thread
    input_thread = threading.Thread(target=monitor_input, daemon=True)
    input_thread.start()

    # Wait for the download thread to complete
    download_thread.join()

    # Ensure input_thread stops if it's waiting
    stop_event.set()
    resume_event.set()
    input_thread.join()
    
    if not download_completed.is_set():
        return False
    return True