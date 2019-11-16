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
from colour import Color
from PIL import Image, ImageDraw, ImageFont, ImageOps

# PROJECT LIB
import rectround
from text import ImageText
from extern import *

SML_FNT = ImageFont.truetype(FONT_BOLD, 28)
MED_FNT = ImageFont.truetype(FONT_BOLD, 64)
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
    score = math.floor(min((score + 1) * 50, 99.99))
    red = Color(rgb=(1, 179/255, 186/255))
    grn = Color(rgb=(186/255, 1, 201/255))
    gradient = list(red.range_to(grn, 100))
    color = tuple(int(val * 255) for val in gradient[score].rgb)
    return color

def box(text, size, fill=WHITE):
    width, height = size
    
    text_size = (width, height)
    text_img = ImageText(text_size, background=fill).write_text_box(text, font_filename=FONT_BOLD)
    text_loc = (0, 0)
    
    img = Image.new('RGBA', size, color=BLANK)    

    img.paste(text_img, text_loc)

    return img

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
    avatar_loc = ((BUFFER // 2, BUFFER // 2), (avatar_size[0] + SPACING, avatar_size[1] + SPACING))
    
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
    bottom_loc = (0, height - (bottom_size[1] + BUFFER))
    
    base_size = (width - BUFFER, height - (top_size[1] + bottom_size[1] + BUFFER))
    base = box(text, base_size)
    base_loc = (0, top_size[1])
    
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
    
    summary_size = (base_size[0] - BUFFER, base_size[1] - BUFFER)
    summary_img = box(summary, summary_size)
    summary_loc = (BUFFER // 2, BUFFER // 2)
    
    base.paste(summary_img, summary_loc)
    
    notice_size = (width - BUFFER, BUFFER*2)
    notice_img = box('Here\'s what people are saying.', notice_size)
    notice_loc = (BUFFER // 2, BUFFER // 2)
    
    img = Image.new('RGBA', size, color=BLANK)
    draw = ImageDraw.Draw(img)
    rectround.rectangle(draw, size)
    img.paste(notice_img, notice_loc)
    img.paste(base, base_loc, base)

    return img

def cluster_box(rep, size, conf_color=None):
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
    
    stats_text = f'Cardinality: {cardinality}; Confidence: {confidence}'
    stats_loc = (BUFFER // 2, BUFFER // 2)
    
    img = Image.new('RGBA', size=size, color=BLANK)
    draw = ImageDraw.Draw(img)
    rectround.rectangle(draw, size, fill=conf_color)
    draw.text(stats_loc, stats_text, fill=BLACK, font=SML_FNT)
    img.paste(base, base_loc, base)
    
    return img

def sent_box(rep, size):
    color = sent_color(rep[1])
    return cluster_box(rep, size, conf_color=color)

def create(target, summary, cluster_reps, sent_reps, seed=None, label=None):
    '''
    Takes data generated by the rest of the program and generates a report.
    '''
    # Some sanity checks to make sure we have the right data.
    assert(type(summary) == str)
    assert(len(cluster_reps) == 3)
    assert(len(sent_reps) == 6)
    
    img = Image.open(BACKGROUND).convert('RGBA')
    title_size = BIG_FNT.getsize(target)
    
    width, height = img.size
    label_loc =     (int(width * 0.80), int(height * 0.02))
    seed_loc =      (int(width * 0.10), int(height * 0.02))
    title_loc =     (width // 2 - title_size[0] // 2, int(height * 0.05))
    summary_loc =   (int(width * 0.02), title_loc[1] + title_size[1] + BUFFER*2)
    cluster_0_loc = (int(width * 0.02), int(height * 0.46))
    cluster_1_loc = (int(width * 0.34) + BUFFER // 4, int(height * 0.46))
    cluster_2_loc = (int(width * 0.66) + BUFFER // 2, int(height * 0.46))
    sent_0_loc =    (int(width * 0.02), int(height * 0.64))
    sent_1_loc =    (int(width * 0.34) + BUFFER // 4, int(height * 0.64))
    sent_2_loc =    (int(width * 0.66) + BUFFER // 2, int(height * 0.64))
    sent_3_loc =    (int(width * 0.02), int(height * 0.82))
    sent_4_loc =    (int(width * 0.34) + BUFFER // 4, int(height * 0.82))
    sent_5_loc =    (int(width * 0.66) + BUFFER // 2, int(height * 0.82))
    
    summary_size = (width - (summary_loc[0] + BUFFER), cluster_0_loc[1] - (summary_loc[1] + BUFFER))
    cluster_size = (cluster_1_loc[0] - (cluster_0_loc[0] + BUFFER), sent_0_loc[1] - (cluster_0_loc[1] + BUFFER))
    sent_size = (sent_1_loc[0] - (sent_0_loc[0] + BUFFER), height - (sent_4_loc[1] + BUFFER))
    
    draw = ImageDraw.Draw(img)
    if label: draw.text(label_loc, f'label={label}', fill=BLACK, font=SML_FNT)
    if seed: draw.text(seed_loc, f'seed={seed}', fill=BLACK, font=SML_FNT)
    draw.text(title_loc, target, fill=BLACK, font=BIG_FNT, align='center')
    
    # TODO: ADD LABEL TO SUMMARY BOX
    summary_img = summary_box(summary, summary_size)
    cluster_0_box = cluster_box(cluster_reps[0], cluster_size)
    cluster_1_box = cluster_box(cluster_reps[1], cluster_size)
    cluster_2_box = cluster_box(cluster_reps[2], cluster_size)
    sent_0_box = sent_box(sent_reps[0], sent_size)
    sent_1_box = sent_box(sent_reps[1], sent_size)
    sent_2_box = sent_box(sent_reps[2], sent_size)
    sent_3_box = sent_box(sent_reps[3], sent_size)
    sent_4_box = sent_box(sent_reps[4], sent_size)
    sent_5_box = sent_box(sent_reps[5], sent_size)
    
    img.paste(summary_img, summary_loc, summary_img)
    img.paste(cluster_0_box, cluster_0_loc, cluster_0_box)
    img.paste(cluster_1_box, cluster_1_loc, cluster_1_box)
    img.paste(cluster_2_box, cluster_2_loc, cluster_2_box)
    img.paste(sent_0_box, sent_0_loc, sent_0_box)
    img.paste(sent_1_box, sent_1_loc, sent_1_box)
    img.paste(sent_2_box, sent_2_loc, sent_2_box)
    img.paste(sent_3_box, sent_3_loc, sent_3_box)
    img.paste(sent_4_box, sent_4_loc, sent_4_box)
    img.paste(sent_5_box, sent_5_loc, sent_5_box)
    
    img.save(str(REPORT_DIR / target) + '.png')
    img.show()