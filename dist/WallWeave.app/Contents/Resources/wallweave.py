#!/usr/bin/env python3
"""macOS wallpaper manager.

**Author: Jonathan Delgado**

"""
#------------- Imports -------------#
from pathlib import Path
import random
import rumps
import subprocess
from PIL import Image, ImageFilter, ImageDraw
import screeninfo
#--- Custom imports ---#
# from tools.config import *
#------------- Fields -------------#
__version__ = '0.0.0.1'
BLUR_INTENSITY = 40
# Scaling algorithm
SCALING = Image.LANCZOS
toggle = False
PAPERS_PATH = Path.home() / 'Drive/Wallpapers/Laptop'
TEMP_FOLDER = Path(__file__).parent.parent / 'temp'
#======================== Helpers ========================#
def should_extend_img(img, monitor):
    """ Checks whether we should bother extending the image. Maybe the image is wide enough. """
    width_percentage = 0.9
    # The image is less than width_percentage% of the monitor width, extend it
    return img.size[0] < monitor.width * width_percentage


def change_to_random_paper():
    path, img = random_paper()
    change_all_papers(path)
    return img


def get_playlists():
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


#======================== Image Modifiers ========================#
def extend_img(img):
    """ Extend the image to fit into screen space. """
    monitor = screeninfo.get_monitors()[0]
    
    # Rescale the image to fit into display
    # img.thumbnail((monitor.width, monitor.height), SCALING)
    aspect_ratio = monitor.width / monitor.height
    monitor.width = int(img.height * aspect_ratio)
    monitor.height = img.height

    if not should_extend_img(img, monitor):
        print('Not going to extend this image.')
        return img.convert('RGB')

    # The padding we need on the left, i.e. we'll have the main image start here
    # This also indicates the width of the left portion of the blur.
    x_padding = (monitor.width - img.width) // 2
    # Check if we're cutting off more than half
    # y_padding = (monitor.height - img.height) // 2
    y_padding = 0

    if x_padding > img.width / 2:
        # The image is not wide enough, we'd be cutting off more than half
        # Let's stretch it first
        left_width = img.width // 2
        left = img.crop((0, 0, left_width, img.height))
        right = img.crop((left_width, 0, img.width, img.height))
        # Stretch it
        left = left.resize((x_padding, img.height), SCALING)
        right = right.resize((x_padding, img.height), SCALING)

    else:
        # Get the left portion of the image for blurring, it's big enough
        left = img.crop((0, 0, x_padding, img.height))
        right = img.crop((img.width - x_padding, 0, img.width, img.height))

    # The main canvas
    canvas = Image.new('RGBA', (monitor.width, monitor.height), (0, 0, 0, 0))
    canvas.paste(left, (0, y_padding))
    canvas.paste(img, (x_padding, y_padding)) # center
    # - 1 to account for integer flooring
    canvas.paste(right, (monitor.width - x_padding - 1, y_padding))

    # Create rectangle mask
    mask = Image.new('L', canvas.size, 0)
    draw = ImageDraw.Draw(mask)
    # Blur into the main picture a bit to hide lines
    buffer = 20
    draw.rectangle(
        [ (x_padding + buffer, y_padding),
        (x_padding + img.width - buffer, y_padding + img.height) ],
        fill=255
    )
    # Blur the entire canvas
    blurred = canvas.filter(ImageFilter.GaussianBlur(BLUR_INTENSITY))
    # Reapply the main image over the blurred canvas while using the mask to 
    # indicate where the main image should pass through.
    # Effectively blurs the complement
    blurred.paste(canvas, mask=mask)
    return blurred.convert('RGB')

    
#======================== MacOS Interactions ========================#
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


#======================== MenuBar ========================#
class WallWeave(object):
    def __init__(self):
        self.app = rumps.App('Wallpaper Manager')
        self.playlists = get_playlists()
        self.set_up_menu()

        # Make the wallpaper change timer
        self.make_timer(5)


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
        # Slider for adjusting time delay of papers
        self.delay_slider = rumps.SliderMenuItem(
             value=5, min_value=5, max_value=600,
            dimensions=(150, 40), callback=self.on_slide
        )
        self.slider_label = rumps.MenuItem(
            title=f'Delay: {int(self.delay_slider.value)}s'
        )

        #--- Pause ---#
        self.toggle_pause_button = rumps.MenuItem(
            title='Pause', callback=self.toggle_pause
        )

        #--- Paper information ---#
        self.img_name = rumps.MenuItem(title='Name')
        self.resolution = rumps.MenuItem(title='Resolution: ')
        self.open_paper_button = rumps.MenuItem(
            title='Open Image', callback=self.open_paper
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
            # { 'Paper Information': [
            self.img_name,
            self.resolution,
            self.open_paper_button,
            playlists_menu,
            None,
                # ],
            # },
        ]


    def open_paper(self, _):
        print(f'Opening original image path: {self.img_path}')
        subprocess.run(f'open -R "{self.img_path}"', shell=True)


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
        self.slider_label.title = f'Delay: {value}s'
        self.make_timer(value)
    

    def on_tick(self, sender):
        self.random_paper()
        change_all_papers(self.paper_path)
        print(f'Paper changed to: {self.img_path.name}')
        self.img_name.title = self.img_path.name
        self.resolution.title = f'Resolution: {self.img.width} x {self.img.height}'


    def random_img_path(self):
        """ Get the path to a random image to be converted to a wallpaper. """
        img_paths = [
            f for f in self.playlist['path'].rglob('*.*') if f.is_file()
        ]
        return random.choice(img_paths)


    def random_paper(self):
        """ Change to a random wallpaper and update the information on it. """
        # Temp toggle to force changing of wallpaper
        global toggle
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
        self.paper = extend_img(self.img)
        # Save the modified version to a temp directory
        self.paper_path = TEMP_FOLDER / f'{toggle}.jpg'
        self.paper.save(self.paper_path, quality=100, subsampling=0)
        # Flip toggle
        toggle = not toggle


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
    #--- Real ---#
    WallWeave().run()
    return

    #--- Test image extension ---#
    orig_path = Path.home() / 'Drive/Wallpapers/Mobile/512ybxga4pv81.jpg'
    extend_img(Image.open(orig_path)).show()
    return


    #--- Test main ---#
    # Temp toggle to force changing of wallpaper
    toggle = False
    # Get a random image
    # orig_path = random_img_path()
    # Force a path
    img = Image.open(orig_path)
    # Load and modify while saving path to original
    img = extend_img(img)
    # Save the modified version to a temp directory
    modified_path = temp_folder / f'{toggle}.png'
    image.save(modified_path, 'PNG')
    # Flip toggle
    toggle = not toggle
    # Change wallpapers
    # change_all_papers(modified_path)
    # change_all_papers(orig_path)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print('Keyboard interrupt.')
