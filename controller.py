
import time
import json
import logging
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


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
DIRS_WATCHED = set()


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

    import random
    print(f'uploading {path}')
    time.sleep(6)
    if random.choice((True, False)):
        return True
    else:
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


class WatchListHandler(FileSystemEventHandler):
    """Handle modifications to the watchlist.json file."""

    @staticmethod
    def on_modified(event):
        logger.info('Reloading watchlist.json')
        load_watchlist()

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


if __name__ == '__main__':
    watcher = Watcher()

    load_watchlist()
    watcher.run()
