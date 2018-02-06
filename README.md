# About
Tornado-based imageboard
### Current features:
1. Admin panel:
    Ability to create boards, view board stats, banned users, reports.
2. Admin features:
    Ability to delete posts and ban users
3. Posting features:
	Support of .jpg/jpeg, .png, .gif images and .webm and .mp4 videos.
    Spoiler thumbnails for images and videos;
	Filesize is limited to 5mb but can be changed in JS validator and imageboard settings.
    Maximum of one file per post.
    Ability to report posts.
# Requirements
python 3

mongodb

mediainfo
# How to run
```sh
$ pip install -r requirements.txt
$ sudo service mongod start
$ python board.py
```
