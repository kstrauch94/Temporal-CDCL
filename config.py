import os

def get_parent_dir(path):
    # this gets the name of the parent folder

    # if there is a trailing backslash then delete it
    if path.endswith("/"):
        path = path[:-1]

    return os.path.dirname(path)

FD_CALL = ["/home/klaus/bin/Fast-Downward/fast-downward.py", "--translate"]

FILE_PATH = os.path.abspath(__file__)

RUNSOLVER_PATH = os.path.join(get_parent_dir(FILE_PATH), "runsolver") 

PLASP = "plasp"