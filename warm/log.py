# Basic logging interface for printing to the terminal in colour

OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL    = '\033[91m'
ENDC    = '\033[0m'

def info(msg):
    print(msg)

def success(msg):
    print(OKGREEN + msg + ENDC)

def warn(msg):
    print(WARNING + msg + ENDC)

def fatal(msg):
    print(FAIL + msg + ENDC)
    quit()

def print_action_header(action_name):
    print("""
🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥
                Starting to warm {action_name}                
🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥
    """.format(action_name = action_name))