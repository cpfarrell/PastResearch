#Standard modules
import sys
import cPickle

#Third party modules
import numpy as np
from sklearn import linear_model
from sklearn.externals import joblib

import helper
sys.path.append('../UserDatabase/')
import user_database

#Reads test tweets and checks if tweets contain Ngrams found to be useful by LearnGender to attempt to determine the gender of the user.
#Previously determined weights from logistic regression of the Ngrams are used to make the guess.
def main():

    users = user_database.UserDatabase()
    test_tweets = helper.extract_tweets(users, max_users = -1, max_tweets = 1, min_tweets = 1, test_sample = True)
    print len(test_tweets)

    with open('ngrams.pkl') as fid:
        ngrams_vars = cPickle.load(fid)
        ngrams = ngrams_vars["ngrams"]
        useful_ngrams = ngrams_vars["useful_ngrams"]

    helper.extract_ngrams(test_tweets, ngrams, for_cv_tweets = True)
    test_vars = helper.build_Xy(test_tweets, useful_ngrams)
    X_test = test_vars["X"]
    y_test = test_vars["y"]

    logistic = joblib.load("Results/Log_Testing/Logit_C0.1.joblib.pkl")
    print('Test Logistic Regression score: %f'%logistic.score(X_test, y_test))
    y_test_pred = logistic.predict(X_test)
    helper.write_output("Results/Log_Testing/TestUsers.csv", y_test, y_test_pred, test_tweets, users)

if __name__ == '__main__':
    main()
