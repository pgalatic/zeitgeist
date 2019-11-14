#!/usr/bin/env python
# coding: utf-8

# Copyright 2011 Álvaro Justen [alvarojusten at gmail dot com]
# Edited by Paul Galatic
# License: GPL <http://www.gnu.org/copyleft/gpl.html>

import pdb

from PIL import Image, ImageDraw, ImageFont

from extern import *

class ImageText(object):
    def __init__(self, filename_or_size, mode='RGBA', background=(0, 0, 0, 0),
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
                if newsize[0] < self.size[0]:
                    # We can fit this word on the line
                    line.append(word)
                else:
                    # We have to make a new line
                    height -= newsize[1]
                    newline = ' '.join(line)
                    if font.getsize(newline)[0] > self.size[0]:
                        # We can't fit this one-word line horizontally
                        return prev_lines, prev_font
                    lines.append(newline)
                    line = [word]
            if height < 0:
                # We can't fit this text vertically
                return prev_lines, prev_font
            prev_lines = lines
            prev_font = font
            font_size += 8

    def write_text_box(self, text, font_filename, color=(0, 0, 0)):
        height = 0
        lines, font = self.split_lines(text, font_filename)
        
        for index, line in enumerate(lines):
            self.draw.text((0, height), line, fill=color, font=font)
            height += font.getsize(line)[1]
        
        return self.image