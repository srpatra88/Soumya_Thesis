from gensim.models import word2vec
import logging
import re,json,urllib,urllib2
import os,sys,time
from itertools import combinations,product
from operator import itemgetter
import enchant
from PyDbLite import Base
import jellyfish
import subprocess

testfile = str(sys.argv[1])
jarfile = 'ark-tweet-nlp-0.3.2.jar'

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
service_url = 'https://www.googleapis.com/freebase/v1/search'
unnecessary = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday','january','february','march','april','may','june','july','august','september','october','november','december','it']
freebase_link = 'http://www.freebase.com'
model1 = word2vec.Word2Vec.load_word2vec_format('freebase-vectors-skipgram1000-en.bin.gz', binary=True)
chant = enchant.Dict("en_US")
bcluster = Base('bcluster.pdl')
bcluster.open()
api_key = 'YOUR FREEBASE API KEY HERE'
mslink = 'http://weblm.research.microsoft.com/rest.svc/bing-body/2013-12/3/jp?u=YOUR MICROSOFT NGRAM TOKEN HERE'

#Tokenize and Tag individual tokens using Owoputi et al. tagger
def tokenize():
    cmd = 'java -XX:ParallelGCThreads=2 -Xmx500m -jar '+jarfile+' \"'+testfile+'\"'
    process = subprocess.Popen(cmd,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT,shell=True)
    return  iter(process.stdout.readline, b'')


#Collect ngrams from the segments
def ngrams(input, n):
    input = input.split(' ')
    input = [x.split('||') for x in input]
    output = []
    for i in range(len(input)-n+1):
        temp = input[i:i+n]
        output.extend(list(product(*temp)))
    output = [' '.join(d) for d in output]
    return output

#Find the best candidate to replace the OOV word
def bestcandidate(wrd):
    w = wrd
    candidate_list = []
    try:
        #Check the Brown word clusters
        c = bcluster._word[w]
        for rec in c:
            d = rec['cluster']
        recs = bcluster._cluster[d]
        for rec in recs:
            candidate = rec['word']
            levenshtein = jellyfish.levenshtein_distance(w,candidate)
            n2 = jellyfish.metaphone(w)
            n3 = jellyfish.metaphone(candidate)
            if chant.check(candidate):
                #Filter the candidates within a specific character and phonetic distance
                if levenshtein <= 2 or jellyfish.levenshtein_distance(n2, n3) <= 1:
                    candidate_list.append((candidate, rec['count']))
        return candidate_list[-1][0]
    except Exception:
        return 'No'

#Extract possible candidates for a mention from Freebase API    
def checkAPI(term):
    term = term.lower()
    params = {
        'query': term,
        'limit' : 30,
        'key': api_key
        }
    url = service_url + '?' + urllib.urlencode(params)
    response = json.loads(urllib.urlopen(url).read())
    results = []
    for result in response['result']:
        try:
            name = result['name']
            if term not in name.lower():
                continue
            id_res = result['id'].encode('utf8')
            results.append(id_res)
        except Exception:
            pass
       
    return results

#For tweets with only 1 mention, assign the most popular entity as a "best guess" from Freebase
def checkAPIfinal(term):
    term = term.lower()
    params = {
        'query': term,
        'limit' : 30,
        'key': api_key
        }
    url = service_url + '?' + urllib.urlencode(params)
    response = json.loads(urllib.urlopen(url).read())
    results = []
    for result in response['result']:
        try:
            name = result['name']
            id_res = result['id'].encode('utf8')
            results.append(id_res)
        except Exception:
            pass
       
    return results

#For 2 given mentions, find the best candidate pairs using vector model scores
def compare_two_mentions(mention1,mention2):
    entity_list1 = checkAPI(mention1)
    entity_list2 = checkAPI(mention2)
    maximum = 0.0
    best = 'no'
    a =[]
    for e1 in entity_list1:
        for e2 in entity_list2:
            try:
                sim = model1.similarity(e1,e2)
                if sim > maximum and 0.20 < sim < 1.0:
                    maximum = sim
                    best = (mention1,e1,mention2,e2,sim)
            except Exception:
                pass
    return best

#Normalize the segment
def normalize_sentence(segments,dict_tweet):
    word_in_segment = segments.split(' ')
    normalized = ''
    for t in word_in_segment:
        try:
            t_lower = t.lower()
            #If Dictionary check fails and token is not a proper noun, perform normalization
            if chant.check(t_lower)== False and dict_tweet[t] != '^':
                bcluster_best = bestcandidate(t_lower)
                if bcluster_best == 'No':
                    suggestions = chant.suggest(t_lower)
                    p = []
                    pos = word_in_segment.index(t)
                    if pos == 0:
                        for s in suggestions:
                            a = float(urllib2.urlopen(urllib2.Request(mslink,s+' '+word_in_segment[pos+1])).read()[:-1])
                            p.append((s,a))
                    elif pos == len(word_in_segment)-1:
                        for s in suggestions:
                            a = float(urllib2.urlopen(urllib2.Request(mslink,word_in_segment[pos-1]+' '+s)).read()[:-1])
                            p.append((s,a))
                    else:
                        for s in suggestions:
                            a1 = float(urllib2.urlopen(urllib2.Request(mslink,word_in_segment[pos-1]+ ' ' + s)).read()[:-1])
                            a2 = float(urllib2.urlopen(urllib2.Request(mslink,s+' '+word_in_segment[pos+1])).read()[:-1])
                            p.append((s,(a1+a2)/2))
                    p = sorted(p, key=lambda tup: float(tup[1]), reverse=True)
                    normalized = normalized+' '+t+'||'+str(p[0][0])
                else:            
                    normalized = normalized+' '+t+'||'+bcluster_best
            else:
                normalized = normalized+' '+t
        except Exception:
            return segments
        
    return normalized[1:]

#Check if an ngram is a mention or not, by comparing against the entities in the vector model
def check_mention(all_mentions,element):
    e = '/en/'+'_'.join(element.split())
    if element.endswith('\'s'):
        element = element.replace('\'s','')
    if not (filter(lambda x: element in x ,all_mentions)):
        try:
            if model1.most_similar(e.lower(),topn=1):
                return True
        except Exception:
            return False
    return False

#Extract ngrams from segments and check if they are NEs
def extract_ngram_mentions(segments,dict_tweet):
    ngram_mentions = []
    four_grams = ngrams(segments,4)
    tri_grams = ngrams(segments,3)
    bi_grams = ngrams(segments,2)
    uni_grams = ngrams(segments,1)
        
        
    for element in four_grams:
        if check_mention(ngram_mentions,element):
            ngram_mentions.append(element)
            
    for element in tri_grams:
        if check_mention(ngram_mentions,element):
            ngram_mentions.append(element)
            
    for element in bi_grams:
        if check_mention(ngram_mentions,element):
            ngram_mentions.append(element)

    for element in uni_grams:
        check = 0
        if element.endswith('\'s'):
            element = element.replace('\'s','')
            check = 1
        e = '/en/'+element
        if not (filter(lambda x: element in x ,ngram_mentions)):
            try:
                if model1.most_similar(e.lower(),topn=1):
                    if check == 1 or dict_tweet[element] in ['^']:
                        ngram_mentions.append(element)
                        check = 0
            except Exception:
                continue           
    return ngram_mentions

#Add proper nouns to the mentions list
def add_proper_nouns(tw,tg,pnoun_mentions):
    temp = ''
    count = -1
    proper_nouns = []
    
    for key in tw:
        count += 1
        if tg[count] != '^':
            if temp != '':
                if not (filter(lambda x: temp in x ,pnoun_mentions)):
                    if ' ' in temp:
                        if len(checkAPI(temp))>0:
                            proper_nouns.append(temp)
                    else:
                        proper_nouns.append(temp)
                temp = ''
            continue
        else:
            if temp == '':
                temp = key
            else:
                temp += ' '+key 

    if temp != '' and not (filter(lambda x: temp in x ,pnoun_mentions)):
        proper_nouns.append(temp)
    return proper_nouns

#Remove false positives using the language model
def remove_FP(rm_mentions,dict_tweet,twt):
    discarded = []
    for x in rm_mentions:
        if x.lower() in unnecessary:
            discarded.append(x)
            continue
        for y in rm_mentions:
            if (x!=y and (x.lower() == y.lower())):
                discarded.append(x)
            
    for mention in rm_mentions:
        check_pnoun = mention.split()
        try:
            if any(dict_tweet[x]=='^' for x in check_pnoun):
                continue
        except Exception:
            continue
        p1 = float(urllib2.urlopen(urllib2.Request(mslink,mention)).read()[:-1])
        p2= -100.0
        m=re.search(mention+" (\w+)",twt)
        m2=re.search("(\w+) "+mention,twt)
        if m and m2:
            next_word = m.groups()[0]
            prev_word = m2.groups()[0]
            p2 = (float(urllib2.urlopen(urllib2.Request(mslink,mention+' '+next_word)).read()[:-1])+float(urllib2.urlopen(urllib2.Request(mslink,prev_word+' '+mention)).read()[:-1]))/2
        if m and not m2:
            next_word = m.groups()[0]
            p2 = float(urllib2.urlopen(urllib2.Request(mslink,mention+' '+next_word)).read()[:-1])
        if m2 and not m:
            prev_word = m2.groups()[0]
            p2 = float(urllib2.urlopen(urllib2.Request(mslink,prev_word+' '+mention)).read()[:-1])
        if p1 < p2:
            discarded.append(mention)
    rm_mentions = list(set(rm_mentions) - set(discarded))
    return rm_mentions,discarded

#Assign final mapping to mentions using relationship measure between entities
def disambiguate(dis_mentions,dict_tweet):
    similarity,final,rmv = [],[],[]
    final_mapping = {}
    combos = combinations(dis_mentions, 2)
    for e in combos:
        comparision = compare_two_mentions(e[0],e[1])
        if comparision != 'no':
            similarity.append(comparision)
    similarity.sort(key=lambda elem: elem[4],reverse=True)
    #Entities having similarity > 0.35, are strongly connected
    final = [x for x in similarity if x[4] > 0.35]
    similarity = list(set(similarity)-set(final))
    
    #Entities with high probability scores
    for x in final:
        if x[0] not in final_mapping:
            final_mapping[x[0]] = freebase_link+x[1]
            dis_mentions.remove(x[0])
            related = [y for y in similarity if (y[1]==x[1] or y[3]==x[1]) and  y[4] > 0.2]
            similarity = list(set(similarity)-set(related))
            for y in related:
                if y[0] not in final_mapping:
                    final_mapping[y[0]] = freebase_link+y[1]
                    dis_mentions.remove(y[0])
                if y[2] not in final_mapping:
                    final_mapping[y[2]] = freebase_link+y[3]
                    dis_mentions.remove(y[2])
                
        if x[2] not in final_mapping:
            final_mapping[x[2]] = x[3]
            dis_mentions.remove(x[2])
            related = [y for y in similarity if (y[1]==x[3] or y[3]==x[3]) and  y[4] > 0.2]
            similarity = list(set(similarity)-set(related))
            for y in related:
                if y[0] not in final_mapping:
                    final_mapping[y[0]] = freebase_link+y[1]
                    dis_mentions.remove(y[0])
                if y[2] not in final_mapping:
                    final_mapping[y[2]] = freebase_link+y[3]
                    dis_mentions.remove(y[2])               
    
    #Entities without much context
    for mention in dis_mentions:
        s = mention.split(' ')
        try:
            if any(dict_tweet[x]=='^' for x in s):
                final = checkAPIfinal(mention)
                final_mapping[mention] = freebase_link+final[0]
                rmv.append(mention)
        except Exception:
            continue
    dis_mentions = list(set(dis_mentions) - set(rmv))
    return final_mapping,dis_mentions

#Normalization + Mention Extraction + Disambiguaion
def NERD(twt):
    parts = twt.split('\t')
    tweet = parts[0]
    tags = parts[1].split()
    twords = tweet.split()
    tweet_length = len(twords)
    dict_tweet = dict(zip(twords,tags))
    partitions =[]
    splitTweet = [key for key in dict_tweet if dict_tweet[key] in ['@','#','U','E',',','~']]
    splitTweet = map(re.escape,splitTweet)
    pattern = '|'.join(splitTweet)
    partitions = re.split(pattern,tweet)
    partitions = [x for x in partitions if x!='']
    partitions = [s.lstrip().rstrip() for s in partitions]
    mentions,pnouns,discard,discard2= [],[],[],[]
    
    final_mapping = {}
    print 'Tweet'+'\n'+'-------------------'+'\n'+tweet+'\n'
    
    for segments in partitions:
        segments = normalize_sentence(segments,dict_tweet)
        mentions.extend(extract_ngram_mentions(segments,dict_tweet))
    pnouns = add_proper_nouns(twords,tags,mentions)
    mentions.extend(pnouns)
    
    print 'Extracted Mentions -->\t'+ str(mentions)+'\n'
    mentions,discard = remove_FP(mentions,dict_tweet,twt)
    final_mapping,discard2 = disambiguate(mentions,dict_tweet)
    print 'Drop False Positives -->\t'+ str(discard+discard2)+'\n'
    print str(final_mapping)+'\n'
    
    return str(final_mapping)

def main():
    write_to_file = str(sys.argv[2])
    f= open(write_to_file,'w')
    for output_line in tokenize():
        try:
            if '\t' in output_line:
                a,b,c,e = output_line.split('\t')
                tweet_content = a
                tweet = a+'\t'+b
                final_mapping = NERD(tweet)
                f.write(tweet_content+'\t'+final_mapping+'\n')
        except Exception:
            continue
    f.close()

if __name__ == "__main__":
   main()
