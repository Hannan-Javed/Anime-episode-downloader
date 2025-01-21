# Anime-episode-downloader
This is the python implementation of downloading anime episodes from the website https://s3embtaku.pro/ automatically using selenium, which is a python libary used to simulate chrome.<br>
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
2. Number of episodes: Input how many episodes do you want to download. The options are:
    - All - From episode 1 until final episode
    - m - Episode m
    - m,n - From episode m to n (m <= n)
    - m,-1 - From episode m to final
    - m,n,o..... - episode m, n, o, ....

After entering, the download(s) will automatically start starting from the highest quality, and lowering down in case of error; error being the that specific **link does not work**.<br>
You can manually skip that specific quality download and move to lower quality if it is taking too long. To do it, press any key while it is downloading, then press **y** within **10 seconds** when prompted. If you press any other key or 10 seconds pass, the download resumes downloading again.<br>
You can change these configurations inside `config.py`:
- `SUB` or `DUB`
- Download folder. Use `get_default_download_directory()` to get the default location.
## Note
1. Dubbed anime will not show up in the list. Change to `DUB` inside `config.py` to download dubbed version.
1. Closing the opened chrome tab will terminate the program
2. The script can download same episodes multiple times
3. If there is an authentication issue, open chrome and manually authenticate it once. Afterwards there should be no issue in downloading episodes automatically.