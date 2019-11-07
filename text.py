#!/usr/bin/env python
# coding: utf-8

# Copyright 2011 Álvaro Justen [alvarojusten at gmail dot com]
# License: GPL <http://www.gnu.org/copyleft/gpl.html>
#
# Updated by Paul Galatic

import pdb
from PIL import Image, ImageDraw, ImageFont
from extern import *

class ImageText(object):
    def __init__(self, image, mode='RGBA', background=(0, 0, 0, 0)):
        if isinstance(image, type(Image)):
            self.image = image
            self.size = self.image.size
            self.filename = None
        if isinstance(image, str):
            self.filename = image
            self.image = Image.open(self.filename)
            self.size = self.image.size
        elif isinstance(image, (list, tuple)):
            self.size = image
            self.image = Image.new(mode, self.size, color=background)
            self.filename = None
        self.draw = ImageDraw.Draw(self.image)

    def save(self, filename=None):
        self.image.save(filename or self.filename)

    def get_fnt_size(self, text, fnt, max_width=None, max_height=None):
        if max_width is None and max_height is None:
            raise ValueError('You need to pass max_width or max_height')
        fnt_size = 1
        text_size = self.get_text_size(fnt, fnt_size, text)
        if (max_width is not None and text_size[0] > max_width) or \
           (max_height is not None and text_size[1] > max_height):
            raise ValueError("Text can't be filled in only (%dpx, %dpx)" % \
                    text_size)
        while True:
            if (max_width is not None and text_size[0] >= max_width) or \
               (max_height is not None and text_size[1] >= max_height):
                return fnt_size - 1
            fnt_size += 1
            text_size = self.get_text_size(fnt, fnt_size, text)

    def write_text(self, pos, text, fnt, fnt_size=11, color=(0, 0, 0), max_width=None, max_height=None):
        if fnt_size == 'fill':
            if max_width is None or max_height is None:
                max_width = self.size[0]
                max_height = self.size[1]
            fnt_size = self.get_fnt_size(text, fnt, max_width, max_height)
        assert(type(fnt_size) == int)
        fnt = ImageFont.truetype(fnt, fnt_size)
        self.draw.text(pos, text, fnt=fnt, fill=color)
        return self.image

    def get_text_size(self, fnt, fnt_size, text):
        fnt = ImageFont.truetype(fnt, fnt_size)
        text_size = fnt.getsize(text)
        return text_size

    def write_text_box(self, text, fnt, fnt_size, color=(0, 0, 0), align='left', justify_last_line=False, box_width=None):
        lines = []
        line = []
        x, y = 0, 0
        words = text.split()
        if not box_width: box_width = int(self.size[0] * 0.9)
        for word in words:
            new_line = ' '.join(line + [word])
            text_size = self.get_text_size(fnt, fnt_size, new_line)
            text_width = text_size[0]
            text_height = text_size[1]
            if text_width <= self.size[0]:
                line.append(word)
            else:
                lines.append(line)
                line = [word]
        if line:
            lines.append(line)
        lines = [' '.join(line) for line in lines if line]
        height = y
        for index, line in enumerate(lines):
            height += text_height
            if align == 'left':
                self.write_text((x, height), line, fnt, fnt_size, color)
            elif align == 'right':
                total_size = self.get_text_size(fnt, fnt_size, line)
                x_left = x + box_width - total_size[0]
                self.write_text((x_left, height), line, fnt, fnt_size, color)
            elif align == 'center':
                total_size = self.get_text_size(fnt, fnt_size, line)
                x_left = int(x + ((box_width - total_size[0]) / 2))
                self.write_text((x_left, height), line, fnt, fnt_size, color)
            elif align == 'justify':
                words = line.split()
                if (index == len(lines) - 1 and not justify_last_line) or \
                   len(words) == 1:
                    self.write_text((x, height), line, fnt, fnt_size, color)
                    continue
                line_without_spaces = ''.join(words)
                total_size = self.get_text_size(fnt, fnt_size, line_without_spaces)
                space_width = (box_width - total_size[0]) / (len(words) - 1.0)
                start_x = x
                for word in words[:-1]:
                    self.write_text((start_x, height), word, fnt, fnt_size, color)
                    word_size = self.get_text_size(fnt, fnt_size, word)
                    start_x += word_size[0] + space_width
                last_word_size = self.get_text_size(fnt, fnt_size, words[-1])
                last_word_x = x + box_width - last_word_size[0]
                self.write_text((last_word_x, height), words[-1], fnt, fnt_size, color)
        return (box_width, height - y)