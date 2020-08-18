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
        * .mp3, .ogg, .wav, .opus audio;
    * Up to 20 MB filesize;
    * Spoiler thumbnails for images and videos;
    * Maximum of four files per post;
    * Ability to report posts;
    * Ability to remove your own posts.
# Requirements
* python 3
* mongodb
* mediainfo
* ffmpeg
* imagemagick
# How to run
1. Install all software dependencies
2. Configure nginx - use example config, make sure mongo is running
    ```sh
    $ sudo service mongod start
    ```
3. Install module dependencies and run
    ```sh
    $ pip install -r requirements.txt
    $ python board.py
    ```
