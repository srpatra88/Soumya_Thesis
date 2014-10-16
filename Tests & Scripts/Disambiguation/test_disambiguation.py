#This script is used to test the disambiguation performance.
# Input 1: brian_collection.xml 
# Input 2 : Our_output_Wikipedia.txt
# Output : Disambiguation performance

import xml.etree.ElementTree as ET
import jellyfish
tree = ET.parse('brian_collection.xml')
root = tree.getroot()
f1 = open('Our_output_Wikipedia.txt','r')
out1 = f1.readlines()
total_count = 0
tp = 0
fn = 0
not_wikipedia = []
for tweet in root.findall("./Tweets/Tweet"):
    mlist = []
    twt = tweet.find('TweetText').text.encode("utf8")
    print twt
    mentions = tweet.findall('Mentions/Mention/Entity')
    for mention in mentions:
        if 'wikipedia' in mention.text:
            total_count += 1
            mlist.append(mention.text)
        else:
            not_wikipedia.append(mention.text)
    levenshtein = 100
    s1=''
    for l1 in out1:
        try:
            test1 = l1.split('\t')
            levenshtein2 = jellyfish.levenshtein_distance(test1[0],twt)
            if levenshtein2 < levenshtein:
                s1 = l1
                levenshtein = levenshtein2

        except Exception:
            continue
    if levenshtein < 10:
        parts = s1.split('\t')
        mlist2 = parts[1]
    
    print 'mlist1\t'+str(mlist)+'\n'
    print 'mlist2\t'+str(mlist2)+'\n'
    for m1 in mlist:
        if m1 not in mlist2:
            fn += 1
            print 'False\t'+m1+'\n'
        else:
            tp +=1

print 'Total\t'+str(total_count)+'\ttp\t'+str(tp)+'\tfp\t'+str(fn)
print str(len(not_wikipedia))
f1.close()
#f2.close()
