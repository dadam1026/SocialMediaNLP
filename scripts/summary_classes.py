import pandas as pd
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

import nltk
from nltk import download as nltk_download
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
import numpy as np
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer

#this is the class for generative summarization
class GenFinSummarizer():
    def __init__(self):

        print("Initializing Object...")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("sshleifer/distilbart-cnn-12-6")
        self.tokenizer = AutoTokenizer.from_pretrained("sshleifer/distilbart-cnn-12-6")

    # params: text to summarize
    # returns: summary generated by generative summary model
    def summarize(self, text):
        
        print("Generating Summary...")
        #this truncates the block... don't want that
        input_ids = self.tokenizer.encode(text, return_tensors="pt", truncation=True, max_length=1024)
        output = self.model.generate(
            input_ids,
            max_length=200,
            num_return_sequences=1,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        
        output = self.tokenizer.decode(output[0])

        return output

#this is the class for extractive summarization
class ExFinSummarizer():
    def __init__(self):

        print("Initializing Object...")

        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk_download('punkt')

        try:
            nltk.data.find('stopwords')
        except LookupError:
            nltk_download('stopwords')

        self.vectorizer = TfidfVectorizer()
        self.sentences=[]
        self.fv = []
    
    # params: text to summarize
    # returns: sentences prepped for analysis  
    def prep_sentences(self, textblock):
        #splits into sentences
        sentences = sent_tokenize(textblock)

        #remove non-alphanumeric characters and stopwords from each sentence, lowercase, tokenize
        sentences_processed = []
        for s in sentences:
            sentence_reduced = s.replace("[^a-zA-Z0-9_]", ' ')
            sentence_reduced = [word.lower() for word in sentence_reduced.split(' ') if word.lower() not in stopwords.words('english')]
            sentences_processed.append(' '.join(word for word in sentence_reduced))
        
        #vectorize each setence
        feature_vecs = self.vectorizer.fit_transform(sentences)
        feature_vecs = feature_vecs.todense().tolist()
            
        #return
        self.sentences = sentences
        self.fv = feature_vecs

    # params: text to summarize, how many sentences to pick
    # returns: summary generated by extractive process
    def summarize(self, textblock, top_n):

        print("Generating Summary...")
        self.prep_sentences(textblock)

        adjacency_matrix = np.zeros((len(self.fv), len(self.fv)))
    
        for i in range(len(self.fv)):
            for j in range(len(self.fv)):
                if i == j: #ignore if both are the same sentence
                    continue 
                adjacency_matrix[i][j] = cosine_distance(self.fv[1], self.fv[j])
               
        # Create the graph representing the document
        document_graph = nx.from_numpy_array(adjacency_matrix)

        # Apply PageRank algorithm to get centrality scores for each node/sentence
        scores = nx.pagerank(document_graph)
        scores_list = list(scores.values())

        # Sort and pick top sentences
        ranking_idx = np.argsort(scores_list)[::-1]
        ranked_sentences = [self.sentences[i] for i in ranking_idx]   

        summary = []
        for i in range(top_n):
            summary.append(ranked_sentences[i])

        summary = " ".join(summary)

        return summary