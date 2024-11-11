#!/usr/bin/env python3
"""Handles extending images to fit provided resolutions and eases testing.

**Author: Jonathan Delgado**

"""
#------------- Imports -------------#
# ImageEnhance for controlling brightness
from PIL import Image, ImageFilter, ImageDraw, ImageEnhance
import numpy as np
# import cv2
#--- Custom imports ---#
#------------- Fields -------------#
# Scaling algorithm
SCALING = Image.LANCZOS
#======================== Helpers ========================#
def aspect_ratio(monitor):
    return monitor.width / monitor.height


def canvas_dimensions(img, monitor):
    """ Gets the dimensions of the canvas to work with for generating the wallpaper keeping into account the monitor's dimensions and the current dimensions of the image. """
    # Assumes that the height of the canvas will match the height of the image.
    height = img.height
    width = int(aspect_ratio(monitor) * height)
    return (width, height)


#======================== Image Helpers ========================#
def make_shadow_rect(img, rectangle):
    """ Pastes a rectangle onto the image to be blurred into a shadow. """
    rect_width = 40
    ImageDraw.Draw(canvas).rectangle(
        [ img_x1 - (rect_width // 2), img_y0, img_x1 + (rect_width // 2), img_y1 ],
        fill='black'
    )
    ImageDraw.Draw(canvas).rectangle(
        [ img_x0 - (rect_width // 2), img_y0, img_x0 + (rect_width // 2), img_y1 ],
        fill='black'
    )


#======================== Modifiers ========================#
def by_blur(img, monitor, blur_intensity=20, brightness=0.8):
    """ Extend the image to fit into screen space. """
    canvas_width, canvas_height = canvas_dimensions(img, monitor)
    # The padding we need on the left, i.e. we'll have the main image start here
    # This also indicates the width of the left portion of the blur.
    x_padding = (canvas_width - img.width) // 2
    # Check if we're cutting off more than half
    # y_padding = (monitor.height - img.height) // 2
    y_padding = 0

    if x_padding <= 0:
        # Image is too big as-is just use it by viewing it as a centered frame
        return img.convert('RGB')
    elif x_padding > img.width / 2:
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

    # New coordinates for the focus of the image in the center
    img_x0, img_y0 = x_padding, y_padding
    # Corrective -2 to adjust for flooring, may cut slightly into image
    img_x1, img_y1 = img_x0 + img.width, img_y0 + img.height

    # The main canvas
    canvas = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
    canvas.paste(left, (0, img_y0))
    canvas.paste(img, (img_x0, img_y0)) # center
    # Paste the right portion at the top right corner of the main image
    canvas.paste(right, (img_x1, img_y0))

    # Create rectangle mask
    mask = Image.new('L', canvas.size, 0)
    draw = ImageDraw.Draw(mask)
    # Small buffer to blur into the image to avoid some rounding issues
    buffer = 1
    draw.rectangle(
        [ img_x0 + buffer, img_y0, img_x1 - buffer, img_y1 ],
        fill=255
    )

    # Blur the entire canvas
    blurred = canvas.filter(ImageFilter.GaussianBlur(blur_intensity))
    
    # Dim it
    if brightness != 1:
        enhancer = ImageEnhance.Brightness(blurred)
        # to reduce brightness by 50%, use factor 0.5
        blurred = enhancer.enhance(brightness)

    # Put the center
    blurred.paste(img, (img_x0, img_y0))

    return blurred.convert('RGB')


# def by_mirror(img, monitor, blur_intensity=None, brightness=None):
#     """ Extends the image by mirroring the sides to fill up remaining space. Written by Joseph Farah. Extra kwargs are ignored but included in signature to match other modifiers. """
#     padding = np.shape(img)[0] * aspect_ratio(monitor) - np.shape(img)[0]

#     image = cv2.copyMakeBorder(
#         np.array(img), 0, 0, padding // 2, padding // 2,
#         cv2.BORDER_REFLECT
#     )
#     return Image.fromarray(image)


def by_matched_ratio_blur(img, monitor, blur_intensity=20, brightness=0.8):
    """ Extend the image to fit into screen space but match the aspect ratio. """
    canvas_width, canvas_height = canvas_dimensions(img, monitor)
    # The padding we need on the left, i.e. we'll have the main image start here
    # This also indicates the width of the left portion of the blur.
    x_padding = (canvas_width - img.width) // 2
    # Check if we're cutting off more than half
    # y_padding = (monitor.height - img.height) // 2
    y_padding = 0

    if x_padding <= 0:
        # Image is too big as-is just use it by viewing it as a centered frame
        return img.convert('RGB')
    # elif x_padding > img.width / 2:
    #     # The image is not wide enough, we'd be cutting off more than half
    #     # Let's stretch it first
    #     left_width = img.width // 2
    #     left = img.crop((0, 0, left_width, img.height))
    #     right = img.crop((left_width, 0, img.width, img.height))
    #     # Stretch it
    #     left = left.resize((x_padding, img.height), SCALING)
    #     right = right.resize((x_padding, img.height), SCALING)
    else:
        img_aspect_ratio = img.width / img.height
        # Make the image the full width of the display
        back_img_height = int(canvas_width / img_aspect_ratio)
        
        back_img = img.resize((canvas_width, back_img_height), SCALING)
        # Crop out the center portion of the image that respects
        # the aspect ratio and to later serve as the background
        back_img = back_img.crop((
            0, (back_img_height - canvas_height) // 2,
            canvas_width, (back_img_height + canvas_height) // 2
        ))


    # New coordinates for the focus of the image in the center
    img_x0, img_y0 = x_padding, y_padding
    # Corrective -2 to adjust for flooring, may cut slightly into image
    img_x1, img_y1 = img_x0 + img.width, img_y0 + img.height

    # The main canvas
    canvas = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
    canvas.paste(back_img, (0, 0))

    # Create rectangle mask
    mask = Image.new('L', canvas.size, 0)
    draw = ImageDraw.Draw(mask)
    # Small buffer to blur into the image to avoid some rounding issues
    buffer = 1
    draw.rectangle(
        [ img_x0 + buffer, img_y0, img_x1 - buffer, img_y1 ],
        fill=255
    )

    # Blur the entire canvas
    blurred = canvas.filter(ImageFilter.GaussianBlur(blur_intensity))
    
    # Dim it
    if brightness != 1:
        enhancer = ImageEnhance.Brightness(blurred)
        # to reduce brightness by 50%, use factor 0.5
        blurred = enhancer.enhance(brightness)

    # Put the center
    blurred.paste(img, (img_x0, img_y0))

    return blurred.convert('RGB')


#======================== Entry ========================#

def main():
    from pathlib import Path
    import screeninfo
    monitor = screeninfo.get_monitors()[0]

    PAPERS_PATH = Path.home() / 'Drive/Wallpapers'
    # Testing papers
    # Standard
    path = PAPERS_PATH / 'Testing/IMG_3363.JPG'
    # Mobile
    # path = PAPERS_PATH / 'IMG_3822.jpg'
    # Ultrawide
    # path = PAPERS_PATH / '62 - CFn9TEx.jpg'

    img = Image.open(path)
    # img.show()
    # by_blur(img, monitor).show()
    by_matched_ratio_blur(img, monitor).show()

    

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print('Keyboard interrupt.')