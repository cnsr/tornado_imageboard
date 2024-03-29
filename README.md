# About
Tornado-based imageboard

[![State-of-the-art Shitcode](https://img.shields.io/static/v1?label=State-of-the-art&message=Shitcode&color=7B5804)](https://github.com/trekhleb/state-of-the-art-shitcode)

### Current features:
1. Admin panel features:
    * Creation, editing, delition and viewing stats of boards;
    * Ability to post as admin;
    * Ability to remove posts, ban and unban users;
    * Ability to view detailed logging history;
    * Ability to move threads to different board;
2. Highly configurable imageboardboard creation tool with ability to set:
    * default poster name and ability to allow custom usernames (tripcodes are supported);
    * board full and shortened names;
    * board specific settings:
        * number of posts in thread,
        * bumplimit,
        * amount of threads in catalog, 
        * amount of threads per page,
        * optional countryflags,
        * 300x100px banners,
        * optional dice rolls.
3. Posting features:
    * Support of:
        * .jpg/.jpeg, .png, .gif images,
        * .webm and .mp4 videos,
        * .mp3, .ogg, .wav audio;
    * Up to 20 MB filesize;
    * Spoiler thumbnails for images and videos;
    * Maximum of four files per post;
    * Ability to report posts;
    * Ability to remove your own posts.

# Requirements
* python 3.9+ (or go remove 3.9+ features lol)

   I intend to use whatever the latest version of stable python there is, 3.9.6 at the time I am writing this.
   Will do my best to update to 3.10 upon release.
* mongodb
* mediainfo
* ffmpeg
* imagemagick

Installing requirements on osx:
```shell
brew tap mongodb/brew
brew install mongodb-community
brew install imagemagick
brew install ffmpeg
brew install mediaifo
```
Shouldn't be much harder to do on a less disgusting OS, but I can't really choose atm.

FYI there might be issues with mongodb on osx Catalina+ - use [this fix](https://stackoverflow.com/a/61423909/12932611)

For development purposes, [poetry]() with [poetry-virtualenv]() are used.

# How to run
1. Install all software dependencies
2. Configure nginx - use example config
3. Install mongodb and make sure it is running
    ```sh
    $ sudo service mongod start
    ```
   For osx it's, as usual, retarded as fuck:
   1) run the commands from the aforementioned fix e.g.
      ```shell
      sudo chown -R $(whoami) /System/Volumes/Data/data/db
      ```
   2) don't forget to add this line to `.zshrc`:
      ```shell
      alias mongod="sudo mongod --dbpath /System/Volumes/Data/data/db"
      ```
   3) if you did the previous step, run the following command:
       ```shell
       $ mongod
       ```
   Yep, you can't have it as a service. Yes, what the wtf.
4. Install module dependencies and run
   
   Please, keep in mind that `requirements.txt` might be not up-to-date.
   
   * Using pip:
    ```sh
    $ pip install -r requirements.txt
    $ python src/board.py
    ```
   * Using poetry:
   ```sh
    $ poetry install
    $ poetry run python run.py
    ```

# TODO:
0. Fix UI
1. Wrap in Docker
2. Introduce external storage
3. Add Celery for periodic cleanup
4. Rewrite in Rust