import numpy as np


def rect_detection(pixel_list):
    rect = np.array(pixel_list)[3:25, -25:-3]   # rows 3-25, columns 25-3 from the right (was -3:-25 = empty)
    return bool((rect > 70).any())


def center_detection(pixel_list):
    img = np.asarray(pixel_list); h, w = img.shape[:2]
    cy = h//2 + h//10   # middle, shifted down by 10% of the image height
    rect = img[cy-11:cy+11, w//2-11:w//2+11]   # 22x22 px, same size as the corner area
    return bool((rect > 70).any())
