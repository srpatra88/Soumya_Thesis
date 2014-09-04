Installation and Usage Instructions
**********************************
**********************************
requires Python 2.7 or higher.


Prerequisites Tools
**********************************
**********************************
1. Make sure "ark-tweet-nlp-0.3.2.jar" is in folder "NERD_Tweets". This is needed for Tokenization and POS tagging.
2. Make sure the in memory DB "bcluster.pdl" is in folder "NERD_Tweets". This contains Brown word clusters for Normalization.
3. Go to the web site https://code.google.com/p/word2vec/ . From the section "Pre-trained entity vectors with Freebase naming" download the entity vector model "freebase-vectors-skipgram1000-en.bin.gz" (2.5 GB) and place it in the folder "NERD_Tweets".


Prerequisites API keys
**********************************
**********************************

Freebase API Key
**********************************
This key is needed for the NER component. Key can be obtained from Google developers website https://developers.google.com/freebase/v1/getting-started#api-keys
Please see Screenshots/API\_Keys.png to check where to add your API key in the "nerd\_tweets.py" file (line 23).

Microsoft Web ngram user token
**********************************
This is needed for the Language model and dropping false positives. Token can be found by sending a mail to "webngram@microsoft.com" with subject "Token Request".
More info and tutorial : http://weblm.research.microsoft.com/info/rest.html   http://weblm.research.microsoft.com/info/index.html
Please see Screenshots/API\_Keys.png to check where to add your ngram token in the "nerd\_tweets.py" file (line 24).



Prerequisites Python Modules
**********************************
**********************************

gensim
**********************************
This module is needed for the word2vec entity vector model. Install from terminal with command "sudo pip install --upgrade gensim".
Detailed information & installation instructions : http://radimrehurek.com/2013/09/deep-learning-with-word2vec-and-gensim/ and http://radimrehurek.com/gensim/install.html

jellyfish
**********************************
This module is needed for Normalization to compute Character edit distance (Levenshtein) and Phonetic edit distance (Metaphone).
To install the module, download the zip from the site https://github.com/sunlightlabs/jellyfish , unzip it . Then navigate to the unzipped folder in terminal and run the command "python setup.py install".
tutorial : https://pypi.python.org/pypi/jellyfish (optional : not needed for using this tool).

PyDbLite
**********************************
This is an adapter for SQLite in-memory database and is needed to manipulate the word clusters.
Installation instructions : http://www.pydblite.net/en/index.html

pyenchant
**********************************
This module is required for Out-of-vocabulary word checking and spelling suggestions.
Installation command : "sudo pip install pyenchant"
More information : https://pythonhosted.org/pyenchant/api/enchant.html (optional : not needed for using this tool)

Other modules
**********************************
Other used modules are pre-existing in Python 2.7.



Usage instructions
**********************************
**********************************
1. Download the Project as a zip file from GitHub
2. Unzip and navigate to the unzipped "NERD_Tweets" folder from terminal
3. Make sure all the prerequisite tools are present inside "NERD\_Tweets" folder and the required Python modules are installed. Also, add the Microsoft user token and Freebase API key in appropriate places in the file "nerd\_tweets.py" as shown in the screenshots.
4. Run the command  "python nerd\_tweets.py sample\_input.txt sample\_output.txt" 
	sample\_input.txt : contains sample tweets separated by lines
	sample\_output.txt : The tool will output the extracted named entities with their disambiguations  (Screenshots/terminal\_output.png).

Queries
**********************************
For any queries, please contact me through mail "srpatra88@gmail.com". For reference, please see https://github.com/srpatra88/Soumya_Thesis/tree/master/Reports
