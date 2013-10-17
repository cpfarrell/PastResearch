import sys
import math
import helper
import cPickle

#Third party modules
from sklearn import linear_model
from sklearn.naive_bayes import MultinomialNB
from sklearn.externals import joblib

#Attensity Media Modules
import ObjectsWithDemo
import gender_terms
sys.path.append('../UserDatabase/')
import user_database

users = user_database.UserDatabase()

#Reads in file with tweets containing text and gender. File split into training set and cross validation set containing 1/5 of the tweets. Ngrams which appear at
#different rates in male and female tweets are identified. These Ngrams are then used to try and guess the gender of the users in the cross validation set
#using logistic regression.
def main():
    #Parameters
    show_useful_ngrams = False
    best_cv_score = 0.

    #Where to store files measuring how models performed
    directory = "data/"
    helper.mkdir_p(directory)

    print "Extracting tweets from database"
    tweets = helper.extract_tweets(users, max_users = -1, max_tweets = 1, min_tweets = 1)

    #Can split out CV randomly or by specific terms
    print "Splitting out CV"
    #split_tweets = helper.split_out_cv_by_terms(tweets, users, cv_terms = ["husband", "wife"], train_terms = [])
    split_tweets = helper.split_out_cv_random(tweets)
    train_tweets = split_tweets["train"]
    cv_tweets = split_tweets["cv"]

    out_string = 'Running with ' + str(len(train_tweets)) + ' training tweets and ' + str(len(cv_tweets)) + ' cross-validation tweets'
    sys.stdout.write(out_string + '\n')

    #Build Ngrams for train tweets, make this general
    print "Building Train Ngrams"
    #ngrams maps the actual ngram to a unique id
    ngrams = {}
    helper.extract_ngrams(train_tweets, ngrams)
    print "Number of Ngrams " + str(len(ngrams))

    counts = [2, 6, 10]
    min_sig = [0.2, 0.7, 1.2]
    filename = directory + "Scores"

    if show_useful_ngrams:
        print_useful_ngrams(ngrams, 100, type = "T")

    print "Building Cross-Validation Ngrams"
    #useful_ngrams maps the ngram id to the column it occupies in matrix
    useful_ngrams = find_useful_ngrams(ngrams, min_count=5, min_significance=0.5)

    helper.extract_ngrams(cv_tweets, ngrams, for_cv_tweets = True)
    with open('data/ngrams.pkl', 'wb') as fid:
        cPickle.dump({"ngrams": ngrams, "useful_ngrams": useful_ngrams}, fid)

    print "Building training matrix"
    train_vars = helper.build_Xy(train_tweets, useful_ngrams)
    X_train = train_vars["X"]
    y_train = train_vars["y"]

    print "Building cross-validation matrix"
    cv_vars = helper.build_Xy(cv_tweets, useful_ngrams)
    X_cv = cv_vars["X"]
    y_cv = cv_vars["y"]

    logit_score = logistic_regression(X_train, y_train, X_cv, y_cv, train_tweets, cv_tweets, directory + "Logit")
    if logit_score > best_cv_score:
        best_cv_score = logit_score

    nb_score = naive_bayes(X_train, y_train, X_cv, y_cv, train_tweets, cv_tweets, directory + "MultiNB")
    if nb_score > nb_score:
        best_cv_score = nb_score

    print('Best CV score: %(score)f'% {"score":best_cv_score})



#Find useful Ngrams defined as those with total number of appearances greater than MinCount and with a difference in the rate of appearing in male and female
#different from zero with a zignificance greater than MinSig. 
#The total number of useful Ngrams found is encoded in UsefulNgrams hashmap with the key "TOTALNUMBEROFUSEFULNGRAMSFOUNDMARKER"
def find_useful_ngrams(ngrams, min_count=5, min_significance=0.4):
    useful_ngrams = {}

    female_total = ngrams["TOTALGENDERCOUNTER"].get_gender_count("female")
    male_total = ngrams["TOTALGENDERCOUNTER"].get_gender_count("male")

    columns = 0

    for Ngram in ngrams.keys():
        #Special encoding
        if Ngram == "TOTALGENDERCOUNTER":
            continue

        female_count = ngrams[Ngram].get_gender_count("female")
        male_count = ngrams[Ngram].get_gender_count("male")
        sum = female_count + male_count

        female_average = float(female_count)/female_total
        male_average = float(male_count)/male_total
        difference = female_average - male_average
        uncertainty = math.sqrt((female_average/female_total) + (male_average/male_total))
        sig_diff = difference/uncertainty

        #Store only Ngrams which are significant and appear a certain number of times
        if(math.fabs(sig_diff) > min_significance and sum > min_count):
            
            if(Ngram not in useful_ngrams):
                useful_ngrams[ngrams[Ngram].Id] = columns
                columns += 1
        
        else:
            #Free some memory
            ngrams.pop(Ngram, None)

    #Encode the total number of columns with the key TOTALNUMBEROFUSEFULNGRAMSFOUNDMARKER            
    useful_ngrams["TOTALNUMBEROFUSEFULNGRAMSFOUNDMARKER"] = columns
    return useful_ngrams


def logistic_regression(X_train, y_train, X_cv, y_cv, train_tweets, cv_tweets, filename):
    C_regs = [0.03, 0.1, 0.3, 1.0, 3.0]
#    C_regs = [0.1]
    best_cv_score = 0.
    best_C = 0

    for C_reg in C_regs:
        print "Doing fit"
        logistic = linear_model.LogisticRegression(penalty="l2", C=C_reg)
        logistic.fit(X_train, y_train)

        cv_score = logistic.score(X_cv, y_cv)
        print('Train LogisticRegression score: %f'% logistic.score(X_train, y_train))
        print('CV LogisticRegression score: %(score)f for C_reg = %(C)f'% {"score": cv_score, "C": C_reg})
        y_cv_pred = logistic.predict(X_cv)

        if cv_score > best_cv_score:
            best_cv_score = cv_score
            best_C = C_reg

        helper.write_output(filename + "_C" + str(C_reg) + ".csv", y_cv, y_cv_pred, cv_tweets, users)
        joblib.dump(logistic, filename + "_C" + str(C_reg) + ".joblib.pkl", compress=9)

    return best_cv_score


def naive_bayes(X_train, y_train, X_cv, y_cv, train_tweets, cv_tweets, filename):
    alphas = [0.01, 0.1, 1, 10, 100]
    best_cv_score = 0.
    best_alpha = 0

    for alpha in alphas:
        print "Doing fit"
        mnb = MultinomialNB(alpha=alpha)
        mnb.fit(X_train, y_train)

        y_cv_pred = mnb.predict(X_cv)
        cv_score = mnb.score(X_cv, y_cv)
        print('CV Multinomial NB score: %(score)f for alpha = %(alpha)f'% {"score": cv_score, "alpha": alpha})

        if cv_score > best_cv_score:
            best_cv_score = cv_score
            best_alpha = alpha

        helper.write_output(filename + "_alpha" + str(alpha) + ".csv", y_cv, y_cv_pred, cv_tweets, users)

    return best_cv_score


def print_useful_ngrams(ngrams, N, type=""):
    print '\nShowing useful Ngrams for men\n'
    
    for ngram in helper.top_ngrams(ngrams, "male", N=N, type=type):
        print (ngram[1] + " " + " Male Counts = " + str(ngrams[ngram[1]].male_count) + " Female Counts = " + str(ngrams[ngram[1]].female_count)
               + " Significance " + str(ngrams[ngram[1]].significance(ngrams)))

    print '\nShowing useful Ngrams for women\n'
    for ngram in helper.top_ngrams(ngrams, "female", N=N, type=type):
        print (ngram[1] + " " + " Male Counts = " + str(ngrams[ngram[1]].male_count) + " Female Counts = " + str(ngrams[ngram[1]].female_count)
                 + " Significance " + str(ngrams[ngram[1]].significance(ngrams)))


if __name__ == '__main__':
    main()
