import nltk
import re

import stopwords
sw = stopwords.StopWords()
stop_words = sw.get_words()

import emoticons
em = emoticons.Emoticons()
emoticons = em.get_emoticons()

stemmer = nltk.PorterStemmer()

#Add features beyond ngrams to list of words.
def add_features(words):
    new_words = []
    veto_indices = set([])
    is_quote = False
    for idx, word in enumerate(words):
        #If remaining is a retweet, just add that a retweet was found but don't add anymore words
        if word == "rt":
            new_words.append("rt")            
            break

        #If word is left quote then all that follows is coming from someone besides user
        if word == u"\u201C":
            new_words.append("QUOTEDTEXT")
            is_quote = True
            continue

        #End of quote, normally at the end of a word
        if word.find(u"\u201d") != -1 or word == '"':
            is_quote = False
            continue

        #Skip some indices as we replaced them with special keys
        if idx in veto_indices or is_quote:
            continue

        if repeated_letter(word, new_words):
            continue
        if add_string_emotion(idx, word, words, new_words, veto_indices):
            continue
        if add_emoji(idx, word, new_words, veto_indices):
            continue
        if add_number(word, new_words):
            continue
        if add_time(word, new_words):
            continue
        #Add word if it is not special
        new_words.append(word)
    return new_words


def add_time(word, new_words):
    words = word.split(":")
    if len(words) != 2:
        return False
    if words[0].isdigit() and int(words[0]) < 25 and words[1].isdigit() and int(words[1]) < 61:
        new_words.append("TIMEVALUEFOUND")
        return True
    return False


def add_number(word, new_words):
    if word.isdigit() and word !="2" and word != "4":
        new_words.append("NUMERICVALUE")
        return True
    return False

#See if word has letter repeated at least three times. If so just mark it as such,
#don't include work itself as unlikely to have exact matches in other tweets
def repeated_letter(word, new_words):
    for letter_idx in range (0, len(word)-2):
        if word[letter_idx]==word[letter_idx+1]==word[letter_idx+2]:
            if word[letter_idx] == ".":
                new_words.append("ELIPSES")
            else:
                new_words.append("WORDWITHREPEATEDLETTER")
            return True
    return False


#See if string of exclamation or question marks found
def add_string_emotion(idx, word, words, new_words, veto_indices):
    if word == "!" or word == "?":
        both_true = False
        one_true = False
        for i, next_word in enumerate(words[idx+1:]):
            if next_word == "!" or next_word == "?":
                if next_word != word:
                    both_true = True
                else:
                    one_true = True
                veto_indices.add(idx + 1 + i)
            else:
                break
                    
        if both_true:
            new_words.append("STRINGOF!AND?")

        elif one_true:
            new_words.append("STRINGOF" + word)

        else: 
            new_words.append(word)
            
        return True

    return False

#Check if emoji found. If so add that tag as well as the letters that came before it in case is hanging on end of word
def add_emoji(idx, word, new_words, veto_indices):
    for idx, char in enumerate(word):
        #Emojis have very high code point values
        if ord(char)>10000:

            #Add word up to this point if emoji not first letter and add that word at end of emoji
            if idx > 0:
                new_words.append("EMOJIENDWORD")

            #Emoji alone
            elif len(word) < 3:
                new_words.append("EMOJIALONE")
                new_words.append(char)
                    
            #Mulitple emojis
            else:
                new_words.append("EMOJISTRING")

            return True

        elif ord(char)>1000:
            new_words.append("UNKNWONCHAR")

            return True

    return False


#Remove stopwords
def remove_stopwords(words):
    new_words = [word for word in words if not word in stop_words]
    return new_words


def stem(words):
    stemwords = [stemmer.stem(word) for word in words]
    return stemwords


#Use nltk tokenizer to get words but first modify the text to handle things the tokenizer doesn't handle well
def get_words_tokenized(corpus):
    words = corpus.split()

    for idx, word in enumerate(words):
        if word.find("http") == 0:
            words[idx] = "WEBSITELINK"

        if word.find("@") == 0 and len(word) > 1:
            words[idx] = "ATUSERNAME"

        if word in emoticons:
            words[idx] = emoticons[word] + "EMOTICON"

        if word.find("&lt;3") != -1:
            words[idx] = "HeartEMOTICON"

        if word.find("&amp;") != -1:
            words[idx] = "AMPERSAND"

    rebuilt_words = " ".join(words)
    return sum((nltk.word_tokenize(sent) for sent in nltk.sent_tokenize(rebuilt_words)), [])


#Replace stopwords with their part of speech
def add_pos(words):
    for idx, word_and_pos in enumerate(nltk.pos_tag(words)):
        if word_and_pos[0] in stop_words:
            words[idx] = word_and_pos[1]

    return words

def restore_emoticons(words):
    emoticonLetters = set([":", "-", ")", "o", "]", "3", "c", ">", "=", "8", "}", "^", "D", "-", "x", "X", "B", "[", "(", "<", "{", "||", "'", ";", "v", "DX", "O", "*",
                           "p", "P", "b", "/", "\\", "L", "%", "_", "t", "&", "-", ","])

    emoticon = []
    new_words = []

    for idx, word in enumerate(words):
        if all(letter in emoticonLetters for letter in word):
            emoticon.append(word)
        else:
            if len(emoticon) > 0:
                if len("".join(emoticon)) > 1 and not re.match(r'^[A-Za-z0-9_]+$', "".join(emoticon)):
                    new_words.append("UNKNOWNEMOTICON")
                else:
                    new_words.extend(emoticon)
                emoticon = []

            new_words.append(word)

    #If still have an emoticon
    if len("".join(emoticon)) > 1 and not re.match(r'^[A-Za-z0-9_]+$', "".join(emoticon)):
        new_words.append("UNKNOWNEMOTICON")

    if len(emoticon) > 0:
        new_words.append("".join(emoticon))

    return new_words

def clean_words(words):
    words = restore_emoticons(words)

    #Add in any extra features desired
    words = add_features(words)

    #Remove stopwords
    words = remove_stopwords(words)

    #Stem words
    words = stem(words)

    return words


def clean_words_with_pos(words):
    words = restore_emoticons(words)

    #Add in any extra features desired
    words = add_features(words)

    #Add POS
    words = add_pos(words)

    #Stem words
    words = stem(words)

    return words
