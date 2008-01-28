import re, collections

class SpellCheck( object ):

    alphabet = 'abcdefghijklmnopqrstuvwxyz'

    def __init__( self, thesaurus ):
        self.NWORDS = self.__train( self.__words( " ".join(thesaurus) ) )

    def __words( self, text): return re.findall('[a-z]+', text.lower()) 

    def __train( self, features ):
        model = {}
        for f in features:
            if not model.has_key(f):
                model[f] = 1
            model[f] += 1
        return model

    def __edits1( self, word ):
        n = len(word)
        return set([word[0:i]+word[i+1:] for i in range(n)] +                     # deletion
                   [word[0:i]+word[i+1]+word[i]+word[i+2:] for i in range(n-1)] + # transposition
                   [word[0:i]+c+word[i+1:] for i in range(n) for c in self.alphabet] + # alteration
                   [word[0:i]+c+word[i:] for i in range(n+1) for c in self.alphabet])  # insertion

    def __known_edits2( self, word ):
        return set(e2 for e1 in self.__edits1(word) for e2 in self.__edits1(e1) if e2 in self.NWORDS)

    def __known( self, words ): return set(w for w in words if w in self.NWORDS)

    def correct( self, word ):
        candidates = self.__known([word]) or \
            self.__known(self.__edits1(word)) or \
            self.__known_edits2(word) or [word]
        return list( candidates )
#    key = lambda w: self.NWORDS[w]
#    return max(candidates)# key)

if __name__ == "__main__":
    pass
