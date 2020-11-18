
import os, sys
import time
import json
import logging
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import pydrive2
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

ROOT = Path(__file__).parent
WATCHLIST_FILE = ROOT.joinpath(Path('./watchlist.json')).resolve()
QUEUE_FILE = ROOT.joinpath(Path('./queue.json')).resolve()
CREDS_FILE = ROOT.joinpath('./client_secrets.json').resolve()
CONFIG_FILE = ROOT.joinpath('./config.json').resolve()
CREDS_FILE = ROOT.joinpath('./client_creds.json').resolve()

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

def load_watchlist():
    try:
        watchlist = _load_watchlist()
        for dir in watchlist['watch']:
            path = Path(dir).resolve()
            if path.is_dir() and str(path) not in [watch.path for watch in DIRS_WATCHED]:
                _watch = watcher.observer.schedule(TargetDirHandler(), path)
                DIRS_WATCHED.add(_watch)
        
        for dir in watchlist['exclude']:
            path = Path(dir).resolve()
            if path.is_dir() and str(path) in [watch.path for watch in DIRS_WATCHED]:
                _watch = [watch for watch in DIRS_WATCHED if watch.path == str(path)][0]
                watcher.observer.unschedule(_watch)
                DIRS_WATCHED.remove(_watch)
    except:
        logger.error(f'Error loading watchlist at {WATCHLIST_FILE}')

def watch(*paths):
    """Add directories to the watchlist.
    Relative and absolute paths are allowed.
    """

    watchlist = _load_watchlist()
    # remove paths from exclude, if exists
    # add to watch if it does not exist
    for path in paths:
        _path = str(Path(path).resolve())
        if _path in watchlist['exclude']:
            watchlist['exclude'].remove(_path)
        watchlist['watch'].append(_path)
    
    # remove duplicates
    watchlist['watch'] = list(set(watchlist['watch']))
    # rewrite list to file
    WATCHLIST_FILE.write_text(json.dumps(watchlist))
    
    # WatchListWatcher will pick changes up and load into memory

def exclude(*paths):
    """Exclude directories from being watched.
    """

    watchlist = _load_watchlist()
    # remove paths from watch, if exists
    # add to exclude if it does not exist
    for path in paths:
        _path = str(Path(path).resolve())
        if _path in watchlist['watch']:
            watchlist['watch'].remove(_path)
        watchlist['exclude'].append(_path)
    
    # remove duplicates
    watchlist['exclude'] = list(set(watchlist['exclude']))
    # rewrite list to file
    WATCHLIST_FILE.write_text(json.dumps(watchlist))
    
    # WatchListWatcher will pick changes up and load into memory

def remove(*paths):
    """Remove directories from watchlist.json.
    Does not stop watching a directory. Use `exclude`.
    """

    watchlist = _load_watchlist()
    for path in paths:
        # TODO: use list filters instead
        _path = str(Path(path).resolve())
        if _path in watchlist['watch']:
            watchlist['watch'].remove(_path)
        if _path in watchlist['exclude']:
            watchlist['exclude'].remove(_path)
    
    # rewrite list to file
    WATCHLIST_FILE.write_text(json.dumps(watchlist))

    # WatchListWatcher will pick changes up and load into memory

def watchlist():
    """Show watch and exclude lists.
    """
    
    watchlist = _load_watchlist()

    print('Watching:')
    if watching := watchlist['watch']:
        for dir in watching:
            print(f'\t{dir}')
    else:
        print('\tNone')
    
    print('Excluding:')
    if excluding := watchlist['exclude']:
        for dir in excluding:
            print(f'\t{dir}')
    else:
        print('\tNone')

def status():
    """Show upload/schedule status."""

    watching = _load_watchlist()['watch']
    q = _load_queue()['to_do']

    all_ = {}
    for target_dir in watching:
        if Path(target_dir).exists():
            if not all_.get(target_dir):
                all_[target_dir] = []
            files_in_dir = [path for path in Path(target_dir).iterdir() if path.is_file()]
            all_[target_dir].extend(files_in_dir)
    
    print('Scheduled for upload (run `push` to sync)')
    if all_:
        for dir in all_:
            print(f'\t{dir}')
            for file in all_[dir]:
                if str(file) in q:
                    print(f'\t\t{file}')
            print()

    print('Not scheduled for upload (run `collect` to schedule)')
    if all_:
        for dir in all_:
            print(f'\t{dir}')
            for file in all_[dir]:
                if str(file) not in q:
                    print(f'\t\t{file}')
            print()

def push():
    """Upload files in queue."""

    main(temp=True)
    q = _load_queue()['to_do']

    for path in q:
        uploaded = upload(path)
        if uploaded:
            unschedule(path)
            delete(path)

def collect():
    """Manually schedule files in target dirs for upload."""

    watching = _load_watchlist()['watch']
    q = _load_queue()['to_do']

    all_ = {}
    for target_dir in watching:
        if Path(target_dir).exists():
            if not all_.get(target_dir):
                all_[target_dir] = []
            files_in_dir = [path for path in Path(target_dir).iterdir() if path.is_file()]
            all_[target_dir].extend(files_in_dir)
    
    if all_:
        for dir in all_:
            for file in all_[dir]:
                if str(file) not in q:
                    schedule(file)

def upload(path) -> bool:
    """Upload files/directories to Google Drive

    Method attempts to upload given path.
    If upload fails, retry three more times.
    If upload still fails, assume internet connectivity is unavailable
        and "schedule" path, ie add it to a queue to be pushed manually.
    
    Will return True if upload was successful, False if not.
    """

    # TODO: make provision for more nuanced error resolution/logging
    # TODO: make async
    
    path = Path(path).resolve()
    try:
        file = drive.CreateFile({
            "title": path.name,
            "parents": [{
                "id": CONFIG['folder_id']
            }]
        })
        file.SetContentFile(path)
        file.Upload()
        return True
    except pydrive2.files.ApiRequestError:
        # there's some issue with the parent folder id
        # most likely, PusherUploads was "Deleted Forever"
        create_parent_folder()
        return upload(path)
    except:
        # raise
        return False

def schedule(path) -> None:
    """Add path to a queue of files to be uploaded.
    This queue is used by the manual `push` command.
    """

    q = _load_queue()
    path = str(Path(path).resolve()) # resolve paths
    to_do = set(q['to_do'])
    to_do.add(path)
    q['to_do'] = list(to_do) # ensure we don't have doubles
    QUEUE_FILE.write_text(json.dumps(q))

def unschedule(path) -> None:
    """Remove a path from the queue"""

    q = _load_queue()
    path = str(Path(path).resolve()) # making sure to resolve paths
    to_do = q['to_do']
    if path in to_do:
        to_do.remove(path)
        to_do = list(set(to_do)) # still ensuring no duplicates
        q['to_do'] = to_do
        QUEUE_FILE.write_text(json.dumps(q))

def delete(path) -> None:
    """File has been uploaded. Delete from the
    queue as well as from their current locations.
    """

    path = Path(path).resolve()
    if path.exists() and path.is_file():
        path.unlink()

def add_creds(path):
    """Add the client_secrets.json file.
    
    Provide the path to a valid JSON file containing credentials
    downloaded from your Google Cloud Console.
    Command will replace previously added creds file.
    """

    file = Path(path).resolve()
    
    if not CREDS_FILE.exists():
        CREDS_FILE.touch()
    
    CREDS_FILE.write_text(file.read_text())
    print('client_secrets.json file added successfully.')

def get_google_auth():
    """Create a connection to Google Drive
    To do this a client_secrets.json file must have been added.
    Authentication (client_creds.json) will be created via a LocalWebServer.
    If one already exists, it will be loaded from file."""\

    # TODO: need to allow for expiry and refresh of tokens

    global drive 

    google_auth = GoogleAuth()

    if not ROOT.joinpath(Path('./client_secrets.json')).exists():
        print('Error! client_secrets.json is not available')
        print('Run `add-creds --help` to get more information.')
        sys.exit()
    
    try:
        google_auth.LoadCredentialsFile(CREDS_FILE)
    except:
        google_auth.LocalWebserverAuth()
        google_auth.SaveCredentialsFile(CREDS_FILE)
    drive = GoogleDrive(google_auth)

def create_parent_folder():
    """Create a PusherUploads folder in the rot of My Drive"""

    file = drive.CreateFile({'title': 'PusherUploads'})
    file['mimeType'] = 'application/vnd.google-apps.folder'
    file.Upload()
    folder_id = file['id']
    update_config({'folder_id': folder_id})

class WatchListHandler(FileSystemEventHandler):
    """Handle modifications to the watchlist.json file."""

    @staticmethod
    def on_modified(event):
        logger.info('Reloading watchlist.json')
        load_watchlist()

class ConfigFileHandler(FileSystemEventHandler):
    """Handle modifications to the config.json file."""

    @staticmethod
    def on_modified(event):
        logger.info('Reloading config.json')
        _load_config()

class TargetDirHandler(FileSystemEventHandler):
    """Schedule and upload new additions to cloud.
    Scheduling involves queuing files for upload, retrying upon
    failure, and/or re-queuing for later (when internet connection
    is restored).
    """

    # handle only files in the root of the target dir, at this time
    # all handlers are unfortunately blocking, at this time
    
    @staticmethod
    def on_any_event(event):
        pass

    @staticmethod
    def on_created(event):
        # file is newly created in target dir or moved into target dir
        # upload and remove or schedule for manual push/sync later.. 
        # also raises a modified event, so handled there instead..
        pass
    
    @staticmethod
    def on_modified(event):
        # file created or modified in place (before upload/delete)
        # run upload anyway
        if not event.is_directory:
            uploaded = upload(event.src_path)
            if uploaded:
                delete(event.src_path)
            else:
                schedule(event.src_path)

    @staticmethod
    def on_moved(event):
        # if file is moved out of the target dir scope
        # (root to a sub dir, or to a parent/another dir),
        # file will no longer be considered for upload, unschedule
        # if file was only renamed, it will raise and be handled
        # by a modified event
        unschedule(event.src_path)
    
    @staticmethod
    def on_deleted(event):
        # file is deleted in place, simply unschedule
        # unsure of impact if file is deleted while upload is being
        # uploaded.. will be handled by the upload method anyways 
        unschedule(event.src_path)

class Watcher:
    """Watch given directories for changes."""

    def __init__(self):
        self.observer = Observer()

        _watch = self.observer.schedule(WatchListHandler(), WATCHLIST_FILE)
        DIRS_WATCHED.add(_watch)
        _config = self.observer.schedule(ConfigFileHandler(), CONFIG_FILE)
        DIRS_WATCHED.add(_config)

    def run(self):
        self.observer.start()
        try:
            while True:
                # 3 second intermittent pauses
                time.sleep(3)
        except:
            self.observer.stop()
            print()
            logger.info('Stopping watcher')
        
        self.observer.join()


def main(temp=False):
    """Run start-up checklist"""

    global watcher

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
    
    if not temp:
        watcher = Watcher()
        load_watchlist()
        logger.info('Starting watcher')
        watcher.run()


if __name__ == '__main__':
    main()
