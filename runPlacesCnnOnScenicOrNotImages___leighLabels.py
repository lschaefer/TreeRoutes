import pandas as pd
import seaborn as sns
# local tools
import getImage
from places365 import run_placesCNN_basic_gen
import leighTmpLabels

test=True

# THIS IS ALL TO VALIDATE MY SCENERY SCORING.

# 1. make a pandas data frame from `scenic or not' (son) data, using the images.tsv file
# THIS FILE IS NOT IN THE REPO
sond = pd.read_csv('data/images.tsv',sep='\t')
# TODO add some cleaning 
# (then won't need that http check (hack) lower down)
#print(sond.head())

# 2. for now: just use everything as train since i'm using this dummy system anyway.
   # 2. (eventually: split into train and test groups)

# 3. loop through train images (using url's from dataframe)
scenScore=[0]*len(sond.index)

for index, row in sond.iterrows():
    imgLink = row['Geograph URI']
    
    # get the image, always write it to the same file name
    print (imgLink)
    if not "http://www" in imgLink:
            continue
    img = getImage.getImage(imgLink,'myTest')
    if img==None:
        scenScore[index]=-1
        continue

    # 4. run basic CNN on train images
    probs,classes = run_placesCNN_basic_gen.runBasicCNN()
    totalScore = 0.
    for i in range(len(probs)):

        # 5. for now: assign my scenery score from leighDummyLabels.py according to labels and percentages.
           # 5. (eventually: calculate scenery score based on what that paper did. retrain last layer of CNN?)
        if classes[i] not in leighDummyLabels.leighLabels:
            continue
        thisDummyScore = leighDummyLabels.leighLabels[classes[i]]
        totalScore += float(probs[i])*leighDummyLabels.leighLabels[classes[i]]


    # 6. compare to scenic or not average score (eventually: with errors) for test data, or train if using leighDummyLabels.
    # print ("total scenery score : %.3f ... compared to scenic or not: %.3f" %(totalScore,row['Average']))
    scenScore[index]=totalScore

    if test and index>20:
        break

sond['sceneryScore'] = scenScore

sns.relplot(x="Average",
            y="sceneryScore",
            data=sond,
            kind='line',
            ci=None,
         )

# save the output dataframe to some format!!! 
# because this takes a while to run, don't want to have to do it again until I have a cnn! 
sond.to_csv('scenScoreValidation.csv',index=False)

