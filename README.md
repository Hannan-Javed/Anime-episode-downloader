# Anime-episode-downloader
This is the python implementation of downloading anime episodes from the website https://s3embtaku.pro/ automatically using selenium, which is a python libary used to simulate chrome.<br>
The download destination can be changed, but by default the episodes are downloaded in the download directory. A new directory is created in this specified directory for each anime using its name where the episodes will be downloaded. For different animes different directories will be created.
## Installation
Clone the repository:
```
git clone https://github.com/Hannan-Javed/Anime-episode-downloader
```
Then download the required packages
```shell
pip install -r requirements.txt
```
## Run
Run `main.py`:
1. Enter the search key word for the anime you want to download and then select it from the menu. If no anime is in search result, you will be asked to enter search keyword again.
2. Number of episodes: Input how many episodes do you want to download. The format is:
    - `all` - From episode 1 until final episode
    - `m` - Episode m
    - `m,n` - From episode m to n (m <= n)
    - `m,-1` - From episode m to final
    - `m,n,o.....` - episode m, n, o, ....
    - Can just enter `1` if its a movie

After entering, the download(s) will automatically start starting from the highest quality, and lowering down in case of error; error being the episodes takes longer than **two and a half minutes** to download or that specific **link does not work**.<br>
By default it will download english subbed episodes, which can be changed to dub.
## Note
1. Closing the opened chrome tab will terminate the program
2. The script can download same episodes multiple times