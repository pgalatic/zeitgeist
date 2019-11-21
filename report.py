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
import math
import operator
import textwrap
from datetime import datetime

# EXTERNAL LIB
import tweepy
import numpy as np
from colour import Color
from PIL import Image, ImageDraw, ImageFont, ImageOps

# PROJECT LIB
import rectround
from text import ImageText
from extern import *

SML_FNT = ImageFont.truetype(FONT_BOLD, 28)
MED_FNT = ImageFont.truetype(FONT_BOLD, 36)
BIG_FNT = ImageFont.truetype(FONT_BOLD, 128)

def time_string(timestamp):
    dt = datetime.strptime(timestamp, TIME_FORMAT)
    return dt.strftime(OUT_FORMAT)
    
def cluster_color(score):
    '''
    Scores are between 0 and 1.
    '''
    score = math.floor(min(score * 100, 99.99))
    gry = Color(rgb=(170/255, 184/255, 194/255))
    wht = Color(rgb=(1, 1, 1))
    gradient = list(gry.range_to(wht, 100))
    color = tuple(int(val * 255) for val in gradient[score].rgb)
    return color

def sent_color(score):
    '''
    Scores are between -1 and 1.
    '''
    norm = math.floor(min((score + 1) * 50, 99.99))
    red = Color(rgb=(1., 179/255, 186/255))
    grn = Color(rgb=(186/255, 1., 201/255))
    gradient = list(red.range_to(grn, 100))
    color = tuple(int(val * 255) for val in gradient[norm].rgb)
    return color

def box(text, size, fill=WHITE):
    width, height = size
    
    text_size = (width, height)
    text_img = ImageText(text_size, background=fill).write_text_box(text, font_filename=FONT_BOLD)
    text_loc = (0, 0)
    
    img = Image.new('RGBA', size, color=BLANK)    

    img.paste(text_img, text_loc)

    return img
    
def slocbox(size, text):
    width, height = size

    text_size = (width - BUFFER*2, height - SPACING)
    text_img = box(text, text_size)
    text_loc = (BUFFER, SPACING//2)

    base = Image.new('RGBA', size, color=BLANK)
    draw = ImageDraw.Draw(base)
    rectround.rectangle(draw, size)
    base.paste(text_img, text_loc, text_img)
        
    return base

def icon_text(icon, text):
    text_size = SML_FNT.getsize(text)
    text_loc = (icon.size[0] + SPACING // 2, 0)

    total_size = (icon.size[0] + text_size[0] + SPACING, max(icon.size[1], text_size[1]))
    
    img = Image.new('RGBA', total_size, color=WHITE)
    draw = ImageDraw.Draw(img)
    
    img.paste(icon, (0, 0))
    draw.text(text_loc, text, fill=BLACK, font=SML_FNT)
    
    return img

def top_bar(size, username, at_tag):
    width, height = size
    
    if username == '': username = 'Unknown'
    if at_tag == '@': at_tag = '@unknown'

    img = Image.new('RGBA', size, color=WHITE)
    draw = ImageDraw.Draw(img)
    
    avatar_size = (height - BUFFER, height - BUFFER)
    avatar_loc = ((SPACING, SPACING), (avatar_size[0] + SPACING, avatar_size[1] + SPACING))
    
    username_size = SML_FNT.getsize(username)
    username_loc = (avatar_loc[1][0] + SPACING, SPACING)
    
    at_tag_size = SML_FNT.getsize(username)
    at_tag_loc = (avatar_loc[1][0] + SPACING, height - (at_tag_size[1] + SPACING))
    
    icon_img = Image.open(ICON)
    icon_img.thumbnail(avatar_size)
    icon_loc = (size[0] - (SPACING + avatar_size[0]), SPACING)

    draw.ellipse(avatar_loc, fill='black')
    draw.text(username_loc, username, fill=BLACK, font=SML_FNT)
    draw.text(at_tag_loc, at_tag, fill=BLACK, font=SML_FNT)
    img.paste(icon_img, icon_loc)
    
    return img

def bottom_bar(size, comments, retweets, likes, date):
    width, height = size
    
    if comments == '': comments = '0'
    if retweets == '': retweets = '0'
    if likes == '': likes = '0'
    
    icon_comment = Image.open(COMMENT)
    icon_comment.thumbnail((height, height))
    icon_retweet = Image.open(RETWEET)
    icon_retweet.thumbnail((height, height))
    icon_like = Image.open(LIKE)
    icon_like.thumbnail((height, height))
    icon_mail = Image.open(MAIL)
    icon_mail.thumbnail((height, height))
    
    img_comment = icon_text(icon_comment, comments)
    img_retweet = icon_text(icon_retweet, retweets)
    img_like = icon_text(icon_like, likes)
    
    comment_loc = (BUFFER, 0)
    retweet_loc = (BUFFER*2 + img_comment.size[0], 0)
    like_loc = (BUFFER*3 + img_comment.size[0] + img_retweet.size[0], 0)
    mail_loc = (BUFFER*4 + img_comment.size[0] + img_retweet.size[0] + img_like.size[0], 0)
    
    bar = Image.new('RGBA', size=(width, height), color=WHITE)
    bar.paste(img_comment, comment_loc)
    bar.paste(img_retweet, retweet_loc)
    bar.paste(img_like, like_loc)
    bar.paste(icon_mail, mail_loc)
    
    draw = ImageDraw.Draw(bar)
    date_size = SML_FNT.getsize(date)
    date_loc = (width - (BUFFER + date_size[0]), 0)
    draw.text(date_loc, date, fill=BLACK, font=SML_FNT)
    
    return bar

def render_tweet(tweet, size):
    width, height = size
    
    text = tweet['text']
    username = tweet['username']
    at_tag = '@' + tweet['at_tag']
    comments = '' # TODO: Is this in the Twitter search API?
    retweets = tweet['ret_count']
    likes = tweet['fav_count']
    date = time_string(tweet['timestamp'])
    
    top_size = (width, BUFFER*3)
    top = top_bar(top_size, username, at_tag)
    top_loc = (0, 0)
    
    bottom_size = (width, BUFFER)
    bottom = bottom_bar(bottom_size, comments, retweets, likes, date)
    bottom_loc = (0, height - (bottom_size[1] + SPACING))
    
    base_size = (width - BUFFER*2, height - (top_size[1] + bottom_size[1] + BUFFER*2))
    base = box(text, base_size)
    base_loc = (BUFFER, top_size[1])
    
    img = Image.new('RGBA', size=size, color=WHITE)
    img.paste(top, top_loc)
    img.paste(base, base_loc)
    img.paste(bottom, bottom_loc)

    return img

def summary_box(summary, size):
    width, height = size
    
    base_size = (width, height - BUFFER*3)
    base = Image.new('RGBA', base_size, color=BLANK)
    base_draw = ImageDraw.Draw(base)
    rectround.rectangle(base_draw, base_size, border=BLACK)
    base_loc = (0, BUFFER*3)
    
    summary_size = (base_size[0] - BUFFER*4, base_size[1] - BUFFER*4)
    summary_img = box(summary, summary_size)
    summary_loc = (BUFFER*2, BUFFER*2)
    
    base.paste(summary_img, summary_loc)
    
    notice_size = (width - BUFFER, BUFFER*2)
    notice_img = box('Here\'s a summary of what people are saying.', notice_size)
    notice_loc = (BUFFER, BUFFER // 2)
    
    img = Image.new('RGBA', size, color=BLANK)
    draw = ImageDraw.Draw(img)
    rectround.rectangle(draw, size)
    img.paste(notice_img, notice_loc)
    img.paste(base, base_loc, base)

    return img

def colorbar(color_func, size, left_label, right_label, min, max):
    width, height = size
    
    fills = [color_func(score) for score in np.linspace(min, max, 10, endpoint=False)]
    
    left_size = SML_FNT.getsize(left_label)
    left_loc = (SPACING, 0)
    right_size = SML_FNT.getsize(right_label)
    right_loc = (width - (right_size[0] + SPACING), 0)

    rect_size = (width // 10, height // 2)
    rect_loc = ((SPACING, height // 2), (rect_size[0] + SPACING, height))
    
    bar = Image.new('RGBA', size, color=BLANK)
    draw = ImageDraw.Draw(bar)
    draw.text(left_loc, left_label, fill=BLACK, font=SML_FNT)
    draw.text(right_loc, right_label, fill=BLACK, font=SML_FNT)
    for fill in fills:
        draw.rectangle(rect_loc, fill=fill)
        rect_loc = ((rect_loc[0][0] + rect_size[0], height // 2), (rect_loc[1][0] + rect_size[0], height))
    
    return bar

def graph_box(size):
    width, height = size
    
    sloc_size = (width - BUFFER*2, BUFFER*2)
    slocbox_0 = slocbox(sloc_size,
        'Below the summary are tweets representing different groups. The bar above each tweet reflects the size of the group it represents.')
    sloc_0 = (BUFFER, 0)
    
    cluster_size = (width // 2 - BUFFER, height//2)
    cluster_bar = colorbar(cluster_color, cluster_size, 'Low representation', 'High representation', 0, 1)
    cluster_loc = (BUFFER, SPACING*5)
    
    sent_size = (width // 2 - BUFFER, height//2)
    sent_bar = colorbar(sent_color, sent_size, 'Negative sentiment', 'Positive sentiment', -1, 1)
    sent_loc = (width - (cluster_size[0] + BUFFER), SPACING*5)
    
    base = Image.new('RGBA', size, color=BLANK)
    base_draw = ImageDraw.Draw(base)
    rectround.rectangle(base_draw, size)
    base.paste(cluster_bar, cluster_loc, cluster_bar)
    base.paste(sent_bar, sent_loc, sent_bar)
    base.paste(slocbox_0, sloc_0, slocbox_0)

    return base

def cluster_box(rep, size, target, conf_color=None):
    width, height = size

    cardinality = rep[0]
    confidence = rep[1]
    tweet = rep[2]
    
    if not conf_color: conf_color = cluster_color(float(confidence))
    
    base_size = (width, height - BUFFER*2)
    base = Image.new('RGBA', base_size, color=BLANK)
    base_draw = ImageDraw.Draw(base)
    rectround.rectangle(base_draw, base_size, border=BLACK)
    base_loc = (0, BUFFER*2)
    
    tweet_size = (base_size[0] - BUFFER, base_size[1] - BUFFER)
    tweet_img = render_tweet(tweet, tweet_size)
    tweet_loc = (BUFFER // 2, BUFFER // 2)
    
    base.paste(tweet_img, tweet_loc)
    
    proportion = cardinality / len(sample(target))
    color = Color(rgb=(conf_color[0] / 255, conf_color[1] / 255, conf_color[2] / 255))
    color.luminance *= 0.66
    color.saturation *= 0.9
    card_loc = ((BUFFER*2, BUFFER // 2), (BUFFER*2 + (proportion * (width - BUFFER*4)), BUFFER*3//2))
    rect_color = (int(color.red * 255), int(color.green * 255), int(color.blue * 255))
    
    img = Image.new('RGBA', size=size, color=BLANK)
    draw = ImageDraw.Draw(img)
    rectround.rectangle(draw, size, fill=conf_color)
    draw.rectangle(card_loc, fill=rect_color)
    img.paste(base, base_loc, base)
    
    return img

def sent_box(rep, size, target):
    color = sent_color(rep[1])
    return cluster_box(rep, size, target, conf_color=color)

def clustering(size, target, rep0, rep1, rep2, struct, sent=False):
    width, height = size

    struct_size = (width - SPACING*2, BUFFER*2)
    struct_img = slocbox(struct_size, struct)
    struct_loc = (SPACING, SPACING)
    
    # FIXME: Is there a better way to more evenly space these?
    cluster_size = (int(width // 3.03) - SPACING, height - (struct_loc[1] + struct_size[1] + BUFFER))
    cluster_0_loc = (SPACING, height - (cluster_size[1] + BUFFER//2))
    cluster_1_loc = (SPACING + cluster_size[0] + cluster_0_loc[0], cluster_0_loc[1])
    cluster_2_loc = (SPACING + cluster_size[0] + cluster_1_loc[0], cluster_0_loc[1])
    
    if sent:
        cluster_0 = sent_box(rep0, cluster_size, target)
        cluster_1 = sent_box(rep1, cluster_size, target)
        cluster_2 = sent_box(rep2, cluster_size, target)
    else:
        cluster_0 = cluster_box(rep0, cluster_size, target)
        cluster_1 = cluster_box(rep1, cluster_size, target)
        cluster_2 = cluster_box(rep2, cluster_size, target)
    
    img = Image.new('RGBA', size=size, color=BLANK)
    draw = ImageDraw.Draw(img)
    rectround.rectangle(draw, size, fill=WHITE)
    img.paste(struct_img, struct_loc, struct_img)
    img.paste(cluster_0, cluster_0_loc, cluster_0)
    img.paste(cluster_1, cluster_1_loc, cluster_1)
    img.paste(cluster_2, cluster_2_loc, cluster_2)
    
    return img

def create(target, summary, cluster_reps, sent_reps, seed=None, label=None):
    '''
    Takes data generated by the rest of the program and generates a report.
    '''
    log('Compiling report...')
    
    # Some sanity checks to make sure we have the right data.
    assert(type(summary) == str)
    assert(len(cluster_reps) == 3)
    assert(len(sent_reps) == 6)
    
    img = Image.open(BACKGROUND).convert('RGBA')
    name = 'powered by Zeitgeist'
    title_size = BIG_FNT.getsize(target)
    name_size = SML_FNT.getsize(name)
    
    width, height = img.size
    label_loc =     (int(width * 0.80), int(height * 0.02))
    seed_loc =      (int(width * 0.10), int(height * 0.02))
    name_loc =      (width // 2 - name_size[0] // 2, int(height * 0.02))
    title_loc =     (width // 2 - title_size[0] // 2, int(height * 0.05))
    graph_loc =     (int(width * 0.02), title_loc[1] + title_size[1] + BUFFER*2)
    summary_loc =   (int(width * 0.02), int(height * 0.18))
    cluster_0_loc = (int(width * 0.02), int(height * 0.40))
    cluster_1_loc = (int(width * 0.02), int(height * 0.60))
    cluster_2_loc = (int(width * 0.02), int(height * 0.80))
    
    graph_size = (width - (graph_loc[0]*2), summary_loc[1] - (graph_loc[1] + BUFFER))
    summary_size = (width - (summary_loc[0]*2), cluster_0_loc[1] - (summary_loc[1] + BUFFER))
    cluster_size = (width - cluster_0_loc[0]*2, (int(height * 0.19)))
    draw = ImageDraw.Draw(img)
    if label: draw.text(label_loc, f'label={label}', fill=BLACK, font=SML_FNT)
    if seed: draw.text(seed_loc, f'seed={seed}', fill=BLACK, font=SML_FNT)
    draw.text(name_loc, name, fill=BLACK, font=SML_FNT, align='center')
    draw.text(title_loc, target, fill=BLACK, font=BIG_FNT, align='center')
    
    # TODO: ADD LABEL TO SUMMARY BOX
    summary_img = summary_box(summary, summary_size)
    graph_img = graph_box(graph_size)
    cluster_0_box = clustering(cluster_size, target, cluster_reps[0], cluster_reps[1], cluster_reps[2],
        'These tweets represent groups who each use the same words.')
    cluster_1_box = clustering(cluster_size, target, sent_reps[0], sent_reps[1], sent_reps[2],
        'These tweets represent groups who feel strongly on this subject.', sent=True)
    cluster_2_box = clustering(cluster_size, target, sent_reps[3], sent_reps[4], sent_reps[5],
        'These tweets represent the largest groups who all feel similarly.', sent=True)
    
    img.paste(summary_img, summary_loc, summary_img)
    img.paste(graph_img, graph_loc, graph_img)
    img.paste(cluster_0_box, cluster_0_loc, cluster_0_box)
    img.paste(cluster_1_box, cluster_1_loc, cluster_1_box)
    img.paste(cluster_2_box, cluster_2_loc, cluster_2_box)
    
    if label:   img.save(str(REPORT_DIR / target) + label + '.png')
    else:       img.save(str(REPORT_DIR / target) + '.png')
    img.show()