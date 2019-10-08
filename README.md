# About
Tornado-based imageboard
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

## Licensed under NFLv1  -  No  Faggots  License  Version  One 

Anyone may run, modify, distribute, sell or otherwise use  this software as they see fit with the understanding that it is provided without a warranty of any kind, so long  as they are heterosexual.  This license bans all homosexuals, bisexuals, transgenders,  and other assorted queers from  using  or interacting with  this software in any way.  Homosexuals may not run, modify, distribute, sell, fork,  or otherwise use  this code in any way.
