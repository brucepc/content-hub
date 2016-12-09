import time
from threading import Timer

import os
from distutils.file_util import copy_file
from django.conf import settings

DATABASES = getattr(settings, 'DATABASES', None)
BACKUPDIR = getattr(settings, 'BACKUPDIR', None)
DATABASEPATH = DATABASES['default']['NAME']

def backup_database(resetTimer = True):
    if os.path.isfile(DATABASEPATH):
        # Create any intermediate directories that do not exist.
        # Note that there is a race between os.path.exists and os.makedirs:
        # if os.makedirs fails with EEXIST, the directory was created
        # concurrently, and we can continue normally. Refs #16082.
        if not os.path.exists(BACKUPDIR):
            try:
                os.makedirs(BACKUPDIR)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
        if not os.path.isdir(BACKUPDIR):
            raise IOError("%s exists and is not a directory." % BACKUPDIR)     
    
        dbname = os.path.basename(DATABASEPATH)
        backedupDatabase = os.path.join(BACKUPDIR, dbname);
        
        copy_file(src=DATABASEPATH, dst=backedupDatabase, update=1)

    if resetTimer:
        # Run the backup function every 2 mins
        Timer(120, backup_database, ()).start()

def restore_database(dbname):
    backedupDatabase = os.path.join(BACKUPDIR, dbname);
    if os.path.isfile(backedupDatabase):
        copy_file(src=backedupDatabase, dst=DATABASEPATH)
        return True
    return False

