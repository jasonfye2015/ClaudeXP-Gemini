"""Where the archive is: the folders in the shared Local Storage that the archive tools read."""
from claudecore import host

FOLDERS = {"mediaarchive": "furry media archive", "tvmovies": "tv and movies",
           "miscimages": "misc personal image folders", "personaldocs": "personal text"}


def archive_folder(key):
    """The Local Storage folder for an archive ('mediaarchive', 'tvmovies'), or None if it isn't there."""
    prefix = FOLDERS[key]
    root = host.local_storage()
    if not root.is_dir():
        return None
    return next((d for d in sorted(root.iterdir()) if d.is_dir() and d.name.lower().startswith(prefix)), None)
