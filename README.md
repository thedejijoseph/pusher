# Pusher

Watch given folders for changes and upload new files to Google Drive

- [x] Provide the list of directories to watch from a file.
- [x] Include a command to add new directories: `pusher watch .`
- [X] When new files or folders are added to these folders, upload them to Google Drive
- [X] If internet connection is not available, create a schedule of files that failed to upload. User will have to manually push changes
- [] Script will run in the background..
- [] Package script for pypi

## Notes

watchdog.observers.Observer [only works](https://pythonhosted.org/watchdog/api.html#module-watchdog.observers) for Linux systems. Until other systems need to be supported, it should work just fine.

Supporting only files, not dirs, at this time


After creating a folder in Drive, you should be able to rename or move it into a desired location.
Do not delete the folder. If you do, Pusher will just create another one in root (My Drive).


Install procedure
+ move pusher soure code to install directory
+ confirm that client_secrets.json exists
+ optionally, run tests


TODO:
Put watlist.json, queue.json and config.json into one file
Create tests for these scenarios:
    Google Drive: PusherUploads is renamed, moved, trashed, deleted forever
    Local: Files to be uploaded are moved, renamed, deleted or otherwise modified before upload is complete
    App: Handling internet connections issues, handling other errors, functionality of app commands
Provide step by step instructions for creating client_secrets.json on Cloud Console (with pictures)
Clear logs would be needed for inspection, since app is to be running in background