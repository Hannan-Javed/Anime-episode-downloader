# Anime-episode-downloader
This is the python implementation of downloading anime episodes from the website https://s3taku.com automatically using selenium, which is a python libary used to simulate chrome.
The episodes are downloaded in the download folder.
## Installation
Clone the repository:
```
git clone https://github.com/Hannan-Javed/Anime-episode-downloader
```
Then download the required packages
```shell
pip install -r requirements.txt
```
## Requirements 
Make sure that you are not downloading any other file in the download folder
## Run
Run `main.py` and input two things:
1. url: Go to the website https://s3taku.com and search for the anime you want to download. Go to the **first episode** of that anime and copy the URL, and paste it in the terminal.
2. Number of episodes: Input how many episodes do you want to download. The format is:
    - `all` - From episode 1 until final episode
    - `m` - Episode m
    - `m,n` - From episode m to n (m <= n)
    - `m,-1` - From episode m to final
    - `m,n,o.....` - episode m, n, o, ....
    - Can just enter `1` if its a movie

After inputting and clicking enter, the downloading will automatically start and it will try to download from the highest quality. If theres an error in the link, it will try the lower quality links if they work. Episode will not be downloaded if it takes longer than **two and a half minutes** to download or **no links work**.
By default it will download english subbed episodes. To change these, modify line 9 and 11.
## Note
1. Running this will delete any undownloaded (.crdownload) files in the downloads folder
2. Closing the opened chrome tab will terminate the program
3. The script can download same episodes multiple times