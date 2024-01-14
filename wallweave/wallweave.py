#!/usr/bin/env python3
"""macOS wallpaper manager.

**Author: Jonathan Delgado**

"""
#------------- Imports -------------#
from pathlib import Path
import random
import rumps # menu bar
import subprocess
from PIL import Image, ImageFilter, ImageDraw
from pillow_heif import register_heif_opener # working with heic
register_heif_opener() # necessary for HEIC files to work
import screeninfo # getting monitor information
from datetime import datetime # used for serializing temp paths
import os
os.nice(19) # Decrease the program's CPU priority
#--- Custom imports ---#
import image_extender
import paper_manager
#------------- Fields -------------#
__version__ = '0.0.0.3'
PAPERS_PATH = Path.home() / 'Drive/Wallpapers'
# temp folder inside of project directory
TEMP_FOLDER = Path(__file__).parent.parent / 'temp'

#======================== Helpers ========================#
def clear_temp_folder():
    """ Clears any files in the temp folder to avoid any accidentaly reusing. """
    print('Clearing temp folder...')
    for file in TEMP_FOLDER.iterdir():
        file.unlink()


def should_extend_img(img, monitor):
    """ Checks whether we should bother extending the image. Maybe the image is wide enough. """
    width_percentage = 0.9
    # The image is less than width_percentage% of the monitor width, extend it
    return img.size[0] < monitor.width * width_percentage


def serial():
    """ Generates a timestamp used for temporarily serializing a file down to the seconds. """
    return datetime.now().strftime("%I-%M-%S")


#======================== MenuBar ========================#
class WallWeave(object):
    def __init__(self):
        self.app = rumps.App('Wallpaper Manager')
        #--- Settings ---#
        self.playlists = self.get_playlists()
        self.blur_intensity = 20
        self.counter = 0
        self.history = []

        #--- Initialization ---#
        self.update_monitor()
        clear_temp_folder()
        self.set_up_menu()
        # Make the wallpaper change timer
        self.make_timer(5)


    def update_monitor(self):
        """ Gets the most relevant monitor information. """
        self.monitor = screeninfo.get_monitors()[0]


    def get_playlists(self):
        """ Get all available folders with images. """
        playlists = {
            f.name: {
                'name': f.name,
                'path': f
            }
            for f in PAPERS_PATH.iterdir()
            if not f.is_file()
        }
        playlists.update({'All': {'name': 'All', 'path': PAPERS_PATH}})
        return playlists


    def update_counter(self):
        self.counter += 1
        self.check_counter()


    def check_counter(self):
        """ Calls functions that should happen after a certain number of runs. """
        if self.counter % 10 == 9:
            # Clear the temp folder every 10th run
            clear_temp_folder()


    def make_timer(self, delay):
        # Kill any existing timers
        if hasattr(self, 'timer') and self.timer.is_alive():
            self.timer.stop()
            print('Killed timer.')

        self.timer = rumps.Timer(self.on_tick, delay)
        self.timer.start()


    def set_up_menu(self):
        self.app.title = 'WallWeave'
        #--- Delay Slider ---#
        slider_dimensions = (200, 30)
        # Slider for adjusting time delay of papers
        self.delay_slider = rumps.SliderMenuItem(
             value=5, min_value=5, max_value=605,
            dimensions=slider_dimensions, callback=self.on_slide
        )
        self.delay_slider._slider.setNumberOfTickMarks_(11)
        self.delay_slider._slider.setAllowsTickMarkValuesOnly_(True)

        self.slider_label = rumps.MenuItem(
            title=f'Delay: {int(self.delay_slider.value)}s'
        )

        #--- Blur Intensity Slider ---#
        # Slider for intensity of the blurring effect
        self.blur_slider = rumps.SliderMenuItem(
            value=self.blur_intensity, min_value=0, max_value=100,
            dimensions=slider_dimensions, callback=self.on_blur_slide
        )
        self.blur_slider._slider.setNumberOfTickMarks_(11)
        self.blur_slider._slider.setAllowsTickMarkValuesOnly_(True)

        # Set default label
        self.blur_slider_label = rumps.MenuItem(
            title=f'Blur Radius: {int(self.blur_slider.value)}.'
        )

        #--- Pause ---#
        self.toggle_pause_button = rumps.MenuItem(
            title='Pause', callback=self.toggle_pause
        )

        #--- Paper information ---#
        self.img_name = rumps.MenuItem(title='Name')
        self.resolution = rumps.MenuItem(title='Resolution: ')
        self.open_paper_button = rumps.MenuItem(
            title='Open Image', callback=lambda sender: self.open_paper(self.img_path)
        )

        #--- Playlists ---#
        self.playlist_buttons = {
            name: rumps.MenuItem(
                title=name,
                callback=lambda sender: self.change_playlist(sender.title)
            )
            for name in self.playlists
        }
        # Set default playlist
        self.change_playlist('All')
        
        sorted_playlists = list(self.playlist_buttons.values())
        sorted_playlists.sort(key=lambda x: x.title)
        # Sort them in alphabetical order by title
        playlists_menu = {
            'Playlists': sorted_playlists
        }

        #--- Menu Generation ---#
        self.app.menu = [
            self.toggle_pause_button,
            self.slider_label,
            self.delay_slider,
            self.blur_slider_label,
            self.blur_slider,
            self.open_paper_button,
            { 'Paper Information': [
                self.img_name,
                self.resolution,
                None,
                ],
            },
            'History',
            playlists_menu,
        ]


    def open_paper(self, path=None):
        if path is None: path = self.img_path
        print(f'Opening original image path: {path}')
        subprocess.run(f'open -R "{path}"', shell=True)


    def toggle_pause(self, _):
        if self.toggle_pause_button.title == 'Pause':
            self.timer.stop()
            self.toggle_pause_button.title = 'Play'
            print('Paused...')
            return

        self.timer.start()
        self.toggle_pause_button.title = 'Pause'
        print('Played.')


    def on_slide(self, sender):
        value = int(sender.value)
        self.slider_label.title = f'Delay: {value}s.'
        self.make_timer(value)


    def on_blur_slide(self, sender):
        """ Controls the blur slider. """
        self.blur_intensity = int(sender.value)
        self.blur_slider_label.title = f'Blur Radius: {self.blur_intensity}.'
    

    def on_tick(self, sender):
        self.update_monitor()
        self.update_counter()

        self.random_paper()
        print(f'Changing paper to: {self.img_path.name}')
        paper_manager.change_all_papers(self.paper_path)
        self.img_name.title = self.img_path.name
        self.resolution.title = f'Resolution: {self.img.width} x {self.img.height}'

        self.counter += 1


    def random_img_path(self):
        """ Get the path to a random image to be converted to a wallpaper. """
        img_paths = [
            f for f in self.playlist['path'].rglob('*.*') if f.is_file()
        ]
        return random.choice(img_paths)


    def random_paper(self):
        """ Change to a random wallpaper and update the information on it. """
        # Path to the original image
        self.img_path = self.random_img_path()
        # The original image
        try:
            self.img = Image.open(self.img_path)
        except IOError:
            # File is not an image, try again
            self.random_paper()
            return
        # Load and modify while saving path to original
        self.paper = image_extender.by_blur(self.img, self.monitor, blur_intensity=self.blur_intensity)
        # Save the modified version to a temp directory
        self.paper_path = TEMP_FOLDER / f'{serial()}.jpg'
        self.paper.save(self.paper_path, quality=100, subsampling=0)
        self.update_history(self.img_path)


    def update_history(self, paper_path):
        # Refresh history buttons
        if self.history:
            self.app.menu['History'].clear()

        # Manages the history of papers
        self.history.append(paper_path)
        # Remove the item if the history is too long
        if len(self.history) > 10: self.history.pop(0)

        history_buttons = [
            rumps.MenuItem(
                title=path,
                callback=lambda sender: self.open_paper(sender.title)
            )
            for path in self.history
        ]

        self.app.menu['History'].update(history_buttons)
        


    def mark_playlist_state(self, playlist_name):
        """ Removes mark from old playlist and adds one to new playlist. """
        marker = ' ✓'
        if marker == playlist_name[-2:]:
            return

        if not hasattr(self, 'playlist'):
            # Setting default for first run
            self.playlist_buttons['All'].title += marker
            return

        current_playlist = self.playlist['name']
        # Remove the marker
        self.playlist_buttons[current_playlist].title = current_playlist
        self.playlist_buttons[playlist_name].title += marker


    def change_playlist(self, playlist_name):
        self.mark_playlist_state(playlist_name)
        self.playlist = self.playlists[playlist_name]
        print(f'Playlist changed to: {playlist_name}')


    def run(self):
        self.app.run()


#======================== Entry ========================#
def main():
    WallWeave().run()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print('Keyboard interrupt.')
