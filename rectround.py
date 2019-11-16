#
# author: Paul Galatic
#
# This program is JUST for drawing a rounded rectangle.
#

import pdb

from PIL import Image, ImageDraw

from extern import *

def sub_rectangle(draw, xy, corner_radius=50, fill=(255, 255, 255)):
    '''
    Source: https://stackoverflow.com/questions/7787375/python-imaging-library-pil-drawing-rounded-rectangle-with-gradient
    '''
    upper_left_point = xy[0]
    bottom_right_point = xy[1]
    draw.rectangle(
        [
            (upper_left_point[0], upper_left_point[1] + corner_radius),
            (bottom_right_point[0], bottom_right_point[1] - corner_radius)
        ],
        fill=fill,
    )
    draw.rectangle(
        [
            (upper_left_point[0] + corner_radius, upper_left_point[1]),
            (bottom_right_point[0] - corner_radius, bottom_right_point[1])
        ],
        fill=fill,
    )
    draw.pieslice([upper_left_point, (upper_left_point[0] + corner_radius * 2, upper_left_point[1] + corner_radius * 2)],
        180,
        270,
        fill=fill,
    )
    draw.pieslice([(bottom_right_point[0] - corner_radius * 2, bottom_right_point[1] - corner_radius * 2), bottom_right_point],
        0,
        90,
        fill=fill,
    )
    draw.pieslice([(upper_left_point[0], bottom_right_point[1] - corner_radius * 2), (upper_left_point[0] + corner_radius * 2, bottom_right_point[1])],
        90,
        180,
        fill=fill,
    )
    draw.pieslice([(bottom_right_point[0] - corner_radius * 2, upper_left_point[1]), (bottom_right_point[0], upper_left_point[1] + corner_radius * 2)],
        270,
        360,
        fill=fill,
    )

def rectangle(draw, size, fill=WHITE, border=None):
    width, height = size
    
    img = Image.new('RGBA', size, color=BLANK)

    if border:
        outdims = ((0, 0), (width, height))
        sub_rectangle(draw, outdims, fill=border)
        indims = ((BORDER, BORDER), (width - BORDER, height - BORDER))
    else:
        indims = ((0, 0), (width, height))
    
    sub_rectangle(draw, indims, fill=fill)
    
    return img