import os

FD_CALL = ["/home/klaus/bin/Fast-Downward/fast-downward.py", "--translate"]

FILE_PATH = os.path.abspath(__file__)

RUNSOLVER_PATH = os.path.join(get_parent_dir(FILE_PATH), "runsolver") 
