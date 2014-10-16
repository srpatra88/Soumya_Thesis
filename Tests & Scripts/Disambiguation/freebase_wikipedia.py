# Nerd_Tweets.py outputs Freebase.com links. This script is used to first get equivalent Wikipedia links from the  output file to compare against ground truth for performance. Put the output from NERD_Tweets.py in 'Our_output.txt'.
# Sample input : RT @EgyTweets RT @CandiCunningham : There are more pyramids in Peru than in Egypt #coolfacts	Egypt||Peru	{'Egypt': '/en/egypt', 'Peru': '/en/peru'}
# Sample output : RT @EgyTweets RT @CandiCunningham : There are more pyramids in Peru than in Egypt #coolfacts	[u'http://en.wikipedia.org/wiki/Egypt', u'http://en.wikipedia.org/wiki/Peru']

# Note: Install urllib2 and lxml python modules before using this script.

import urllib2
import lxml.html
f = open('Our_output.txt','r')
f2 = open('Our_output_Wikipedia.txt','w')
url = 'http://www.freebase.com'
out = f.readlines()
for ln in out:
    try:
        links = []
        parts = ln.split('\t')
        d = ast.literal_eval(parts[2])
        for value in d.itervalues():
            check = 0
            code   = urllib2.urlopen(url+value).read()
            html   = lxml.html.fromstring(code)
            result = html.xpath('//div[@class="meta"]/span[@class="key"]/span/a[@class="weblink-favicon"]/@href')
            for r in result:
                if 'index.html' not in r:
                    print r
                    links.append(r)
                    check = 1
            if check == 0:
                result =  html.xpath('//a[contains(text(), "en.wikipedia.org/wiki/")]/@href')
                for r in result:
                    if 'index.html' not in r:
                        print r
                        links.append(r)
                
                #if 'index.html' not in r:
                    #links.append(result)
        f2.write(parts[0]+'\t'+str(links)+'\n')
    except Exception:
        print 'ERROR---'+ln
        pass
f.close()
f2.close()
