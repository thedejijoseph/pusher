# Pusher

Automatically push files in a specified folders to Google Drive.

The tool will **watch** the folders specified using the `watch` command and upload new (or modified) files.

**Background**

I built this 'tool' cause I did not want to have to go through the 'hectic' process of new browser tab plus dragging and dropping. 🙂

I could *dump* files I intend to backup into a folder and leave upload to happen in the background.


## How to use

1. Use the `add-auth` command to allow access to Google Drive
2. Provide some folders to watch using the `watch` command
3. Use the `start` command to begin watching specified folders (will continue running in background)
4. Copy or move files into said folders and leave upload to happen in the background

## Commands


## Notes

- Tool supports only Linux systems
- Only files placed directly in the specified folders are uploaded. Sub-directories are not considered
- **Important!** Uploaded files are immediately deleted
- If upload fails, they are 'scheduled'. Upload is retried periodically (to-do), or you can manually push 'scheduled' files
- All files from all folders being watched are placed as is, in a folder in your Google Drive (PusherUploads). Path information is not retained (ie: ~/ToBackup/app.txt will appear as app.txt)
- Once created, the PusherUploads folder can be renamed or moved around to your origanizational preference (but not deleted)
- If the PusherUploads folder is deleted, for the tool to upload new content, it will re-create the PusherUploads folder

### Technical

- watchdog.observers.Observer [only works](https://pythonhosted.org/watchdog/api.html#module-watchdog.observers) for Linux systems. Until other systems need to be supported, it should work just fine.

---

### TO-DO

The list below as well as in-line code

- [] Put watchlist.json, queue.json and config.json into one file
- [] Provide instructions on creating client_secrets.json on Cloud Console
- [] Add more descriptive logging, and command to read logs
- [] Add periodical upload retry for scheduled files


### Progress

- [x] Provide the list of directories to watch from a file.
- [x] Include a command to add new directories: `pusher watch .`
- [X] When new files or folders are added to these folders, upload them to Google Drive
- [X] If internet connection is not available, create a schedule of files that failed to upload. User will have to manually push changes
- [] Script will run in the background..
- [] Package script for pypi (or just make it installable)
