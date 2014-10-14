#Use this script to test against Ritter_groundtruth.txt.
#Note: Script expects "YOUR_OUTPUT" to be in the following format (i.e. tweet tab extracted entities)
# Example ----  @Jessica_Chobot did you see the yakuza vs zombies .... smh but cool at the same time	['the yakuza']

import jellyfish
import ast
f1 = open("YOUR_OUTPUT",'r')
f2 = open('Ritter_groundtruth.txt','r')
out1 = f1.readlines()
out2 = f2.readlines()
tp,tn,fp,fn=0,0,0,0
for l1 in out1:
    levenshtein = 100
    s1=''
    s2=''
    test1 = l1.split('\t')
    for l2 in out2:
        test2 = l2.split('\t')
        levenshtein2 = jellyfish.levenshtein_distance(test1[0],test2[0])
        if levenshtein2 < levenshtein:
            s1 = l1
            s2 = l2
            levenshtein = levenshtein2
    print 'Tweet :::::'+test1[0]+'\n'
    predicted = s1.split('\t')
    actual = s2.split('\t')
    predicted_entities = ast.literal_eval(predicted[1])
    predicted_entities = [x.replace('\n','') for x in predicted_entities]
    predicted_entities = filter(lambda a: a != '',predicted_entities)
    actual_entities = actual[1].split('||')
    actual_entities = [x.replace('\n','') for x in actual_entities]
    actual_entities = filter(lambda a: a != '',actual_entities)
    print 'Predicted entities : '+ str(predicted_entities)
    print 'Actual entities : '+ str(actual_entities)
    true_positives = list(set(predicted_entities).intersection(actual_entities))
    for x in predicted_entities:
        if x not in test1[0]:
            predicted_entities.remove(x)
            continue
        for y in actual_entities:
            if x in y or y in x:
                try:
                    true_positives.append(x)
                    predicted_entities.remove(x)
                    actual_entities.remove(y)
                except Exception:
                    continue
    predicted_entities = list(set(predicted_entities) - set(true_positives))
    actual_entities = list(set(actual_entities) - set(true_positives))
    false_positives = list(set(predicted_entities) - set(actual_entities))
    false_negatives = list(set(actual_entities) - set(predicted_entities))
    for x in false_positives:
        try :
            if x not in test1[0]:
                false_positives.remove(x)
                continue
            for y in true_positives:
                if x in y or y in x:
                    true_positives.append(x)
                    false_positives.remove(x)
                    continue
            for y in false_negatives:
                if x in y or y in x:
                    true_positives.append(x)
                    false_positives.remove(x)
                    false_negatives.remove(y)
        except Exception:
            continue
    true_positives = list(set(true_positives))
    print 'true positives\t' + str(true_positives)+'\n'
    print 'false positives\t' + str(false_positives)+'\n'
    print 'false negtives\t' + str(false_negatives)+'\n'
    if len(true_positives)>0:
        tp = tp + len(true_positives)
    if len(false_positives)>0:
        fp = fp + len(false_positives)
    if len(false_negatives)>0:
        fn = fn + len(false_negatives)
print "True Positives: "+str(tp)
print "False Positives: "+str(fp)
print "False Negatives: "+str(fn)
f1.close()
f2.close()
