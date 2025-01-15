import os, threading, sys, time
from PyInquirer import prompt
from functools import wraps
from typing import Callable, Union

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

def with_loading_animation(message: Union[str, Callable[..., str]]):
    """
    Decorator to display a loading animation while the decorated function is running.
    
    Args:
        message (str or callable): The message to display. If callable, it should accept the same
                                   arguments as the decorated function and return a string.
    
    Returns:
        function: The decorated function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if callable(message):
                message_ = message(*args, **kwargs)
            else:
                message_ = message
            stop_event = threading.Event()
            animation_thread = threading.Thread(target=loading_animation, args=(message_, stop_event), daemon=True)
            animation_thread.start()
            try:
                result = func(*args, **kwargs)
            finally:
                stop_event.set()
                animation_thread.join()
            return result
        return wrapper
    return decorator