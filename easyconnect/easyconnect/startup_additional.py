# these methods are called at beginning and end of startup procedure
# they are included to facilitate future firmware updates without overwriting the wsgi.py
# this will decouple content hub updates from firmware updates

def begin():
    pass

def finalize():
    pass