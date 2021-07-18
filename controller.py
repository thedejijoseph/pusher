
from util import *

def handle_command():
    """Calling this function looks up changes in the commands.txt
    file and executes if a valid command.

    Commands are picked sequentially. Successful commands are removed from
    commands.txt and commands-history.txt. If a command fails to excute, it is left
    in commands.txt. This means that commands are only retried when a new
    command is executed.

    This patch work is to enable communication between a single execution of a
    process running in the foreground and another continuously running in the background.
    """

    commands = COMMANDS_FILE.read_text().splitlines()
    # structure has been set up. will use if the need arises

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
        logger.info(f'watching: {_path}')
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
        logger.info(f'excluding: {_path}')
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
        logger.info(f'removed: {_path}')
    
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

    # setup call being removed from here.
    # assumption then is taken that at _startup_, all neccessary
    # setups have been made: loading watchlist and queue as well as
    # google drive set up
    q = _load_queue()['to_do']

    logger.info('uploading scheduled files')
    for path in q:
        uploaded = upload(path)
        if uploaded:
            unschedule(path)
            delete(path)

def collect():
    """Manually schedule files in target dirs for upload."""

    watching = _load_watchlist()['watch']
    q = _load_queue()['to_do']

    no_of_files = 0
    all_ = {}
    for target_dir in watching:
        if Path(target_dir).exists():
            if not all_.get(target_dir):
                all_[target_dir] = []
            files_in_dir = [path for path in Path(target_dir).iterdir() if path.is_file()]
            no_of_files += len(files_in_dir)
            all_[target_dir].extend(files_in_dir)
    
    if all_:
        for dir in all_:
            for file in all_[dir]:
                if str(file) not in q:
                    schedule(file)
    s = "" if no_of_files == 1 else "s"
    logger.info(f'collected {no_of_files} file{s} for upload')

def upload(path) -> bool:
    """Upload files/directories to Google Drive

    Method attempts to upload given path.
    If upload fails, retry three more times.
    If upload still fails, assume internet connectivity is unavailable
        and "schedule" path, ie add it to a queue to be pushed manually.
    
    Will return True if upload was successful, False if not.
    """

    # TODO: make provision for more nuanced error resolution/logging
    
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
        logger.info(f'uploaded: {path}')
        return True
    except pydrive2.files.ApiRequestError:
        # there's some issue with the parent folder id
        # most likely, PusherUploads was "Deleted Forever"
        create_parent_folder()
        return upload(path)
    except:
        # raise
        logger.error(f'upload fail: {path}')
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
    logger.info(f'scheduled: {path}')

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
        logger.info(f'unscheduled: {path}')

def delete(path) -> None:
    """File has been uploaded. Delete from the
    queue as well as from their current locations.
    """

    path = Path(path).resolve()
    if path.exists() and path.is_file():
        path.unlink()
        logger.info(f'deleted: {path}')

def add_auth():
    """Launches the authentication flow and saves access credentials.
    """
    if CREDS_FILE.exists():
        logger.info('Saved credentials are available')
        logger.info('Reset saved credentials with `reset-auth` before proceeding')
        return
    
    logger.info('A client_secrets.json file must be in the current directory')
    logger.info('Attempting to set up authentication')

    google_auth = GoogleAuth()
    try:
        google_auth.LocalWebserverAuth()
        google_auth.SaveCredentialsFile(CREDS_FILE)
    except Exception as e:
        logger.info('Fatal error occured while trying to establish authentication. Consult logs with command `logs`.')
        logger.debug(e)

def reset_auth():
    """Clear saved authentication credentials.
    """

    CREDS_FILE.unlink()

def start():
    """Call watcher.py into the background with nohup"""
    os.system("nohup python ./watcher.py &")
