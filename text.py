#!/usr/bin/env python
# coding: utf-8

# Copyright 2011 Álvaro Justen [alvarojusten at gmail dot com]
# Edited by Paul Galatic
# License: GPL <http://www.gnu.org/copyleft/gpl.html>

import pdb

from PIL import Image, ImageDraw, ImageFont

from extern import *

class ImageText(object):
    def __init__(self, filename_or_size, mode='RGBA', background=WHITE,
                 encoding='utf8'):
        if isinstance(filename_or_size, str):
            self.filename = filename_or_size
            self.image = Image.open(self.filename)
            self.size = self.image.size
        elif isinstance(filename_or_size, (list, tuple)):
            self.size = filename_or_size
            self.image = Image.new(mode, self.size, color=background)
            self.filename = None
        self.draw = ImageDraw.Draw(self.image)
        self.encoding = encoding
    
    def split_lines(self, text, font_filename, min_size=8):
        font_size = min_size
        prev_lines = None
        prev_font = None
        while True:
            font = ImageFont.truetype(font_filename, font_size)
            height = self.size[1]
            lines = []
            line = []
            words = text.split()
            for word in words:
                newline = ' '.join(line + [word])
                newsize = font.getsize(newline)
                
                # Can we fit this line horizontally?
                if newsize[0] < self.size[0]:
                    # Can we fit this line vertically?
                    if newsize[1] < height:
                        # Then append it.
                        line.append(word)
                    # We need to return.
                    else:
                        assert(prev_lines and prev_font)
                        return prev_lines, prev_font
                else:
                    # We need to make a new line.
                    if len(line) == 1:
                        # We can't fit this one-word line horizontally
                        assert(prev_lines and prev_font)
                        return prev_lines, prev_font
                    height -= newsize[1]
                    newline = ' '.join(line)
                    lines.append(newline)
                    line = [word]
            # There will be one final line. Can it fit?
            newsize = font.getsize(' '.join(line))
            # If it can, then append it and try the next size.
            if newsize[0] < self.size[0] and newsize[1] < height:
                lines.append(' '.join(line))
                prev_lines = lines
                prev_font = font
                font_size += 8
            # Otherwise, return the previous lines and size.
            else:
                assert(prev_lines and prev_font)
                return prev_lines, prev_font

    def write_text_box(self, text, font_filename, color=(0, 0, 0)):
        height = 0
        lines, font = self.split_lines(text, font_filename)
        
        for index, line in enumerate(lines):
            self.draw.text((0, height), line, fill=color, font=font)
            height += font.getsize(line)[1]
        
        return self.image