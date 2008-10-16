#!/usr/bin/env python

import os, re, collections

localDir = os.path.dirname(__file__)
absDir = os.path.join(os.getcwd(), localDir)

def words(text): return re.findall('[a-z]+', text.lower()) 

def train(features):
    model = collections.defaultdict(lambda: 1)
    for f in features:
        model[f] += 1
    return model

#NWORDS = train(words(file('spell_file.txt').read()))
NWORDS = train(file(os.path.join( absDir, 'spell_file.txt')).read().split('\n'))

alphabet = 'abcdefghijklmnopqrstuvwxyz'

def edits1(word):
    n = len(word)
    return set([word[0:i]+word[i+1:] for i in range(n)] +                     # deletion
               [word[0:i]+word[i+1]+word[i]+word[i+2:] for i in range(n-1)] + # transposition
               [word[0:i]+c+word[i+1:] for i in range(n) for c in alphabet] + # alteration
               [word[0:i]+c+word[i:] for i in range(n+1) for c in alphabet])  # insertion

def known_edits2(word):
    return set(e2 for e1 in edits1(word) for e2 in edits1(e1) if e2 in NWORDS)

def known(words): return set(w for w in words if w in NWORDS)

def correct(word):
    candidates = known([word]) or known(edits1(word)) or known_edits2(word) or [word]
    return candidates
    #return max(candidates, key=lambda w: NWORDS[w]) # Only the best result

if __name__ == '__main__':
    import sys
    print correct( sys.argv[1] )
