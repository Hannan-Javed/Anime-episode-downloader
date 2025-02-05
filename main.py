import os

from utils.anime_list_utils import get_anime
from utils.menu_utils import list_menu_selector
from utils.download_manager import download_episodes
from config import BASE_URL, DOWNLOAD_DIRECTORY, INVALID_FILENAME_CHARS

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
            download_episodes(url, [1], current_download_directory)
        else:
            download_option = list_menu_selector("Select the number of episodes you want to download:", [
                'All - From episode 1 until final episode',
                'm - Episode m',
                'm,n - From episode m to n (m <= n)',
                'm,-1 - From episode m to final',
                'm,n,o..... - Episodes m, n, o, ....',
            ])

            if download_option.startswith('All'):
                download_episodes(url, list(range(1, int(episode_range) + 1)), current_download_directory)
            elif download_option.startswith('m,n,o'):
                episodes = input("Enter the episode numbers separated by commas: ")
                episodes = list(map(int, episodes.split(',')))
                while any(episode > int(episode_range) or episode < 1 for episode in episodes):
                    print(f"Invalid episode number! The range is 1 - {episode_range}.")
                    episodes = input("Enter the episode numbers separated by commas: ")
                    episodes = list(map(int, episodes.split(',')))
                download_episodes(url, episodes, current_download_directory)
            elif download_option.startswith('m,n'):
                m = int(input("Enter the starting episode number (m): "))
                while m > int(episode_range) or m < 1:
                    print(f"Invalid episode number! The range is 1 - {episode_range}.")
                    m = int(input("Enter the starting episode number (m): "))
                if m == int(episode_range):
                    download_episodes(url, [m], current_download_directory)
                    continue
                else:
                    n = int(input("Enter the ending episode number (n): "))
                    while n > int(episode_range) or n < m:
                        if n < m:
                            print("Ending episode number should be greater than or equal to the starting episode number.")
                        else:
                            print(f"Invalid episode number! The range is 1 - {episode_range}.")
                        n = int(input("Enter the ending episode number (n): "))
                    download_episodes(url, list(range(m, n + 1)), current_download_directory)
            elif download_option.startswith('m,-1'):
                m = int(input("Enter the starting episode number (m): "))
                while m > int(episode_range) or m < 1:
                    print(f"Invalid episode number! The range is 1 - {episode_range}.")
                    m = int(input("Enter the starting episode number (m): "))
                download_episodes(url, list(range(m, int(episode_range) + 1)), current_download_directory)
            elif download_option.startswith('m'):
                m = int(input("Enter the episode number (m): "))
                while m > int(episode_range) or m < 1:
                    print(f"Invalid episode number! The range is 1 - {episode_range}.")
                    m = int(input("Enter the episode number (m): "))
                download_episodes(url, [m], current_download_directory)
            
        continue_download = input("Do you want to download another anime? (y/n): ").lower() == 'y'
