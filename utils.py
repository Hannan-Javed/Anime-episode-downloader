import os, threading, sys, time, requests
from PyInquirer import prompt
from functools import wraps

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
        print(content_length)
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

def loading_animation(message, stop_event):
    while not stop_event.is_set():
        for dots in range(4):  # 0 to 3 dots
            sys.stdout.write("\r" + message + " " * 4) # clear previous dots
            sys.stdout.flush()
            sys.stdout.write("\r" + message + "." * dots)
            sys.stdout.flush()
            time.sleep(0.5)
    print()

def with_loading_animation(message):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            stop_event = threading.Event()
            animation_thread = threading.Thread(target=loading_animation, args=(message, stop_event), daemon=True)
            animation_thread.start()
            try:
                return func(*args, **kwargs)
            finally:
                stop_event.set()
                animation_thread.join()
        return wrapper  
    return decorator