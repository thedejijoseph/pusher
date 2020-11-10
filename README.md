# Pusher

Watch given folders for changes and upload new files to Google Drive

- [x] Provide the list of directories to watch from a file.
- [x] Include a command to add new directories: `pusher watch .`
- [] When new files or folders are added to these folders, upload them to Google Drive
- [] If internet connection is not available, do nothing. User will have to manually push changes
- [] Script will run in the background..
- [] Package script for pypi

## Notes

watchdog.observers.Observer [only works](https://pythonhosted.org/watchdog/api.html#module-watchdog.observers) for Linux systems. Until other systems need to be supported, it should work just fine.

Supporting only files, not dirs, at this time
