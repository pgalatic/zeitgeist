#
# authors:
#   Paul Galatic
#
# description:
#   Assembles report given data from Zeitgeist.
#

# STD LIB
import os
import pdb
import sys
import textwrap

# EXTERNAL LIB
import tweepy
from PIL import Image, ImageDraw, ImageFont

# PROJECT LIB
from text2 import ImageText
from extern import *

TNY_FNT = ImageFont.truetype(FONT_BOLD, 10)
SML_FNT = ImageFont.truetype(FONT_BOLD, 32)
MED_FNT = ImageFont.truetype(FONT_BOLD, 48)
BIG_FNT = ImageFont.truetype(FONT_BOLD, 96)
LRG_FNT = ImageFont.truetype(FONT_BOLD, 128)

def box(text, fnt=MED_FNT, wrap=32, align='left'):
    text = textwrap.wrap(text, width=wrap)

    (w, h) = text_size(text, fnt)
    
    img = Image.new('RGB', size=(w+BORDER, h+BORDER), color=WHITE)
    draw = ImageDraw.Draw(img)
    draw.text((BORDER // 2, BORDER // 2), text, fill=BLACK, font=fnt, align=align)
    return img
    
def cluster_box(rep):
    cardinality = rep[0]
    confidence = rep[1]
    text = rep[2]['text']
    username = rep[2]['username']
    at_tag = rep[2]['at_tag']
    
    base = box(text)
    (w, h) = base.size
    base_loc = (10, 50)
    avatar_loc = (10, 10)
    username_loc = (20, 10)
    at_tag_loc = (20, 20)

    img = Image.new('RGB', size=(w + base_loc[0], h + base_loc[1]), color=WHITE)
    draw = ImageDrwa.Draw(img)
    draw.ellipse(avatar_loc, (avatar_loc[0] + 10, avatar_loc[1] + 10), fill='black')
    draw.text(username_loc, username, fill=BLACK, fnt=TNY_FNT, align='left')
    draw.text(at_tag_loc, at_tag, fill=BLACK, fnt=TNY_FNT, align='left')
    img.paste(base, base_loc)

    return img

def create(target, summary, cluster_reps, sent_reps, seed=None, label=None):
    '''
    Takes data generated by the rest of the program and generates a report.
    '''
    # Some sanity checks to make sure we have the right data.
    assert(type(summary) == str)
    assert(len(cluster_reps) == 3)
    assert(len(sent_reps) == 6)
    
    img = Image.open(BACKGROUND)
    
    width, height = img.size
    label_loc =     (int(width * 0.80), int(height * 0.10))
    seed_loc =      (int(width * 0.10), int(height * 0.10))
    title_loc =     (int(width * 0.30), int(height * 0.10))
    summary_loc =   (int(width * 0.05), int(height * 0.20))
    cluster_0_loc = (int(width * 0.05), int(height * 0.45))
    cluster_1_loc = (int(width * 0.35), int(height * 0.45))
    cluster_2_loc = (int(width * 0.65), int(height * 0.45))
    sent_0_loc =    (int(width * 0.05), int(height * 0.65))
    sent_1_loc =    (int(width * 0.35), int(height * 0.65))
    sent_2_loc =    (int(width * 0.65), int(height * 0.65))
    sent_3_loc =    (int(width * 0.05), int(height * 0.85))
    sent_4_loc =    (int(width * 0.35), int(height * 0.85))
    sent_5_loc =    (int(width * 0.65), int(height * 0.85))
    
    summary_size = (width - summary_loc[0] * 2, cluster_0_loc[1] - summary_loc[1])
    
    cluster_text = ['\n'.join(textwrap.wrap(rep[2]['text'], width=32)) for rep in cluster_reps]
    sent_text = ['\n'.join(textwrap.wrap(rep, width=32)) for rep in sent_reps]
    
    draw = ImageDraw.Draw(img)
    if label: draw.text(label_loc, f'label={label}', fill=(0, 0, 0), font=SML_FNT)
    if seed: draw.text(seed_loc, f'seed={seed}', fill=(0, 0, 0), font=SML_FNT)
    draw.text(title_loc, '\n' + target, fill=(0, 0, 0), font=BIG_FNT, align='center')
    
    summary_img = ImageText(summary_size, background=WHITE)
    summary_img.write_text_box((0, 0), summary, font_filename=FONT_BOLD, font_size=96)
    
    img.paste(summary_img.image, summary_loc)
    #img.paste(cluster_box(cluster_reps[0]))
    #img.paste(cluster_box(cluster_reps[1]))
    #img.paste(cluster_box(cluster_reps[2]))
    draw.text(sent_0_loc, sent_text[0], fill=(0, 0, 0), font=MED_FNT, align='center')
    draw.text(sent_1_loc, sent_text[1], fill=(0, 0, 0), font=MED_FNT, align='center')
    draw.text(sent_2_loc, sent_text[2], fill=(0, 0, 0), font=MED_FNT, align='center')
    draw.text(sent_3_loc, sent_text[3], fill=(0, 0, 0), font=MED_FNT, align='center')
    draw.text(sent_4_loc, sent_text[4], fill=(0, 0, 0), font=MED_FNT, align='center')
    draw.text(sent_5_loc, sent_text[5], fill=(0, 0, 0), font=MED_FNT, align='center')
    
    img.save(str(REPORT_DIR / target) + '.png')