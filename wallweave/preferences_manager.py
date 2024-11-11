#!/usr/bin/env python3
"""Preferences GUI for WallWeave

**Author: Jonathan Delgado**

"""
#------------- Imports -------------#
from pathlib import Path
import random
import sys
from PIL import Image, ImageFilter, ImageDraw
from PIL.ImageQt import ImageQt # convert PIL images to Pixmaps
from pillow_heif import register_heif_opener # working with heic
register_heif_opener() # necessary for HEIC files to work
import screeninfo
#--- PyQt6 ---#
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QGridLayout,
    QWidget,
    QPushButton,
    QSlider,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import PyQt6
#--- Custom imports ---#
import image_extender
#------------- Fields -------------#
__version__ = '0.0.0.0'
PAPERS_PATH = Path.home() / 'Drive/Wallpapers'
#======================== Main ========================#


class Preferences(QWidget):

    def __init__(self):
        super().__init__()
        self.monitor = screeninfo.get_monitors()[0]

        self.image_container = QLabel()
        # Setup the layout
        self.layout = QGridLayout()
        self.layout.addWidget(self.image_container, 0, 0, 16, 16)
        self.setLayout(self.layout)
        self.setWindowTitle('WallWeave Preferences')

        #--- Blur Slider ---#
        row = 17
        self.blur_slider_label = QLabel(self)
        self.blur_slider_label.setText('Blur Intensity: 0')
        self.blur_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.blur_slider.setMinimum(0)
        self.blur_slider.setMaximum(100)
        self.blur_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.blur_slider.setTickInterval(5)
        self.blur_slider.sliderReleased.connect(self.blur_slider_changed)
        self.layout.addWidget(self.blur_slider, row, 1, 1, 3)
        self.layout.addWidget(self.blur_slider_label, row, 4)

        #--- Brightness Slider ---#
        row += 1
        self.brightness_slider_label = QLabel(self)
        self.brightness_slider_label.setText('Brightness: 100')
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.brightness_slider.setMinimum(0)
        self.brightness_slider.setMaximum(100)
        self.brightness_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.brightness_slider.setTickInterval(5)
        self.brightness_slider.setValue(100)
        self.brightness_slider.sliderReleased.connect(self.brightness_slider_changed)
        self.layout.addWidget(self.brightness_slider, row, 1, 1, 3)
        self.layout.addWidget(self.brightness_slider_label, row, 4)


        #--- Image interactions ---#
        self.random_img()
        self.button = QPushButton('Random Image')
        self.button.clicked.connect(self.random_img)
        self.layout.addWidget(self.button, 17, 0)

        # self.setGeometry(0, 0, 320, 200)
        self.show()
     

    def blur_slider_changed(self):
        print(self.sender().value())
        self.blur_slider_label.setText(f'Blur Intensity: {self.sender().value()}')
        self.blur_slider_label.adjustSize()  # Expands label size as numbers get larger
        self.update_img()


    def brightness_slider_changed(self):
        print(self.sender().value())
        self.brightness_slider_label.setText(
            f'Brightness: {self.sender().value()}%'
        )
        self.brightness_slider_label.adjustSize()  # Expands label size as numbers get larger
        self.update_img()


    def random_img_path(self):
        """ Get the path to a random image to be converted to a wallpaper. """
        img_paths = [
            f for f in PAPERS_PATH.rglob('*.*') if f.is_file()
        ]
        self.img_path = str(random.choice(img_paths))


    def random_img(self):
        self.random_img_path()
        # The original image
        try:
            self.img = Image.open(self.img_path)
        except IOError:
            # File is not an image, try again
            self.random_img()
            return
        
        self.update_img()
        

    def update_img(self):
        post = image_extender.by_blur(
            self.img, self.monitor,
            blur_intensity=self.blur_slider.value(),
            brightness=self.brightness_slider.value()/100,
        )
        qimage = ImageQt(post)
        pix = PyQt6.QtGui.QPixmap.fromImage(qimage)
        # pix = pix.scaledToHeight(int(0.8 * self.monitor.height))
        percent = 0.8
        img_width = int(percent * self.monitor.width)
        img_height = int(percent * self.monitor.height)
        pix = pix.scaled(img_width, img_height)
        self.image_container.setPixmap(pix)


    def random_paper(self):
        """ Change to a random wallpaper and update the information on it. """
        # Path to the original image
        return QPixmap(str(self.random_img_path()))
        self.img_path = self.random_img_path()


#======================== Entry ========================#
def main():
    app = QApplication(sys.argv)
    ex = Preferences()
    sys.exit(app.exec())


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print('Keyboard interrupt.')