from PIL import Image
import glob
import os

def resizeImage(imgName):
    image=Image.open(imgName)
    image=image.resize((256,256))
    image.save(imgName)
    return
