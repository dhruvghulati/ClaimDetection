import math
import numpy as np
from sklearn import datasets
from sklearn.cross_validation import train_test_split
# from vowpalwabbit.sklearn_vw import VWClassifier
import re
from nltk.corpus import stopwords  # Import the stop word list
from numpy.matlib import empty
import matplotlib.pyplot as plt
import json
import numpy as np
import pandas as pd
from sklearn import datasets
from sklearn import preprocessing
import subprocess
from sklearn.cross_validation import train_test_split
import sys
from sklearn.metrics import precision_score
from sklearn.metrics import accuracy_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import precision_recall_fscore_support
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
import os
from itertools import repeat

# np.set_printoptions(threshold=np.inf)

rng = np.random.RandomState(101)

def sigmoid(x):
  return 1 / (1 + math.exp(-x))

def sentence_to_words(sentence, remove_stopwords=False):
    letters_only = re.sub('[^a-zA-Z| LOCATION_SLOT | NUMBER_SLOT]', " ", sentence)
    # [x.strip() for x in re.findall('\s*(\w+|\W+)', line)]
    words = letters_only.lower().split()

    # In Python, searching a set is much faster than searching a list, so convert the stop words to a set
    if remove_stopwords:
        stops = set(stopwords.words("english"))
        words = [w for w in words if not w in stops]
    return (words)

# def costMatrix(inputSentences):
#     ocmt = empty((len(inputSentences), 4))
#     for i in xrange(ocmt.shape[0]):
#         ocmt[i, 0] = np.random.random()
#     ocmt[:, 1] = ocmt[:, 0] + 1
#     ocmt[:, 2] = 10*ocmt[:, 0]
#     ocmt[:, 3] = ocmt[:, 0]/10
#     return ocmt


def multiVowpalFormat(costVector, trainingLabels, trainingFeatures, datFile):

    # TODO - make sure this opens a fresh file all the time and replaces
    f = open(datFile, 'w')

    print "There are this many unique labels",len(set(trainingLabels))

    for i, (label, cost, features) in enumerate(zip(trainingLabels,costVector,trainingFeatures)):
        line = str(label) + ":" + str(cost) + " " + str(i) + "|" + (" ").join(map(str, features))
        f.write(line+"\n")

    f.close()

def training_features(inputSentences):
    global vectorizer
    global open_cost_mat_train
    global closed_cost_mat_train
    global open_cost_mat_train_1
    global closed_cost_mat_train_1
    global open_cost_mat_train_2
    global closed_cost_mat_train_2
    # [:15000]
    # plt.ion()

    for i, sentence in enumerate(inputSentences[:15000]):
        # Dont train if the sentence contains a random region we don't care about
        # and sentence['predictedRegion'] in properties
        if sentence:
            # Regardless of anything else, an open evaluation includes all sentences
            train_wordlist.append(" ".join(sentence_to_words(sentence['parsedSentence'], True)))
            train_property_labels.append(sentence['predictedPropertyOpen'])
            train_property_labels_threshold.append(sentence['predictedPropertyOpenThreshold'])
            # Closed evaluation only include certain training sentences
            closed_train_property_labels.append(sentence['predictedPropertyClosed'])
            closed_train_property_labels_threshold.append(sentence['predictedPropertyClosedThreshold'])
            # cost_mat[C_FP,C_FN,C_TP,C_TN]
            # TODO - test different versions of this
            # Now analyse the distribution of the costs. One method is to remove the value I chose and look at the median, IQR and mode of the other values.
            openCostVectorRem = np.sort([value for i,value in enumerate(sentence['openCostArr']) if value is not sentence['meanAbsError']])
            closedCostVectorRem = np.sort([value for i,value in enumerate(sentence['closedCostArr']) if value is not sentence['closedMeanAbsError']])
            # print "Sentence is ",sentence['sentence']
            # print "Error is",sentence['meanAbsError']
            # print "Remaining array is",openCostVectorRem
            openIQR = float(np.subtract(*np.percentile(openCostVectorRem, [75, 25])))
            closedIQR = float(np.subtract(*np.percentile(closedCostVectorRem, [75, 25])))
            openMedian = float(np.median(openCostVectorRem))
            closedMedian = float(np.median(closedCostVectorRem))
            openGap = sentence['openCostArr'][1]-sentence['meanAbsError']
            print "Open gap is",openGap
            closedGap = sentence['closedCostArr'][1]-sentence['closedMeanAbsError']
            print "Closed gap is",closedGap
            maxClosedErr = sentence['closedCostArr'][len(sentence['closedCostArr'])-1]
            print "maxClosedErr is",maxClosedErr
            closedRange = np.ptp(sentence['closedCostArr'])
            print "Closed range is",closedRange

            ybins = [0,0.25,0.5,0.75,1]

            squeezeClosedArray = np.digitize(sentence['closedCostArr'], ybins, right=False)

            factor = squeezeClosedArray.tolist().count(1)
            print "Factor is",factor

            print "Squeezed closed array is ",squeezeClosedArray

            # open_cost_mat = np.array([sentence['meanAbsError'],0.0,0.0,0.0],dtype=float)
            # open_cost_mat_train = np.vstack([open_cost_mat_train,sentence['meanAbsError']])
            open_cost_mat_train = np.append(open_cost_mat_train,sentence['meanAbsError'])
            # open_cost_mat_1 = np.array([sentence['costSensitiveOpenError1'],0.0,0.0,0.0],dtype=float)
            # print [value for value in sentence["openCostArr"]]

            open_cost_mat_train_1 = np.append(open_cost_mat_train_1,sentence['meanAbsError']/float(openIQR*(len(openCostVectorRem)+1)))
            # # open_cost_mat_2 = np.array([sentence['costSensitiveOpenError2'],0.0,0.0,0.0],dtype=float)
            open_cost_mat_train_2 = np.append(open_cost_mat_train_2,sentence['meanAbsError']/float(openMedian*(len(openCostVectorRem)+1)))
            # # closed_cost_mat = np.array([sentence['closedMeanAbsError'],0.0,0.0,0.0],dtype=float)
            closed_cost_mat_train = np.append(closed_cost_mat_train,sentence['closedMeanAbsError'])
            # # closed_cost_mat_1 = np.array([sentence['costSensitiveClosedError1'],0.0,0.0,0.0],dtype=float)
            closed_cost_mat_train_1 = np.append(closed_cost_mat_train_1,sentence['closedMeanAbsError']/float(closedIQR*(len(openCostVectorRem)+1)))
            # # closed_cost_mat_2 = np.array([sentence['costSensitiveClosedError2'],0.0,0.0,0.0],dtype=float)
            closed_cost_mat_train_2 = np.append(closed_cost_mat_train_2,sentence['closedMeanAbsError']/float(closedMedian*(len(openCostVectorRem)+1)))

            # calculate the proportional values of samples
            # p = 1. * np.arange(len(sentence['openCostArr'])) / (len(sentence['openCostArr']) - 1)
            # print "array is ",sentence['openCostArr']
            # print "p is ",p

            squeezeClosedArray2 = [val/maxClosedErr for val in sentence['closedCostArr']]
            # print "array is ",sentence['openCostArr']
            print "p2 is ",squeezeClosedArray2
            # TODO this could be a hyperparam
            print "Sum is",sum(float(i) < 0.000000000000001 for i in squeezeClosedArray2)

            closedGapPercent = closedGap/maxClosedErr
            closedGapPercent2 = closedGap/closedRange
            print "closedGapPercent is ",closedGapPercent
            # TODO - these are the same
            print "closedGapPercent2 is",closedGapPercent2
            #
            # # plot the sort ed data:
            # fig = plt.figure()
            # ax1 = fig.add_subplot(121)
            # ax1.plot(p, sentence['openCostArr'])
            # ax1.set_xlabel('$p$')
            # ax1.set_ylabel('$x$')
            #
            # ax2 = fig.add_subplot(122)
            # ax2.plot(sentence['openCostArr'], p)
            # ax2.set_xlabel('$x$')
            # ax2.set_ylabel('$p$')
            # fig.show()
            # _ = raw_input("Press [enter] to continue.")

    # print "These are the clean words in the training sentences: ", train_wordlist
    # print "These are the labels in the training sentences: ", train_labels
    print "Creating the bag of words...\n"
    train_data_features = vectorizer.fit_transform(train_wordlist)
    train_data_features = train_data_features.toarray()
    train_data_features = train_data_features.astype(np.float)

    return train_data_features


def test_features(testSentences):
    global vectorizer
    global cost_mat_test

    for sentence in testSentences:
        if sentence['parsedSentence'] != {} and sentence['mape_label'] != {}:
            clean_test_sentences.append(" ".join(sentence_to_words(sentence['parsedSentence'], True)))
            test_property_labels.append(sentence['property'])
    # print "These are the clean words in the test sentences: ", clean_test_sentences
    # print "These are the mape labels in the test sentences: ", binary_test_labels
    test_data_features = vectorizer.transform(clean_test_sentences)
    test_data_features = test_data_features.toarray()

    return test_data_features

if __name__ == "__main__":
    # training data
    # load the sentence file for training

    with open(sys.argv[1]) as trainingSentences:
        pattern2regions = json.loads(trainingSentences.read())

    print "We have ", len(pattern2regions), " training sentences."
    # We load in the allowable features and also no_region
    with open(sys.argv[3]) as featuresKept:
        properties = json.loads(featuresKept.read())
    properties.append("no_region")

    with open(sys.argv[2]) as testSentences:
        testSentences = json.loads(testSentences.read())

    probThreshold = float(sys.argv[6])

    finalTestSentences = []

    for sentence in testSentences:
        if sentence['parsedSentence'] != {} and sentence['mape_label'] != {} and sentence['mape'] != {} and sentence[
            'property'] != {} and sentence['property'] in properties:
            # print sentence['property']
            finalTestSentences.append(sentence)

    train_wordlist = []
    closed_train_wordlist = []
    test_wordlist = []
    train_property_labels = []
    train_property_labels_threshold = []
    closed_train_property_labels = []
    closed_train_property_labels_threshold = []
    test_property_labels = []

    # open_cost_mat_train = np.array([],dtype=float).reshape((0,4))
    open_cost_mat_train = np.array([])
    closed_cost_mat_train = np.array([])
    open_cost_mat_train_1 = np.array([])
    closed_cost_mat_train_1 = np.array([])
    open_cost_mat_train_2 = np.array([])
    closed_cost_mat_train_2 = np.array([])

    # cost_matrices = {}
    #
    # for x in range(1,5):
    #     cost_matrices["open_cost_mat_train_{0}".format(x)]=np.array([])
    #     cost_matrices["closed_cost_mat_train_{0}".format(x)]=np.array([])
    #
    # print cost_matrices



    vectorizer = CountVectorizer(analyzer="word", \
                                 tokenizer=None, \
                                 preprocessor=None, \
                                 stop_words=None, \
                                 max_features=5000)

    print "Getting all the words in the training sentences...\n"

    # This both sorts out the features and the training labels
    train_data_features = training_features(pattern2regions)



    # open_cost_mat_train = costMatrix(pattern2regions)
    # closed_cost_mat_train = costMatrix(pattern2regions)
    # cost_mat_test = costMatrix(finalTestSentences)

    print len(train_data_features), "sets of training features"

    # print train_data_features[:10]

    print "This is the open cost matrix",open_cost_mat_train[:10]
    print "This is the closed cost matrix",closed_cost_mat_train[:10]
    print "This is the open cost matrix 1",open_cost_mat_train_1[:10]
    print "This is the closed cost matrix 1",closed_cost_mat_train_2[:10]
    print "This is the open cost matrix 2",open_cost_mat_train_2[:10]
    print "This is the closed cost matrix 2",closed_cost_mat_train_2[:10]

    #
    trainingLabels = len(train_data_features)
    positiveOpenTrainingLabels = len(train_property_labels_threshold) - train_property_labels_threshold.count(
        "no_region")
    negativeOpenTrainingLabels = train_property_labels_threshold.count("no_region")
    positiveClosedTrainingLabels = len(closed_train_property_labels_threshold) - closed_train_property_labels_threshold.count(
        "no_region")
    negativeClosedTrainingLabels = closed_train_property_labels_threshold.count(
        "no_region")
    #
    #
    # print "There are ", len(train_property_labels_threshold) - train_property_labels_threshold.count(
    #     "no_region"), "positive open mape threshold labels"
    # print "There are ", train_property_labels_threshold.count("no_region"), "negative open mape threshold labels"
    # print "There are ", len(closed_train_property_labels_threshold) - closed_train_property_labels_threshold.count(
    #     "no_region"), "positive closed mape threshold labels"
    # print "There are ", closed_train_property_labels_threshold.count(
    #     "no_region"), "negative closed mape threshold labels\n"

    multi_logit = LogisticRegression(fit_intercept=True, class_weight='auto', multi_class='multinomial',
                                     solver='newton-cg')

    multi_logit_threshold = LogisticRegression(fit_intercept=True, class_weight='auto', multi_class='multinomial',
                                               solver='newton-cg')

    closed_multi_logit = LogisticRegression(fit_intercept=True, class_weight='auto', multi_class='multinomial',
                                            solver='newton-cg')

    closed_multi_logit_threshold = LogisticRegression(fit_intercept=True, class_weight='auto',
                                                      multi_class='multinomial',
                                                      solver='newton-cg')

    # Fit the logistic classifiers to the training set, using the bag of words as features

    openTrainingClasses = len(set(train_property_labels))
    openTrainingClassesThreshold = len(set(train_property_labels_threshold))
    closedTrainingClasses = len(set(closed_train_property_labels))
    closedTrainingClassesThreshold = len(set(closed_train_property_labels_threshold))


    print "There are ", len(set(train_property_labels)), "open training classes"
    print "There are ", len(set(train_property_labels_threshold)), "open training classes w/threshold"
    print "There are ", len(set(closed_train_property_labels)), "closed training properties"
    print "There are ", len(set(closed_train_property_labels_threshold)), "closed training properties w/ threshold"

    # Create an empty list and append the clean reviews one by one
    clean_test_sentences = []

    print "Cleaning and parsing the test set ...\n"

    print "Get a bag of words for the test set, and convert to a numpy array\n"

    test_data_features = test_features(finalTestSentences)

    print len(test_data_features), "sets of test features"

    # print test_data_features

    #
    #
    # print "Fitting the open multinomial logistic regression model without MAPE threshold...\n"
    # open_multi_logit = multi_logit.fit(train_data_features, train_property_labels)
    # print "Fitting the open multinomial logistic regression model w/ MAPE threshold...\n"
    # open_threshold_multi_logit = multi_logit_threshold.fit(train_data_features, train_property_labels_threshold)
    # print "Fitting the closed multinomial logistic regression model without MAPE threshold...\n"
    # closed_multi_logit = closed_multi_logit.fit(train_data_features, closed_train_property_labels)
    # print "Fitting the closed multinomial logistic regression model with MAPE threshold...\n"
    # closed_threshold_multi_logit = closed_multi_logit_threshold.fit(train_data_features,
    #                                                                 closed_train_property_labels_threshold)
    #
    # print "Predicting open multinomial test labels w/ threshold...\n"
    # y_multi_logit_result_open_threshold = np.array(open_threshold_multi_logit.predict(test_data_features))
    # print "Predicting closed multinomial test labels w/ threshold...\n"
    # y_multi_logit_result_closed_threshold = np.array(closed_threshold_multi_logit.predict(test_data_features))
    # print "Predicting open multinomial test labels w/ threshold...\n"
    # y_multi_logit_result_open_threshold = np.array(open_threshold_multi_logit.predict(test_data_features))
    # print "Predicting closed multinomial test labels w/ threshold...\n"
    # y_multi_logit_result_closed_threshold = np.array(closed_threshold_multi_logit.predict(test_data_features))


    '''
    Cost sensitive classification
    '''

    # TODO - make code modular

    open_cost_category_path = os.path.join(sys.argv[4] +'/openCostClassifier.dat')
    closed_cost_category_path = os.path.join(sys.argv[4] +'/closedCostClassifier.dat')
    open_cost_category_path_1 = os.path.join(sys.argv[4] +'/openCostClassifier_1.dat')
    closed_cost_category_path_1 = os.path.join(sys.argv[4] +'/closedCostClassifier_1.dat')
    open_cost_category_path_2 = os.path.join(sys.argv[4] +'/openCostClassifier_2.dat')
    closed_cost_category_path_2 = os.path.join(sys.argv[4] +'/closedCostClassifier_2.dat')


    openle = preprocessing.LabelEncoder()
    closedle = preprocessing.LabelEncoder()

    openle.fit(train_property_labels)
    train_property_labels = openle.transform(train_property_labels)

    closedle.fit(closed_train_property_labels)
    closed_train_property_labels = closedle.transform(closed_train_property_labels)
    #
    #
    # print "Writing files to vowpal wabbit format\n"
    # csoaa_open = multiVowpalFormat(open_cost_mat_train,train_property_labels,train_data_features,open_cost_category_path)
    # csoaa_closed = multiVowpalFormat(closed_cost_mat_train,closed_train_property_labels,train_data_features,closed_cost_category_path)
    # csoaa_open_1 = multiVowpalFormat(open_cost_mat_train_1,train_property_labels,train_data_features,open_cost_category_path_1)
    # csoaa_closed_1 = multiVowpalFormat(closed_cost_mat_train_1,closed_train_property_labels,train_data_features,closed_cost_category_path_1)
    # csoaa_open_2 = multiVowpalFormat(open_cost_mat_train_2,train_property_labels,train_data_features,open_cost_category_path_2)
    # csoaa_closed_2 = multiVowpalFormat(closed_cost_mat_train_2,closed_train_property_labels,train_data_features,closed_cost_category_path_2)


    # print "Starting cost sensitive predictions using batch script\n"
    # # os.system('../../vowpal.sh')
    # vowpal = subprocess.Popen('../../vowpal.sh',shell=True, stdout=subprocess.PIPE)
    # vowpal.communicate()
    # print vowpal.returncode
    # #
    # # os.chdir(os.getcwd())
    # print "Ending predictions"

    # y_csoaa_open = np.loadtxt("../../data/output/cost/csoaa.predict",dtype=int)
    # y_csoaa_open = [i[0] for i in y_csoaa_open]
    # y_csoaa_open = openle.inverse_transform(y_csoaa_open)
    #
    # y_csoaa_closed = np.loadtxt("../../data/output/cost/csoaa_closed.predict",dtype=int)
    # y_csoaa_closed = [i[0] for i in y_csoaa_closed]
    # y_csoaa_closed = closedle.inverse_transform(y_csoaa_closed)
    #
    # y_csoaa_open_1 = np.loadtxt("../../data/output/cost/csoaa_1.predict",dtype=int)
    # y_csoaa_open_1 = [i[0] for i in y_csoaa_open_1]
    # y_csoaa_open_1 = openle.inverse_transform(y_csoaa_open_1)
    #
    # y_csoaa_closed_1 = np.loadtxt("../../data/output/cost/csoaa_closed_1.predict",dtype=int)
    # y_csoaa_closed_1 = [i[0] for i in y_csoaa_closed_1]
    # y_csoaa_closed_1 = closedle.inverse_transform(y_csoaa_closed_1)
    #
    # y_csoaa_open_2 = np.loadtxt("../../data/output/cost/csoaa_2.predict",dtype=int)
    # y_csoaa_open_2 = [i[0] for i in y_csoaa_open_2]
    # y_csoaa_open_2 = openle.inverse_transform(y_csoaa_open_2)
    #
    # y_csoaa_closed_2 = np.loadtxt("../../data/output/cost/csoaa_closed_2.predict",dtype=int)
    # y_csoaa_closed_2 = [i[0] for i in y_csoaa_closed_2]
    # y_csoaa_closed_2 = closedle.inverse_transform(y_csoaa_closed_2)
    #
    # # Load in the test data
    # test = pd.DataFrame(finalTestSentences)
    # threshold = test['threshold'][0]
    #
    # # These are the ground truths
    # y_multi_true = np.array(test['property'])
    # y_true_claim = np.array(test['claim'])
    # #
    # # # prob_prediction = np.array(open_multi_logit.predict_proba(test_data_features))
    # # #
    # # # prob_prediction_threshold = np.array(open_threshold_multi_logit.predict_proba(test_data_features))
    # # #
    # # # closed_prob_prediction = np.array(closed_multi_logit.predict_proba(test_data_features))
    # # #
    # # # closed_prob_prediction_threshold = np.array(closed_threshold_multi_logit.predict_proba(test_data_features))
    # #
    # # # print "Predicting open multinomial test labels with/without MAPE threshold using probability based predictor...\n"
    # # #
    # # # y_multi_logit_result_open_prob_binary,y_multi_logit_result_open_prob_binaryFixed = probabilityThreshold(multi_logit,prob_prediction,len(set(train_property_labels)), y_multi_true,probThreshold)
    # # #
    # # # y_multi_logit_result_open_prob_binary_threshold,y_multi_logit_result_open_prob_binary_thresholdFixed = probabilityThreshold(multi_logit_threshold,prob_prediction_threshold,len(set(train_property_labels_threshold)), y_multi_true,probThreshold)
    # # #
    # # # print "Predicting closed multinomial test labels with/without MAPE threshold using probability based predictor...\n"
    # # # y_multi_logit_result_closed_prob_binary, y_multi_logit_result_closed_prob_binaryFixed = probabilityThreshold(closed_multi_logit,closed_prob_prediction,len(set(closed_train_property_labels)),y_multi_true,probThreshold)
    # # #
    # # # y_multi_logit_result_closed_prob_binary_threshold,y_multi_logit_result_closed_prob_binary_thresholdFixed = probabilityThreshold(closed_multi_logit_threshold,closed_prob_prediction_threshold,len(set(closed_train_property_labels_threshold)),y_multi_true,probThreshold)
    # #
    # # y_multi_logit_result_open_threshold_binary = []
    # # y_multi_logit_result_closed_threshold_binary = []
    # #
    # y_open_pred_test_cslr_binary = []
    # y_closed_pred_test_cslr_binary = []
    # y_open_pred_test_cslr_binary_1 = []
    # y_closed_pred_test_cslr_binary_1 = []
    # y_open_pred_test_cslr_binary_2 = []
    # y_closed_pred_test_cslr_binary_2 = []
    # #
    # #
    # # # This is Andreas model for distant supervision
    # # y_andreas_mape = test['mape_label']
    # #
    # # y_distant_sv_property_openThreshold = test['predictedPropertyOpenThreshold']
    # # y_distant_sv_property_closedThreshold = test['predictedPropertyClosedThreshold']
    # #
    # # y_openThreshold_distant_sv_to_binary = []
    # # y_closedThreshold_distant_sv_to_binary = []
    # #
    # # positive_result = np.ones(len(finalTestSentences))
    # # y_pospred = positive_result
    # #
    # catLabels = [
    #              # y_distant_sv_property_openThreshold,
    #              # y_distant_sv_property_closedThreshold,
    #              # y_multi_logit_result_open_threshold,
    #              # y_multi_logit_result_closed_threshold,
    #             y_csoaa_open,
    #             y_csoaa_closed,
    #             y_csoaa_open_1,
    #             y_csoaa_closed_1,
    #             y_csoaa_open_1,
    #             y_csoaa_closed_1
    #
    # ]
    # #
    # binaryLabels = [
    #     # y_openThreshold_distant_sv_to_binary,
    #     # y_closedThreshold_distant_sv_to_binary,
    #     # y_multi_logit_result_open_threshold_binary,
    #     # y_multi_logit_result_closed_threshold_binary,
    #     y_open_pred_test_cslr_binary,
    #     y_closed_pred_test_cslr_binary,
    #     y_open_pred_test_cslr_binary_1,
    #     y_closed_pred_test_cslr_binary_1,
    #     y_open_pred_test_cslr_binary_2,
    #     y_closed_pred_test_cslr_binary_2
    # ]
    # #
    # trueLabels = []
    # trueLabels.extend(repeat(y_multi_true, len(binaryLabels)))
    # #
    # #
    # # Convert the categorical predictions to binary based on if matching property
    # def binaryConversion(trueLabel, evalLabel, binaryLabel):
    #     for true, eval in zip(trueLabel, evalLabel):
    #         # print true,eval, binary
    #         if eval == true:
    #             binaryLabel.append(1)
    #         else:
    #             binaryLabel.append(0)
    # #
    # #
    # #
    # for trueLabels, predictionLabels, emptyArray in zip(trueLabels, catLabels, binaryLabels):
    #     binaryConversion(trueLabels, predictionLabels, emptyArray)
    # #
    # # output = pd.DataFrame(data=dict(parsed_sentence=test['parsedSentence'],
    # #                                 features=clean_test_sentences,
    # #
    # #                                 # open_property_prediction_withMAPEthreshold=y_multi_logit_result_open_threshold,
    # #                                 # open_property_prediction_withMAPEthreshold_toBinary=y_multi_logit_result_open_threshold_binary,
    # #                                 # closed_property_prediction_withMAPEthreshold=y_multi_logit_result_closed_threshold,
    # #                                 # closed_property_prediction_withMAPEthreshold_toBinary=y_multi_logit_result_closed_threshold_binary,
    # #
    # #                                 # open_property_probability_prediction_toBinary=y_multi_logit_result_open_prob_binary,
    # #                                 # open_property_probability_threshold_prediction_toBinary=y_multi_logit_result_open_prob_binary_threshold,
    # #                                 # closed_property_probability_prediction_toBinary=y_multi_logit_result_closed_prob_binary,
    # #                                 # closed_property_probability_threshold_prediction_toBinary=y_multi_logit_result_closed_prob_binary_threshold,
    # #                                 #
    # #                                 # open_property_probability_prediction_toBinaryFixed=y_multi_logit_result_open_prob_binaryFixed,
    # #                                 # open_property_probability_threshold_prediction_toBinaryFixed=y_multi_logit_result_open_prob_binary_thresholdFixed,
    # #                                 #
    # #                                 # closed_property_probability_prediction_toBinaryFixed=y_multi_logit_result_closed_prob_binaryFixed,
    # #                                 # closed_property_probability_threshold_prediction_toBinaryFixed=y_multi_logit_result_closed_prob_binary_thresholdFixed,
    # #
    # #
    # #                                 distant_supervision_open_withMAPEThreshold=y_distant_sv_property_openThreshold,
    # #
    # #                                 distant_supervision_closed_withMAPEThreshold=y_distant_sv_property_closedThreshold,
    # #                                 distant_supervision_open_withMAPEThreshold_toBinary=y_openThreshold_distant_sv_to_binary,
    # #
    # #                                 distant_supervision_closed_withMAPEThreshold_toBinary=y_closedThreshold_distant_sv_to_binary,
    # #
    # #                                 test_data_mape_label=test['mape_label'],
    # #                                 claim_label=y_true_claim,
    # #                                 test_data_property_label=test['property'],
    # #                                 andreas_prediction=y_pospred,
    # #                                 threshold=np.full(len(y_true_claim), threshold),
    # #                                 # probThreshold = np.full(len(y_true_claim), probThreshold),
    # #                                 cost_sensitive_open= y_open_pred_test_cslr,
    # #                                 cost_sensitive_closed = y_closed_pred_test_cslr,
    # #                                 cost_sensitive_open_binary= y_open_pred_test_cslr_binary,
    # #                                 cost_sensitive_closed_binary = y_closed_pred_test_cslr_binary,
    # #                                 cost_sensitive_open_1= y_open_pred_test_cslr_1,
    # #                                 cost_sensitive_closed_1 = y_closed_pred_test_cslr_1,
    # #                                 cost_sensitive_open_binary_1= y_open_pred_test_cslr_binary_1,
    # #                                 cost_sensitive_closed_binary_1 = y_closed_pred_test_cslr_binary_1,
    # #                                 cost_sensitive_open_2= y_open_pred_test_cslr_2,
    # #                                 cost_sensitive_closed_2 = y_closed_pred_test_cslr_2,
    # #                                 cost_sensitive_open_binary_2= y_open_pred_test_cslr_binary_2,
    # #                                 cost_sensitive_closed_binary_2 = y_closed_pred_test_cslr_binary_2
    # #                                 ))
    # #
    # # # print str(os.path.splitext(sys.argv[2])[0]).split("/")
    # # # TODO This was an issue on command line - change to [2] if on command line and 8 if not
    # testSet = str(os.path.splitext(sys.argv[2])[0]).split("/")[8]
    # #
    # # resultPath = os.path.join(sys.argv[4] + testSet + '_' + str(threshold) + '_' + str(probThreshold)+ '_costregressionResult.csv')
    # #
    # # output.to_csv(path_or_buf=resultPath, encoding='utf-8', index=False, cols=[
    # #     'parsed_sentence',
    # #     'features',
    # #
    # #     # 'open_property_prediction_withMAPEthreshold',
    # #     # 'open_property_prediction_withMAPEthreshold_toBinary',
    # #     # 'closed_property_prediction_withMAPEthreshold',
    # #     # 'closed_property_prediction_withMAPEthreshold_toBinary',
    # #
    # #     # 'open_property_probability_prediction_toBinary',
    # #     # 'open_property_probability_threshold_prediction_toBinary',
    # #     #
    # #     # 'closed_property_probability_prediction_toBinary',
    # #     # 'closed_property_probability_threshold_prediction_toBinary',
    # #     #
    # #     # 'open_property_probability_prediction_toBinaryFixed',
    # #     # 'open_property_probability_threshold_prediction_toBinaryFixed',
    # #     #
    # #     # 'closed_property_probability_prediction_toBinaryFixed',
    # #     # 'closed_property_probability_threshold_prediction_toBinaryFixed',
    # #
    # #     'distant_supervision_open_withMAPEThreshold',
    # #     'distant_supervision_closed_withMAPEThreshold',
    # #     'distant_supervision_open_withMAPEThreshold_toBinary',
    # #     'distant_supervision_closed_withMAPEThreshold_toBinary',
    # #
    # #     'test_data_mape_label',
    # #     'claim_label',
    # #     'andreas_property_label',
    # #     'andreas_prediction',
    # #     'threshold',
    # #     # 'probThreshold',
    # #     'cost_sensitive_open',
    # #     'cost_sensitive_closed',
    # #     'cost_sensitive_open_binary',
    # #     'cost_sensitive_closed_binary',
    # #     'cost_sensitive_open_1',
    # #     'cost_sensitive_closed_1',
    # #     'cost_sensitive_open_binary_1',
    # #     'cost_sensitive_closed_binary_1',
    # #     'cost_sensitive_open_2',
    # #     'cost_sensitive_closed_2',
    # #     'cost_sensitive_open_binary_2',
    # #     'cost_sensitive_closed_binary_2'
    # #
    # # ])
    # #
    # # # TODO - need to create a per property chart
    # #
    # # Now we write our precision F1 etc to an Excel file
    # summaryDF = pd.DataFrame(columns=('precision', 'recall', 'f1', 'accuracy', 'evaluation set', 'threshold'))
    # # # 'probThreshold'
    # #
    # def evaluation(trueLabels, evalLabels, test_set, threshold):
    #     # ,probThreshold
    #     global summaryDF
    #     global trainingLabels
    #     global positiveOpenTrainingLabels
    #     global negativeOpenTrainingLabels
    #     global positiveClosedTrainingLabels
    #     global negativeClosedTrainingLabels
    #     global openTrainingClasses
    #     global openTrainingClassesThreshold
    #     global closedTrainingClasses
    #     global closedTrainingClassesThreshold
    #
    #     precision = precision_score(trueLabels, evalLabels)
    #     recall = recall_score(trueLabels, evalLabels)
    #     f1 = f1_score(trueLabels, evalLabels)
    #     accuracy = accuracy_score(trueLabels, evalLabels)
    #
    #     data = {'precision': [precision],
    #             'recall': [recall],
    #             'f1': [f1],
    #             'accuracy': [accuracy],
    #             'evaluation set': [test_set],
    #             'threshold': [threshold],
    #             # 'probThreshold': [probThreshold],
    #             'trainingLabels':[trainingLabels],
    #             'positiveOpenLabels':[positiveOpenTrainingLabels],
    #             'negativeOpenLabels':[negativeOpenTrainingLabels],
    #             'positiveClosedLabels':[positiveClosedTrainingLabels],
    #             'negativeClosedLabels':[negativeClosedTrainingLabels],
    #             'openTrainingClasses': [openTrainingClasses],
    #             'openTrainingClassesThreshold': [openTrainingClassesThreshold],
    #             'closedTrainingClasses':[closedTrainingClasses],
    #             'closedTrainingClassesThreshold': [closedTrainingClassesThreshold]
    #             }
    #
    #     DF = pd.DataFrame(data)
    #
    #     summaryDF = pd.concat([summaryDF, DF])
    #
    #
    # results = [
    #            # y_pospred,
    #            #
    #            # y_openThreshold_distant_sv_to_binary,
    #            #
    #            # y_closedThreshold_distant_sv_to_binary,
    #
    #            # y_multi_logit_result_open_threshold_binary,
    #            #
    #            # y_multi_logit_result_closed_threshold_binary,
    #
    #            # y_multi_logit_result_open_prob_binary,
    #            # y_multi_logit_result_open_prob_binary_threshold,
    #            # y_multi_logit_result_closed_prob_binary,
    #            # y_multi_logit_result_closed_prob_binary_threshold,
    #            #
    #            # y_multi_logit_result_open_prob_binaryFixed,
    #            # y_multi_logit_result_open_prob_binary_thresholdFixed,
    #            # y_multi_logit_result_closed_prob_binaryFixed,
    #            # y_multi_logit_result_closed_prob_binary_thresholdFixed
    #             y_open_pred_test_cslr_binary,
    #             y_closed_pred_test_cslr_binary,
    #             y_open_pred_test_cslr_binary_1,
    #             y_closed_pred_test_cslr_binary_1,
    #             y_open_pred_test_cslr_binary_2,
    #             y_closed_pred_test_cslr_binary_2
    #
    #            ]
    # #
    #
    # for result in results:
    #     evaluation(y_true_claim, result, testSet, threshold)
    #     # ,probThreshold
    #
    # columns = list([
    #                 # 'Previous_Model',
    #                 #
    #                 #
    #                 # 'Open_Property_MAPE_Threshold_Distant_Supervision_Model',
    #                 #
    #                 # 'Closed_Property_MAPE_Threshold_Distant_Supervision_Model',
    #
    #                 # 'Open_Property_Bag_of_Words_Multinomial_Logistic_Regression_w_Binary_Evaluation_&_MAPE_Threshold',
    #                 #
    #                 # 'Closed_Property_Bag_of_Words_Multinomial_Logistic_Regression_w_Binary_Evaluation_&_MAPE_Threshold',
    #
    #                 # 'Open_Property_Probability_Prediction',
    #                 # 'Open_Property_Probability_Prediction_MAPEThreshold',
    #                 # 'Closed_Property_Probability_Prediction',
    #                 # 'Closed_Property_Probability_Prediction_MAPEThreshold',
    #                 #
    #                 # 'Open_Property_Probability_PredictionFixed',
    #                 # 'Open_Property_Probability_Prediction_MAPEThresholdFixed',
    #                 # 'Closed_Property_Probability_PredictionFixed',
    #                 # 'Closed_Property_Probability_Prediction_MAPEThresholdFixed'
    #                 'Cost Sensitive Classification Open',
    #                 'Cost Sensitive Classification Closed',
    #                 'Cost Sensitive Classification Open 1',
    #                 'Cost Sensitive Classification Closed 1',
    #                 'Cost Sensitive Classification Open 2',
    #                 'Cost Sensitive Classification Closed 2'
    #                 ])
    #
    # # summaryDF.set_index(['A','B'])
    # summaryDF.index = columns
    #
    # print summaryDF
    #
    # try:
    #     if os.stat(sys.argv[5]).st_size > 0:
    #         # df_csv = pd.read_csv(sys.argv[5],encoding='utf-8',engine='python')
    #         # summaryDF = pd.concat([df_csv,summaryDF],axis=1,ignore_index=True)
    #         with open(sys.argv[5], 'a') as f:
    #             # Need to empty file contents now
    #             summaryDF.to_csv(path_or_buf=f, encoding='utf-8', mode='a', header=False)
    #             f.close()
    #     else:
    #         print "empty file"
    #         with open(sys.argv[5], 'w+') as f:
    #             summaryDF.to_csv(path_or_buf=f, encoding='utf-8')
    #             f.close()
    # except OSError:
    #     print "No file"
    #     with open(sys.argv[5], 'w+') as f:
    #         summaryDF.to_csv(path_or_buf=f, encoding='utf-8')
    #         f.close()