import nltk
import numpy as np
from nltk.stem.lancaster import LancasterStemmer
import tflearn
import tensorflow
import random
import json
import pickle

stemmer = LancasterStemmer()  # stemmer using Lancaster method
bot_name = "BOT"

with open("intents.json") as file:
    data = json.load(file)

    words = []
    labels = []
    docs_x = []
    docs_y = []
    symbols = ["?", "!"]

    for intent in data["intents"]:
        for pattern in intent["patterns"]:
            wrds = nltk.word_tokenize(pattern)  # tokenize: get all the words in pattern
            words.extend(wrds)
            docs_x.append(wrds)
            docs_y.append(intent["tag"])

        if intent["tag"] not in labels:
            labels.append(intent["tag"])

    words = [stemmer.stem(w.lower()) for w in words if
             w not in symbols]  # stemming the words using Lancaster method
    words = sorted(list(set(words)))  # main words list
    labels = sorted(labels)

    training = []
    output = []
    out_empty = [0 for _ in range(len(labels))]

    for x, doc in enumerate(docs_x):
        bag = []

        wrds = [stemmer.stem(w) for w in doc]

        for w in words:
            if w in wrds:
                bag.append(1)
            else:
                bag.append(0)

        output_row = out_empty[:]
        output_row[labels.index(docs_y[x])] = 1

        training.append(bag)
        output.append(output_row)

    training = np.array(training)
    output = np.array(output)

    with open("data.pickle", "wb") as f:
        pickle.dump((words, labels, training, output), f)

tensorflow.compat.v1.reset_default_graph()  # get rid of previous settings

#  Creates a neural network with 4 layers
#  First layer (input) number of neurons = length of training data set
#  Second & third layer 8 neurons
#  Fourth layer (output) number of neurons = length of output data set
#  softmax gives a probability for each element in the output data set
#  Apply regression on the neural network

net = tflearn.input_data(shape=[None, len(training[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(output[0]), activation="softmax")
net = tflearn.regression(net)

model = tflearn.DNN(net)

try:
    model.load("model.tflearn")
    # training the model

except:
    # n_epoch = how many times sees the same data
    model.fit(training, output, n_epoch=1000, batch_size=8, show_metric=True)
    model.save("model.tflearn")


def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))]

    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]

    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1

    return np.array(bag)


def chat(msg):
    results = model.predict([bag_of_words(msg, words)])[0]
    results_index = np.argmax(results)
    tag = labels[results_index]

    if results[results_index] > 0.7:
        for tg in data["intents"]:
            if tg['tag'] == tag:
                responses = tg['responses']

        return random.choice(responses)
    else:
        return "I didn't understand that. Please try again"
