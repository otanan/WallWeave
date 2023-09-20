from PIL import Image
import numpy as np
import cv2

class Monitor(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height

# monitor = {'width':3440, 'height':1440}
monitor = Monitor(3440, 1440)


def extend_img_by_mirroring(img, monitor):


    desired_ar = monitor.width / monitor.height
    padding = np.shape(img)[0]*desired_ar - np.shape(img)[0]

    image = cv2.copyMakeBorder(np.array(img), 0, 0, int(padding/2.), int(padding/2.), cv2.BORDER_REFLECT)

    print(np.shape(image))

    return Image.fromarray(image)


img = Image.open('../tests/test2.jpg')
img.show()
input()

new_img = extend_img_by_mirroring(img, monitor)
new_img.show()