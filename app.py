import re
import os
import nltk
import joblib
import requests
import numpy as np
from bs4 import BeautifulSoup
import urllib.request as urllib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
from wordcloud import WordCloud, STOPWORDS
from flask import Flask, render_template, request
import time
import concurrent.futures  # Import for multithreading

# nltk.download('stopwords')
# nltk.download('punkt')
# nltk.download('wordnet')

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# word_2_int = joblib.load('word2int.sav')
# model = joblib.load('sentiment.sav')
# stop_words = set(open('stopwords.txt'))

def clean(x):
    x = re.sub(r'[^a-zA-Z ]', ' ', x)  # replace everything that's not an alphabet with a space
    x = re.sub(r'\s+', ' ', x)  # replace multiple spaces with one space
    x = re.sub(r'READ MORE', '', x)  # remove READ MORE
    x = x.lower()
    x = x.split()
    y = []
    for i in x:
        if len(i) >= 3:
            if i == 'osm':
                y.append('awesome')
            elif i == 'nyc':
                y.append('nice')
            elif i == 'thanku':
                y.append('thanks')
            elif i == 'superb':
                y.append('super')
            else:
                y.append(i)
    return ' '.join(y)


def extract_all_reviews(url, clean_reviews, org_reviews, customernames, commentheads, ratings, nreviews):
    page_number = 1
    num_reviews_fetched = 0

    while True:
        url2 = url + f'&page={page_number}'
        with urllib.urlopen(url2) as u:
            page = u.read()
            page_html = BeautifulSoup(page, "html.parser")

        reviews = page_html.find_all('div', {'class': 't-ZTKy'})
        commentheads_ = page_html.find_all('p', {'class': '_2-N8zT'})
        customernames_ = page_html.find_all('p', {'class': '_2sc7ZR _2V5EHH'})
        ratings_ = page_html.find_all('div', {'class': ['_3LWZlK _1BLPMq', '_3LWZlK _32lA32 _1BLPMq', '_3LWZlK _1rdVr6 _1BLPMq']})

        if not reviews:
            break  # No more reviews on the current page, so break the loop

        for review in reviews:
            x = review.get_text()
            org_reviews.append(re.sub(r'READ MORE', '', x))
            clean_reviews.append(clean(x))

        for cn in customernames_:
            customernames.append('~' + cn.get_text())

        for ch in commentheads_:
            commentheads.append(ch.get_text())

        ra = []
        for r in ratings_:
            try:
                if int(r.get_text()) in [1, 2, 3, 4, 5]:
                    ra.append(int(r.get_text()))
                else:
                    ra.append(0)
            except:
                ra.append(r.get_text())

        ratings += ra

        num_reviews_fetched += len(reviews)
        if num_reviews_fetched >= nreviews:
            break  # Stop fetching reviews once the desired number is reached

        page_number += 1  # Move to the next page

    return num_reviews_fetched


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/results', methods=['GET'])
@app.route('/results', methods=['GET'])
def result():
    url = request.args.get('url')
    nreviews = request.args.get('num')
    # Default to fetching 10 reviews if no number is provided
    if nreviews is None or nreviews == '':
        nreviews = 10
    else:
        nreviews = int(nreviews)

    clean_reviews = []
    org_reviews = []
    customernames = []
    commentheads = []
    ratings = []

    with urllib.urlopen(url) as u:
        page = u.read()
        page_html = BeautifulSoup(page, "html.parser")

    proname = page_html.find_all('span', {'class': 'B_NuCI'})[0].get_text()
    price = page_html.find_all('div', {'class': '_30jeq3 _16Jk6d'})[0].get_text()

    # getting the link of see all reviews button
    all_reviews_url = page_html.find_all('div', {'class': 'col JOpGWq'})[0]
    all_reviews_url = all_reviews_url.find_all('a')[-1]
    all_reviews_url = 'https://www.flipkart.com' + all_reviews_url.get('href')
    url2 = all_reviews_url + '&page=1'

    num_reviews = 0  # Variable to keep track of the number of reviews extracted
    # Start measuring time for fetching reviews
    start_time_fetching = time.time()

    # Fetch reviews using multithreading for faster processing
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_page_number = {executor.submit(extract_all_reviews, url2, clean_reviews, org_reviews, customernames, commentheads, ratings, nreviews): page_number for page_number in range(1, 6)}
        for future in concurrent.futures.as_completed(future_to_page_number):
            num_reviews_iter = future.result()
            num_reviews += num_reviews_iter
            if num_reviews >= nreviews:
                break

    # Stop measuring time for fetching reviews
    end_time_fetching = time.time()
    time_taken_fetching = end_time_fetching - start_time_fetching
    print(f"Time taken to fetch reviews: {time_taken_fetching:.2f} seconds")

    org_reviews = org_reviews[:num_reviews]
    clean_reviews = clean_reviews[:num_reviews]
    customernames = customernames[:num_reviews]
    commentheads = commentheads[:num_reviews]
    ratings = ratings[:num_reviews]

    # Start measuring time for generating word cloud
    start_time_wordcloud = time.time()
    # building our wordcloud and saving it
    for_wc = ' '.join(clean_reviews)
    wcstops = set(STOPWORDS)
    wc = WordCloud(width=1400, height=800, stopwords=wcstops, background_color='white').generate(for_wc)
    plt.figure(figsize=(20, 10), facecolor='k', edgecolor='k')
    plt.imshow(wc, interpolation='bicubic')
    plt.axis('off')
    plt.tight_layout()
    CleanCache(directory='static/images')
    plt.savefig('static/images/woc.png')
    plt.close()
    # Stop measuring time for generating word cloud
    end_time_wordcloud = time.time()
    time_taken_wordcloud = end_time_wordcloud - start_time_wordcloud
    print(f"Time taken to generate word cloud: {time_taken_wordcloud:.2f} seconds")

    # predictions = []
    # for i in range(len(org_reviews)):
    #     vector = tokens_2_vectors(tokenizer(clean_reviews[i]))
    #     vector = vector[:-1]
    #     if model.predict([vector])[0] == 1:
    #         predictions.append('POSITIVE')
    #     else:
    #         predictions.append('NEGATIVE')

    # making a dictionary of product attributes and saving all the products in a list
    d = []
    for i in range(len(org_reviews)):
        x = {}
        x['review'] = org_reviews[i]
        # x['sent'] = predictions[i]
        x['cn'] = customernames[i]
        x['ch'] = commentheads[i]
        x['stars'] = ratings[i]
        d.append(x)

    for i in d:
        if i['stars'] != 0:
            if i['stars'] in [1, 2]:
                i['sent'] = 'NEGATIVE'
            else:
                i['sent'] = 'POSITIVE'

    np, nn = 0, 0
    for i in d:
        if i['sent'] == 'NEGATIVE':
            nn += 1
        else:
            np += 1

    return render_template('result.html', dic=d, n=num_reviews, nn=nn, np=np, proname=proname, price=price)


@app.route('/wc')
def wc():
    return render_template('wc.html')


class CleanCache:
    '''
    this class is responsible to clear any residual csv and image files
    present due to the past searches made.
    '''

    def __init__(self, directory=None):
        self.clean_path = directory
        # only proceed if directory is not empty
        if os.listdir(self.clean_path) != list():
            # iterate over the files and remove each file
            files = os.listdir(self.clean_path)
            for fileName in files:
                print(fileName)
                os.remove(os.path.join(self.clean_path, fileName))
        print("cleaned!")


if __name__ == '__main__':
    app.run(debug=True, threaded=False)
