# Pusher

Essentially, specify a folder to be automatically backed up to Google Drive.

The tool will **watch** folders specified using the `watch` command and upload files currently in the folder and any new file added.

## How to use

1. Use the `sign-in` command to allow access to Google Drive
2. Provide some folders to watch using the `watch` command
3. Use the `start` command to begin watching specified folders (will continue running in background)

## Commands


## Notes

- Tool supports only Linux systems
- Only files, directly in the specified folders and all sub-folders, are uploaded
- That is, upload does not retain file path
- All files from all folders being watched are placed as is, in a folder in your Google Drive (PusherUploads)
- Once created, the PusherUploads folder can be renamed or moved around to your origanizational preference (but not deleted)
- If the PusherUploads folder is deleted, for the tool to upload new content, it will re-create the PusherUploads folder

## Technical

watchdog.observers.Observer [only works](https://pythonhosted.org/watchdog/api.html#module-watchdog.observers) for Linux systems. Until other systems need to be supported, it should work just fine.

---

### TO-DO

The list below as well as in-line code

- [] Put watlist.json, queue.json and config.json into one file
- [] Provide instructions on creating client_secrets.json on Cloud Console
- [] Add more descriptive logging, and command to read logs


### Progress

- [x] Provide the list of directories to watch from a file.
- [x] Include a command to add new directories: `pusher watch .`
- [X] When new files or folders are added to these folders, upload them to Google Drive
- [X] If internet connection is not available, create a schedule of files that failed to upload. User will have to manually push changes
- [] Script will run in the background..
- [] Package script for pypi (or just make it installable)
