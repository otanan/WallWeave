#!/usr/bin/env python3
"""Handles changing wallpapers.

**Author: Jonathan Delgado**

"""
#------------- Imports -------------#
import subprocess
#--- Custom imports ---#
#------------- Fields -------------#
#======================== Helper ========================#
def change_all_papers(img_path):
    """ Changes wallpapers on all screens. """
    # Convert to path format for Applescript
    path = str(img_path).replace('/', ':')
    script = f"""/usr/bin/osascript<<END
tell application "System Events"
    tell every desktop
        set picture rotation to 0
        set picture to "Macintosh HD{path}"
    end tell
end tell
END"""
    subprocess.run(script, shell=True)




#======================== Entry ========================#

def main():
    pass

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print('Keyboard interrupt.')