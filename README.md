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
        - what tweets in this trending hashtag are the most important?
        - what is the trending hashtag about in a general sense, and can we summarize that programmaticaly?
        - what types of hashtags are more or less difficult to analyze in this way?
    - generating an "abstract" of the trending hashtag (qxh5696)
        - can we make a short paragraph describing a hashtag programmatically?
    - summary statistics
        - what words are the most common?
        - what emojis (if applicable) are the most common?
        
## Agenda

- [ ] 9/16:
    - pgalatic: Implement the data collection algorithm
    - tbendlin: 1st draft of phase 1 report
    - qxh5696: psuedocode for abstract generation algorithm + its source papers