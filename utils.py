import os, threading, sys, time
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