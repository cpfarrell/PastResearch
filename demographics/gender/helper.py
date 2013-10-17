#Standard modules
import sys
import os
import random
import errno
import heapq

#Third party modules
import numpy as np
from scipy.sparse import *

#Attensity media modules
import ObjectsWithDemo
import gender_terms

#Show how much of the loop we've been through
def print_fraction(count, max):
    if count == 0:        
        sys.stdout.write('         0                   20                  40                  60                  80                  100\n')
        sys.stdout.write('Progress:')
        sys.stdout.flush()

    step = max/100
    if step == 0:
        step = 1

    if count%step == 0:
        sys.stdout.write('.')
        sys.stdout.flush()

    if count == (max - 1):
        sys.stdout.write('\n')
        sys.stdout.flush()

    count +=1


#Extract text and gender fields from redis database
def extract_tweets(users, min_tweets = 0, max_tweets = -1, max_users = -1, test_sample = False):
    #Initialize collection of tweets
    tweets = []

    if max_users == -1:
        max_users = len(users.get_users_with_tweets_by_identifier("GenderTerm"))

    for idx, user in enumerate(users.get_users_with_tweets_by_identifier("GenderTerm")):
        print_fraction(idx, max_users)
        if idx >= (max_users-1):
            break

        #Don't get users in test sample unless this is final evaluation. Not equal acts as an xor
        if users.user_in_test_sample(user) != test_sample:
            continue

        info = users.get_info(user)
        tweet = ObjectsWithDemo.TweetWithDemo(user, info, max_tweets)

        #If user has sent the desired number of tweets
        if len(tweet.texts) >= min_tweets:
            tweets.append(tweet) 
            
    return tweets


#Split collection of objects into training and cross validation sets
#Can be done randomly or selecting out names collected in a particular way for CV
def split_out_cv_random(objects, fraction_cv=0.2):
    cv = list()
    train = list()

    for object in objects:
        cv_split = random.randint(1, 1./fraction_cv)
        if(cv_split==1):
            cv.append(object)
        else:
            train.append(object)

    return {'train': train, 'cv': cv}


#Split collection of objects into training and cross validation sets by terms identified by specific terms. If no TrainTerms given then take all not in CV
def split_out_cv_by_terms(objects, users, cv_terms, train_terms):

    cv = list()
    train = list()

    for object in objects:
        cv_split = 0
        #Check if identified by one of the CV terms
        cv_found = False
        for term in cv_terms:
            if users.user_known_by_identifier(term, object.username):
                cv.append(object)
                cv_found = True
        if cv_found:
            continue

        #If no train terms given assume can use everything else
        if not train_terms:
            train.append(object)
            continue
            
        #Check if determined from one of the train terms
        for term in train_terms:
            if users.user_known_by_identifier(term, object.username):
                train.append(object)
                continue
    return {'train': train, 'cv': cv}



#Builds sparse matrix X where each row is a tweet and each column is a particular Ngram. A cell with a value of zero means that tweet contains that Ngram
#while a value of zero means it does not. Number of columns encoded as UsefulNgrams["TOTALNUMBEROFUSEFULNGRAMSFOUNDMARKER"]
#Also makes y vector of true genders, 0 for female and 1 for male. 
def build_Xy(tweets, useful_ngrams):
    columns = useful_ngrams["TOTALNUMBEROFUSEFULNGRAMSFOUNDMARKER"] + 1
    N_tweets = len(tweets)
    X = lil_matrix((N_tweets, columns))
    y = np.zeros(N_tweets)

    for Idx, tweet in enumerate(tweets):
        #Checks for presence of Ngrams
        for Ngram_id in tweet.ngram_ids:
            if Ngram_id in useful_ngrams:
                X[Idx, useful_ngrams[Ngram_id] + 1] = 1
        if(tweet.gender=="male"): y[Idx] = 1
        
    X = X.tocsr()
    return {'X':X, 'y':y}


#Extract Ngrams and keep demographic information about them from objects which have their own function "create_ngrams()".
#Keep track of the total number of times Ngrams found for each gender stored in "TOTALGENDERCOUNTER"
def extract_ngrams(objects, ngrams, max_tweets = -1, min_tweet_words = 1, max_tweet_words = 2,
                  min_name_words = 3, max_name_words = 6, min_username_chars = 3, max_username_chars = 6, for_cv_tweets = False):

    gt = gender_terms.GenderTerms()
    male_terms = gt.get_male_terms()
    female_terms = gt.get_female_terms()

    #Initialize
    if "TOTALGENDERCOUNTER" not in ngrams:
        ngrams["TOTALGENDERCOUNTER"] = ObjectsWithDemo.NgramsWithDemo()

    for idx, object in enumerate(objects):
        print_fraction(idx, len(objects))
        object_ngrams = object.create_ngrams(max_tweets, min_tweet_words, max_tweet_words, min_name_words, max_name_words, min_username_chars, max_username_chars)

        for ngram in object_ngrams:
            #Don't want to bias result with the words I collected with
            if ngram in male_terms or ngram in female_terms:
                continue

            if ngram not in ngrams:
                if for_cv_tweets:
                    continue
                else:
                    ngrams[ngram] = ObjectsWithDemo.NgramsWithDemo()
            object.ngram_ids.add(ngrams[ngram].Id)

            #Would be a bias to use CV tweets to fill the dict we find useful Ngrams from
            if for_cv_tweets:
                continue

            #Increment the Ngram
            ngrams[ngram].increment_gender(object.gender)
            #Increment total counter for each gender
            ngrams["TOTALGENDERCOUNTER"].increment_gender(object.gender)

    return ngrams
            

#Build all combinations of N grams (only includes N length grams, not N-1 or smaller
def make_ngrams(grams, N=1, prepend=""):
    ngrams = list()

    #Loop from N-1 element to end

    for offset in range(N-1, len(grams)):
        ngram = " " + prepend
        
        #Fill in the grams before the offset one to create the N-grams
        for i in range(N):
            ngram = grams[offset-i] + " " + ngram

        ngrams.append(ngram)


    return ngrams

#Prepare creation of N grams of length Min to Max
def make_multi_ngrams(grams, Min=1, Max=3, prepend=""):

    ngrams = list()
    for i in range(Min,Max+1):        
        for ngram in make_ngrams(grams, i, prepend):
            ngrams.append(ngram)

    return ngrams


def top_ngrams(ngrams, gender, N=10, min = 50, type=""):

    #Want most male or female Ngrams
    sign = 1
    if gender == "male":
        sign = -1

    top_ngrams = []

    for ngram in ngrams:
        if type != "" and type != ngram[len(ngram)-1]:
            continue

        count = ngrams[ngram].male_count + ngrams[ngram].female_count
        if count < min:
            continue

        heapq.heappush(top_ngrams, (sign * float(ngrams[ngram].female_count)/count, ngram))
        if (len(top_ngrams)>N):
            heapq.heappop(top_ngrams)

    return sorted(top_ngrams, reverse = True)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


def write_output(filename, y_true, y_pred, tweets, users):
    gt = gender_terms.GenderTerms()
    terms = gt.get_male_terms()
    terms.update(gt.get_female_terms())
    terms.add("FirstName")

    f_csv = open(filename, 'w')
    for idx, tweet in enumerate(tweets):
        identifiers = ""
        for term in terms:
            if users.user_known_by_identifier(term, tweet.username):
                identifiers += ", " + term
        csv_output_string = str(y_true[idx]) + ", " + str(y_pred[idx]) + ", " + str(len(tweet.texts)) + identifiers + "\n"
        f_csv.write(csv_output_string.encode('utf8') )
    f_csv.close()
