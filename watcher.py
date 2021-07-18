

from util import *

# directly import private methods
from util import _load_watchlist, _load_config, _load_queue

from controller import *


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

class CommandsHandler(FileSystemEventHandler):
    """Handle modifications to the commands.txt file."""

    @staticmethod
    def on_modified(event):
        logger.info('Handling new command')
        handle_command()

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
        _commands = self.observer.schedule(CommandsHandler(), COMMANDS_FILE)
        DIRS_WATCHED.add(_commands)

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

def stop():
    global watcher

    watcher.observer.stop()
    logger.info('Stopping watcher')

def start_watcher():
    global watcher

    setup()

    watcher = Watcher()
    load_watchlist()
    logger.info('Starting watcher')
    watcher.run()

if __name__ == "__main__":
    start_watcher()
