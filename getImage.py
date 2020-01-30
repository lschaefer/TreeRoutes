from bs4 import BeautifulSoup
import urllib3 
import certifi
import sys
import os
import resizeImage

def getImage(url,save='',rewrite=False):

    save=save.replace('.jpg','')
    if not rewrite and os.path.exists(save+'.jpg'):
        return open(save+'.jpg','r')

    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    soup = BeautifulSoup(http.request('GET', url).data,features="lxml")
    imagePaths = [img['src'] for img in soup.findAll('img') if "jpg" in img['src']]

    if len(imagePaths)==0:
        print ("ERROR! we did not get any jpg from this url !!! Exiting.", url)
        return
    elif len(imagePaths)>1:
        # print ("ERROR! we got more than one jpg from this url !!! Exiting.", url)
        # print(imagePaths)
        # there were only two cases of this, and in both, the first entry was the correct one.
        imagePaths=[imagePaths[0]]
        # return

    print ( url)
    print (len(imagePaths))
    print (imagePaths)
    imagePath=imagePaths[0]
    imageFile = http.request('GET', imagePath)
    if save!='':
        with open(save+'.jpg','wb') as fout:
            fout.write(imageFile.data)

    resizeImage.resizeImage(save+'.jpg')

    return imageFile.data

# examples:
#getImage('https://www.geograph.org.uk/photo/7')
#getImage('https://www.geograph.org.uk/photo/7','myTest')
