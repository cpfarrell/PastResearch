#Standard modules
import sys
import cPickle
import argparse
import json
import datetime
import bisect
import random

#Third party modules
import numpy as np
from sklearn import linear_model
from sklearn.externals import joblib
import matplotlib.pyplot as plt

#Attensity media modules
import helper
import ObjectsWithDemo

#Reads test tweets and checks if tweets contain Ngrams found to be useful by LearnGender to attempt to determine the gender of the user.
#Previously determined weights from logistic regression of the Ngrams are used to make the guess.
def main(filename, max_size):
    #Time to start and range to look over
    timebins = [datetime.datetime(2013, 9, 13, 0, 0, 0) + datetime.timedelta(hours = i) for i in range(0, 72)]

    with open('data/ngrams.pkl') as fid:
        ngrams_vars = cPickle.load(fid)
        ngrams = ngrams_vars["ngrams"]
        useful_ngrams = ngrams_vars["useful_ngrams"]

    logistic = joblib.load("data/Logit_C0.1.joblib.pkl")
    tweets_and_info = extract_tweets(filename, ngrams, useful_ngrams, logistic, min_time=timebins[0], max_time=timebins[len(timebins)-1])
    times = [tweet['time'] for tweet in tweets_and_info]
    genders = [tweet['gender'] for tweet in tweets_and_info]
    gender_pred = np.asarray([tweet['gender'] for tweet in tweets_and_info])

    y_total = np.zeros(len(timebins))
    y_men = np.zeros(len(timebins))
    y_women = np.zeros(len(timebins))

    for idx, time in enumerate(times):
        bin = find_bin(timebins, time)
        y_total[bin] += 1
        if gender_pred[idx] == 0:
            y_women[bin] += 1
        else:
            y_men[bin] += 1

    timebins = [bin + datetime.timedelta(minutes = 30) for bin in timebins]

    plt.figure()
    plt.plot(timebins, y_men, label="Men")
    plt.plot(timebins, y_women, label="Women")
    plt.gcf().autofmt_xdate()    
    plt.legend()

    plt.figure()
    plt.plot(timebins, np.divide(y_men, y_men + y_women), label = "ratio")
    plt.gcf().autofmt_xdate()    

    plt.show()

    print "Fraction men " + str(np.average(gender_pred))

#Extract text and gender fields from redis database
def extract_tweets(filename, ngrams, useful_ngrams, logistic, min_time=0, max_time=0):
    #Initialize collection of tweets
    tweets = []

    max_users = sum(1 for line in open(filename))

    f = open(filename, 'r')
    for idx, line in enumerate(f):
        helper.print_fraction(idx, max_users)
        if idx >= (max_users):
            break

        if random.randint(1, 1) !=1:
            continue

        json_dict = json.loads(line)
        if json_dict['content_subtype'] != 'twitter':
            continue

        time = get_date_time(json_dict["published_at"]) - datetime.timedelta(hours = 4)
        
        if min_time != max_time:
            if time < min_time:
                continue
            elif time > max_time:
                print "\n"
                break

        user = json_dict['authors'][0]['screen_name']
        info = {'Name': json_dict['authors'][0]['name'], 'texts': [json_dict['title']]}
        tweet = ObjectsWithDemo.TweetWithDemo(user, info)
        gender = guess_gender(tweet, ngrams, useful_ngrams, logistic)

        tweets.append({"gender": gender, "time":time}) 
    
    return tweets


def guess_gender(tweet, ngrams, useful_ngrams, logistic):
    columns = useful_ngrams["TOTALNUMBEROFUSEFULNGRAMSFOUNDMARKER"] + 1
    X = np.zeros(shape = (1, columns))

    object_ngrams = tweet.create_ngrams(1, 1, 2, 3, 6, 3, 6)
    for ngram in object_ngrams:
        if ngram in ngrams:
            id = ngrams[ngram].Id
            if id in useful_ngrams:
                X[0, useful_ngrams[id] + 1] = 1

    return logistic.predict(X)[0]

def get_date_time(string_date_time):
    return datetime.datetime(int(string_date_time[0:4]), int(string_date_time[5:7]), int(string_date_time[8:10]), int(string_date_time[11:13]), int(string_date_time[14:16]))


#Find leftmost value greater than x
def find_bin(a, x):
    i = bisect.bisect_left(a, x) - 1
    if i != (len(a) - 1):
        return i
    else:
        return -1


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', dest='filename',
                        help='File containing jsons of output from the attensity pipeline', default=None)
    parser.add_argument('-s', '--size', dest='max_size', type=int,
                        help='Number of lines to process in file, default processes whole file', default=-1)

    args = parser.parse_args()

    if args.filename is None:
        print 'Did not specify input file.'
        sys.exit(1)

    main(args.filename, args.max_size)
