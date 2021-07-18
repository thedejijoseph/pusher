
import os, sys
import time, json
import logging
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import pydrive2
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


ROOT = Path.home().joinpath('.config/pusher').resolve()
if not ROOT.exists():
    ROOT.mkdir()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

LOGS_FILE = ROOT.joinpath('logs')

console_formatter = logging.Formatter('%(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)

logfile_formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(filename)s/%(funcName)s:%(lineno)d - %(message)s')
logfile_handler = logging.FileHandler(LOGS_FILE)
logfile_handler.setLevel(logging.DEBUG)
logfile_handler.setFormatter(logfile_formatter)

logger.addHandler(console_handler)
logger.addHandler(logfile_handler)


WATCHLIST_FILE = ROOT.joinpath(Path('./watchlist.json')).resolve()
QUEUE_FILE = ROOT.joinpath(Path('./queue.json')).resolve()
CONFIG_FILE = ROOT.joinpath('./config.json').resolve()
CREDS_FILE = ROOT.joinpath('./auth_creds.json').resolve()
COMMANDS_FILE = ROOT.joinpath('./commands.txt').resolve()
HISTORY_FILE = ROOT.joinpath('./commands-history.txt').resolve()


DIRS_WATCHED = set()
CONFIG = {}


def _load_watchlist():
    EMPTY = {"watch": [], "exclude": []}
    try:
        if not WATCHLIST_FILE.exists():
            WATCHLIST_FILE.touch()
            WATCHLIST_FILE.write_text(json.dumps(EMPTY))
            return _load_watchlist()
        
        return json.loads(WATCHLIST_FILE.read_text())
    except:
        logger.error(f'Error loading watchlist at {WATCHLIST_FILE}')

def _load_queue():
    EMPTY = {"to_do": []}
    try:
        if not QUEUE_FILE.exists() or QUEUE_FILE.read_text() == '':
            QUEUE_FILE.touch()
            QUEUE_FILE.write_text(json.dumps(EMPTY))
            return _load_queue()

        return json.loads(QUEUE_FILE.read_text())
    except:
        logger.error(f'Error loading queue at {QUEUE_FILE}')

def _load_config():
    global CONFIG

    EMPTY = {"folder_id": ""}
    try:
        if not CONFIG_FILE.exists() or CONFIG_FILE.read_text() == "":
            CONFIG_FILE.touch()
            CONFIG_FILE.write_text(json.dumps(EMPTY))
            return _load_config()
        
        CONFIG = json.loads(CONFIG_FILE.read_text())
        return CONFIG
    except:
        logger.errorf=(f'Error loading config file at {CONFIG_FILE}')


def update_config(patch):
    
    assert type(patch) is dict

    config = _load_config()
    config.update(patch)
    CONFIG_FILE.write_text(json.dumps(config))

def get_google_auth():
    """Create a connection to Google Drive

    On first use, a client_secrets.json file must be placed in the current directory.
    If you need guidance on where to get the client_secrets.json file, run `auth-help`.
    
    Or consult project readme. Source: https://github.com/wrecodde/pusher#readme

    If authentication has been previously set up, authentication credentials would be loaded
    from saved file.
    """

    # TODO: need to allow for expiry and refresh of tokens

    global drive 

    google_auth = GoogleAuth()
    
    if CREDS_FILE.exists():
        try:
            google_auth.LoadCredentialsFile(CREDS_FILE)
        except:
            error_message = \
            "Error occured when attempting to use saved auth credentials. \n\
            Check your internet connection. If the error persists, clear saved credentials with `clear-auth`."
            logger.error(error_message)
    else:
        logger.info('Unavailable auth credentials. Allow access with the `add-auth` command.')
        sys.exit()
    
    drive = GoogleDrive(google_auth)

def create_parent_folder():
    """Create a PusherUploads folder in the rot of My Drive"""

    file = drive.CreateFile({'title': 'PusherUploads'})
    file['mimeType'] = 'application/vnd.google-apps.folder'
    file.Upload()
    folder_id = file['id']
    update_config({'folder_id': folder_id})

def setup():
    _load_watchlist()
    _load_queue()
    _load_config()
    get_google_auth()

    folder_id = CONFIG.get('folder_id', None)
    if not folder_id:
        # try getting the folder id of PusherUploads on Drive
        file_list = drive.ListFile({'q': "'root' in parents and mimeType='application/vnd.google-apps.folder'"}).GetList()
        for file in file_list:
            if file['title'] == 'PusherUploads':
                folder_id = file['id']
                update_config({'folder_id': folder_id})
                break
        # if not found, create one
        if not folder_id:
            create_parent_folder()
