import os
from PyInquirer import prompt

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
