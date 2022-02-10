import os
from tools.tools import get_parent_dir

# Path to the fast downward python call
FD_CALL = ["/Path/to/Fast-Downward/fast-downward.py", "--translate"]

FILE_PATH = os.path.abspath(__file__)

# Path to the runsolver binary (this works for a binary called "runsolver" that is the same directory)
RUNSOLVER_PATH = os.path.abspath(os.path.join(get_parent_dir(FILE_PATH), "runsolver"))

# Path to plasp call
PLASP = "plasp"
