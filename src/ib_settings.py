import os
from dotenv import load_dotenv

load_dotenv()

# timeout to function that deletes inactive threads, in seconds
CHECK_TIMEOUT = int(os.getenv('INACTIVE_THREAD_TIMEOUT', 15))
ADMIN_PASS = os.getenv('ADMIN_PASSWORD', 'changeme')
PORT = int(os.getenv('PORT', 8000))
UPLOAD_ROOT = os.getenv('UPLOAD_ROOT', 'uploads')

# TODO: add the AMOUNT_OF_FIELDS variable
MAX_FILESIZE = 20971520 * 4 # filesize per field * amount of fields

# boards in which banned users are allowed to post
BAN_ALLOWED = ['bans',]
