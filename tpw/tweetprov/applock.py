import fcntl, os, stat, tempfile

app_name = 'twitter_proven' # name to be used for the lock

# Establish lock file settings
lf_name = '.{}.lock'.format(app_name)
lf_path = os.path.join(tempfile.gettempdir(), lf_name)
lf_flags = os.O_WRONLY | os.O_CREAT
lf_mode = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH  # This is 0o222, i.e. 146

def getAppLock():
    # Create lock file
    # Regarding umask, see https://stackoverflow.com/a/15015748/832230
    umask_original = os.umask(0)
    try:
        lf_fd = os.open(lf_path, lf_flags, lf_mode)
    finally:
        os.umask(umask_original)

    # Try locking the file
    try:
        fcntl.lockf(lf_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lf_fd
    except IOError:
        return None