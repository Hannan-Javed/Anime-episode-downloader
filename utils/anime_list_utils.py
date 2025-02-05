import re

import requests
from bs4 import BeautifulSoup

from utils.animation_utils import with_loading_animation
from utils.menu_utils import list_menu_selector
from config import BASE_URL


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

