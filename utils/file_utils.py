import os

import requests

def clear_undownloaded_files(download_directory: str) -> None:
    """
    Clear all the undownloaded files (e.g., ".crdownload") in the download directory.

    Args:
        download_directory: The path to the download directory.
    """
    for file_name in os.listdir(download_directory):
        if file_name.endswith(".crdownload"):
            file_path = os.path.join(download_directory, file_name)
            os.remove(file_path)


def get_default_download_directory() -> str:
    """
    Get the default download directory based on the operating system.

    Returns:
        str: The path to the default "Downloads" directory.
    """
    home_directory = os.path.expanduser("~")
    return os.path.join(home_directory, 'Downloads')

def get_file_size(url: str) -> float:
    """
    Get the file size of a URL by sending a HEAD request.

    Args:
        url: The URL of the file.
    
    Returns:
        float: The file size in MB.
    
    """
    response = requests.head(url, allow_redirects=True)
    content_length = response.headers.get('Content-Length')
    if content_length is None:
        return 0.0
    return float(content_length) / (1024 * 1024)  # Convert bytes to MB