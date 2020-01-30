import pandas as pd
import getImage # to scrape df image from website
from PIL import Image
import os

def makeCsvWithLocalPath():
  #  - make a pandas dataframe from `scenic or not' data (sond), using the images.tsv file
  sond = pd.read_csv('data/images.tsv',sep='\t')
  # make sure each entry has valid input
  sond.dropna()
  sond = sond[sond['Geograph URI'].str.contains("http://www")]
  #sond.reset_index()
  # to run in parallel
  sond = sond.sample(frac=1).reset_index(drop=True)
  
  #  - retrieve actual image from provided link, add local path to dataframe
  saveNames=['']*len(sond)
  for index, row in sond.iterrows():
    imgLink = row['Geograph URI']
    saveName = 'data/sond/'+imgLink.split('/')[-1]
    if not os.path.exists('data/sond/'):
      os.makedirs('data/sond/')

    try: # see if it exists locally
      test=Image.open(saveName+'.jpg')
    except:
      getImage.getImage(imgLink,saveName,rewrite=True)

    saveName+='.jpg'
    try:
      test=Image.open(saveName)
    except:
      saveName = ''

    saveNames[index] = saveName
  sond['Images'] = saveNames
  sond.drop(sond[sond['Images']==''].index, inplace=True)
  sond.reset_index()
  print(sond.head())
  print(sond.info())
  sond.to_csv('data/imagesWithJpg.tsv',sep='\t')

if __name__=='__main__':
    makeCsvWithLocalPath()
