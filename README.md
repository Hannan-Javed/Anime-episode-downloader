# Anime-episode-downloader
This is the python implementation of downloading anime episodes from the website https://goone.pro automatically using selenium, which is a python libary used to simulate chrome.
The episodes are downloaded in the download folder.
## Installation
First download the required packages
```shell
pip install -r requirements.txt
```
## Requirements 
Make sure that you are not downloading any other file in the download folder
## Run
Run `main.py` and input two things:
1. url: Go to the website https://goone.pro and search for the anime you want to download. Go to the **first episode** of that anime and copy the URL, and paste it in the terminal.
2. Number of episodes: Input how many episodes do you want to download. The format is:
m - From episode 1 until episode m
m,n - From episode m to n (m < n)
m,-1 - From episode m to final
All - From episode 1 until final episode

After inputting and clicking enter, the downloading will automatically start and it will try to download from the highest quality. If theres an error in the link, it will try the lower quality links if they work. Episode will not be downloaded if it takes longer than **Two and a half minutes** to download or **No links work**.
If you want to skip downloading an episode, just close the opened chrome tab and click "exit" when prompted - this will delete the undownloaded file.
## Note
### Running this will delete any undownloaded (.crdownload) files in the downloads folder
