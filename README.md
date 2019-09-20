# zeitgeist
Analyze trending twitter topics and use NLP to generate a summary

## Goals

- grab corpus from live twitter data (trending hashtags)
- areas of analysis:
    - sentiment analysis of corpus (tbendlin)
        - are trending topics generally positive or negative?
        - what is the distribution of the sentiment of individual tweets?
        - can we locate particularly "outlier" tweets using sentiment?
    - topic analysis (pgalatic)
        - clean data (remove urls / hashtags)
        - what tweets in this trending hashtag are the most important?
            - can we cluster tweets and then pick tweets that are representative of those clusters?
        - what is the trending hashtag about in a general sense, and can we summarize that programmaticaly?
        - what types of hashtags are more or less difficult to analyze in this way?
    - generating an "abstract" of the trending hashtag (qxh5696)
        - can we make a short paragraph describing a hashtag programmatically?
    - summary statistics
        - what words are the most common?
        - what emojis (if applicable) are the most common?
        
## Agenda

- [ ] 9/19:
    - [x] pgalatic: Implement the data collection algorithm
    - [x] tbendlin: 1st draft of phase 1 report
    - [ ] qxh5696: psuedocode for abstract generation algorithm + its source papers
- [ ] 9/26
    - [ ] pgalatic: phase 1 report edited and submitted and add data cleaning if possible
    - [ ] tbendlin: plan sentiment analysis portion
    - [ ] qxh5696: carryover from 9/19