import pandas as pd

import requests

from PIL import Image
import base64
from places365 import run_sceneryCNN_basic

import streamlit as st
import polyline
import folium
from folium import IFrame
from geopy.distance import geodesic
import os

import myKeys
myGoogleKey = myKeys.keys['google']

"""
# TreeRoutes
Make the journey your destination.
"""

def mapRoutes(routesDF,mapBounds,iBest,iWorst,iFastest,showMarkers):
    swLat,swLon = mapBounds[0][0],mapBounds[0][1]
    neLat,neLon = mapBounds[1][0],mapBounds[1][1]
    mapCenter = [(neLat+swLat)/2.,(neLon+swLon)/2.]
    m = folium.Map(mapCenter, tiles='CartoDB positron')
    m.fit_bounds(mapBounds)

    # is there a way to feed dataframe directly into polylines?
    for iR, route in routesDF.iterrows():
        color='green' if iR==iBest else 'blue'

        folium.PolyLine(route.polyLines,color=color, tooltip='Route score: %.1f; Nature sightings: %.1f' %(route.score,route.natureCount)).add_to(m)

        if showMarkers:
            for iC,coord in enumerate(route.latLons):
                encoded = base64.b64encode(open(route.imageNames[iC], 'rb').read()).decode('UTF-8')
                html = '<figure> <img src="data:image/jpg;base64,%s" height=225 width=300/> <figcaption> Image Score: %0.2f </figcaption> </figure>' %(encoded,route.imageScores[iC])
                frame=IFrame(html, width=363, height=275)
                popup = folium.Popup(frame,max_width=410)
                folium.Marker(coord,popup=popup,icon=folium.Icon(color=color)).add_to(m)

    return st.markdown(m._repr_html_(), unsafe_allow_html=True)

def getRouteScores(routes):

    # lists
    natureCounts=[] # nature score for each route
    scores=[] # score for each route
    times=[] # time for each route

    # lists of lists, where each entry corresponds to a route
    images=[] # images
    imageScores=[] # score for each image
    imageNames=[] # savename of each image
    polyLines=[] # detailed coordinate system along route, to draw on map
    latLons=[] # points defining segments (for corners of nature boxes / where images are taken)

    # get segments unique to this route, and the distance of unique segments
    uniquePolyLines=[]
    lengthPolyLines=[]
    for iR,route in enumerate(routes):
        uniquePolyLines.append([])
        thisLine = polyline.decode(route['overview_polyline']['points'])
        thisLine = [(round(l[0],4),round(l[1],4)) for l in thisLine]
        otherLines = []
        for iRR,rroute in enumerate(routes):
            if iRR==iR:
                continue
            otherLine = polyline.decode(rroute['overview_polyline']['points'])
            otherLines.extend( [(round(l[0],4),round(l[1],4)) for l in otherLine] )
        thisDist = 0
        uniquePolyLines[-1] = [l for l in thisLine if l not in otherLines]
        for iP,point in enumerate(uniquePolyLines[-1][:-1]):
            thisDist += geodesic(point,uniquePolyLines[-1][iP+1]).meters
        lengthPolyLines.append(thisDist)

    for iR,route in enumerate(routes):

        # initialize lists of lists to hold images along route iR
        images.append([])
        imageNames.append([])
        imageScores.append([])
        latLons.append([])

        # get the full and unique polyLines for each route
        polyLines.append(polyline.decode(route['overview_polyline']['points']))
        thisLine = uniquePolyLines[iR]

        routeScore = 1.
        natureCount = 0.5 # not 0 just in case there are 0 sightings

        # take 5 images per route
        #routeDistance=route['legs'][0]['distance']['value'] # in meters (use 'text' key instead to get a string e.g. '35 mi')
        routeDistance=lengthPolyLines[iR]
        picFreq = routeDistance/5.

        # split route into segments
        distanceTraveled=0
        totalDistance=0
        for iP,point in enumerate(thisLine[:-1]):
            thisDist = geodesic(point,thisLine[iP+1]).meters
            distanceTraveled+=thisDist
            totalDistance+=thisDist
            if distanceTraveled > picFreq or point==thisLine[-2]:
                # take this point for an image
                latLons[-1].append(point)
                distanceTraveled=0

        # get data for this segment
        for iP,point in enumerate(latLons[-1]):
            myLat=point[0]
            myLon=point[1]

            # get iNaturalist data in square boxes
            if iP<len(latLons[-1])-1:
                latMin=str(min(myLat,latLons[-1][iP+1][0]))
                latMax=str(max(myLat,latLons[-1][iP+1][0]))
                lonMin=str(min(myLon,latLons[-1][iP+1][1]))
                lonMax=str(max(myLon,latLons[-1][iP+1][1]))
                thisArea = geodesic((latMin,lonMin),(latMax,lonMin)).meters*geodesic((latMin,lonMax),(latMax,lonMax)).meters
                try:
                    nature=requests.get("https://api.gbif.org/v1/occurrence/search?datasetKey=50c9509d-22c7-4a22-a47d-8c48425ef4a7&decimalLatitude="+str(latMin)+","+str(latMax)+"&decimalLongitude="+str(lonMin)+","+str(lonMax))
                    if nature.status_code==200:
                        natureCount+=len(nature.json()['results'])/float(thisArea)
                except requests.exceptions.ConnectionError:
                    if debug:
                        print("connection error with nature sightings request")
                    pass

            # get the images
            imageResponse=requests.get('https://maps.googleapis.com/maps/api/streetview?size=600x400&location='+str(myLat)+','+str(myLon)+'&source=outdoor&key='+myGoogleKey)
            if not imageResponse.status_code==200:
                continue
            images[-1].append(imageResponse)

            # get CNN output of this image.
            # save image for later
            outName=str(iR)+'_'+str(myLat)+'_'+str(myLon)+'.jpg'
            with open(outName,'wb') as fout:
                fout.write(imageResponse.content)
            imageScore = run_sceneryCNN_basic.run_sceneryCNN_basic(outName,'places365/')
            if imageScore == None:
                continue
            imageNames[-1].append(outName)
            imageScores[-1].append(imageScore)

        # route score combined over all images
        scores.append(natureCount*sum(imageScores[-1])/float(len(imageScores[-1])))
        times.append(route['legs'][0]['duration']['value'])
        natureCounts.append(natureCount)
        
    if debug:
        print(len(routes),len(scores),len(times),len(images),len(imageScores),len(imageNames),len(polyLines),len(latLons))

    routesDF = pd.DataFrame(list(zip(routes,natureCounts,scores,times,images,imageScores,imageNames,polyLines,latLons)),
                            columns=['route', 'natureCount','score', 'time', 'images','imageScores','imageNames','polyLines','latLons'])

    return routesDF

debug=False

user_inS = st.text_input("Enter your starting point",'4605 springfield ave, philadelphia')
user_inE = st.text_input("Enter your ending point",'philadelphia museum of art')

if user_inS=='' and user_inE=='':
    homeImage = Image.open('homePage.jpg')
    st.image(homeImage, use_column_width=True)

elif user_inS!='' and user_inE!='':

    showMarkers = st.checkbox('Show segments used in sampling')
    
    # formatting
    user_inS = user_inS.replace('&','+')
    user_inE = user_inE.replace('&','+')
    user_inS = user_inS.replace(' ','+')
    user_inE = user_inE.replace(' ','+')
    
    # get the google routes
    googleRoute=requests.get('https://maps.googleapis.com/maps/api/directions/json?origin='+user_inS+'&destination='+user_inE+'&alternatives=true&key='+myGoogleKey)
    if debug:
        print(googleRoute)
    gtrj=googleRoute.json()

    if debug:
        import json
        print(json.dumps(gtrj,sort_keys=True,indent=4))

    routes = gtrj['routes']
    routesDF = getRouteScores(routes)

    # now choose the best route
    iBest = routesDF['score'].idxmax()
    iWorst = routesDF['score'].idxmin()
    iFastest = routesDF['time'].idxmin()

    # draw them all on the map
    mapNELat = routesDF.iloc[0].route['bounds']['northeast']['lat']
    mapNELon = routesDF.iloc[0].route['bounds']['northeast']['lng']
    mapSWLat = routesDF.iloc[0].route['bounds']['southwest']['lat']
    mapSWLon = routesDF.iloc[0].route['bounds']['southwest']['lng']
    mapBounds = [[mapSWLat,mapSWLon],[mapNELat,mapNELon]]
    mapRoutes(routesDF,mapBounds,iBest,iWorst,iFastest,showMarkers)

    # choose the best image on the best route, and the worst image on the worst route
    iBestI = routesDF.iloc[iBest]['imageScores'].index(max(routesDF.iloc[iBest]['imageScores']))
    iWorstI = routesDF.iloc[iWorst]['imageScores'].index(min(routesDF.iloc[iWorst]['imageScores']))
    
    timeDiff = routesDF.iloc[iBest]['time']-routesDF.iloc[iFastest]['time']
    if timeDiff < 60:
        timeDiff = '%d seconds' %timeDiff
    else:
        timeDiff = '%0.f minutes' %(timeDiff/60.)

    if iBest==iFastest:
        st.write('Oh joy! Your most scenic route is also the fastest!')
    else:
        st.write('Your most scenic route is %.0f percent more scenic and %s (%.0f percent) slower than the fastest route' %(100.*(routesDF.iloc[iBest]['score']-routesDF.iloc[iFastest]['score'])/routesDF.iloc[iFastest]['score'],timeDiff,100.*(routesDF.iloc[iBest]['time']-routesDF.iloc[iFastest]['time'])/routesDF.iloc[iFastest]['time']))

    image = routesDF.iloc[iBest]['images'][iBestI].content
    st.write('Your most scenic route is along '+routesDF.iloc[iBest]['route']['summary']+'. On your most scenic route you will see: ')
    st.image(image, caption='Image score: %.1f' %max(routesDF.iloc[iBest]['imageScores']), use_column_width=True)

    image = routesDF.iloc[iWorst]['images'][iWorstI].content
    st.write('Your least scenic route is along '+routesDF.iloc[iWorst]['route']['summary']+'. On your least scenic route you will see: ')
    st.image(image, caption='Image score: %.1f' %min(routesDF.iloc[iWorst]['imageScores']), use_column_width=True)

