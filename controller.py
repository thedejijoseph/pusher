
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


WATCHLIST_FILE = Path('./watchlist.json').resolve()
DIRS_TO_WATCH = set()


def _load_watchlist():
    EMPTY = {"watch": [], "exclude": []}
    try:
        if not WATCHLIST_FILE.exists():
            WATCHLIST_FILE.touch()
        
        content = WATCHLIST_FILE.read_text()
        if content == '':
            # if file is empty, write empty content and reload
            WATCHLIST_FILE.write_text(json.dumps(EMPTY))
            return _load_watchlist()
        
        watchlist = json.loads(content)
        return watchlist
    except:
        logger.error(f'Error loading watchlist at {WATCHLIST_FILE}')

def load_watchlist():
    try:
        watchlist = _load_watchlist()
        for dir in watchlist['watch']:
            path = Path(dir).resolve()
            if path.is_dir():
                DIRS_TO_WATCH.add(path)
        
        for dir in watchlist['exclude']:
            path = Path(dir).resolve()
            if path.is_dir():
                if path in DIRS_TO_WATCH:
                    DIRS_TO_WATCH.remove(path)
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

class WatchListHandler(FileSystemEventHandler):
    """Handle modifications to the watchlist.json file."""

    @staticmethod
    def on_modified(event):
        logger.info('Reloading watchlist.json')
        load_watchlist()
        print(DIRS_TO_WATCH)

class WatchListWatcher:
    """Watch the watchlist.json file for changes.
    Should  changes be made, use it to update the list of folders
    the main controller works with.
    """

    def __init__(self):
        self.observer = Observer()
    
    def run(self):
        event_handler = WatchListHandler()

        self.observer.schedule(event_handler, WATCHLIST_FILE)
        self.observer.start()
        try:
            while True:
                time.sleep(10)
        except:
            self.observer.stop()
            print()
            logger.info('Stopping controller.')
        
        self.observer.join()

if __name__ == '__main__':
    load_watchlist()
    w = WatchListWatcher()
    w.run()
