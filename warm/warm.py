# ----------------------------------------------------------------------
#               Windy Keyboards Arduino Package Manager
# ----------------------------------------------------------------------
# This program is a simple package manager for a Windy Keyboards
# Arduino-based project. As the Windy organisation is entirely Github
# based, this package manager works exclusively through Github, and public
# repositories. For more information around the operation of Warm, see the 
# associated wiki pages.

from os import sys
import os

help_message = """
Usage: 
    warm up      - Updates the dependencies of the current project
"""

# We expect 2 - one for the name, one for the action to take
if len(sys.argv) < 2:
    print(help_message)
    quit()

action = None

if "-v" in sys.argv or "--verbose" in sys.argv:
    os.environ["WARM_VERBOSE_LOGGING"] = str(1)
else:
    os.environ["WARM_VERBOSE_LOGGING"] = str(0)

# Parse the actions
if sys.argv[1] == 'up':
    from up import Up
    action = Up()
elif sys.argv[1] == 'this':
    from this import This
    action = This()

# Run the action if not none, else print the help message
if action == None:
    print('Unknown argument: %s' % sys.argv[1])
    print(help_message)
else:
    action.run()








