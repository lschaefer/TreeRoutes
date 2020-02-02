import pandas as pd
import numpy as np

import requests

from PIL import Image
import base64
from places365 import run_placesCNN_basic_gen
import leighTmpLabels

import streamlit as st
import pydeck as pk
import polyline
import folium
from folium import IFrame
from folium.plugins import HeatMap
from geopy.distance import geodesic

import myKeys
myGoogleKey = myKeys.keys['google']
myMapBoxKey = myKeys.keys['mapbox']

"""
# TreeRoutes
Helping drivers find scenic routes
"""

# @st.cache

def mapRoutes(routesDF,mapBounds,iBest,iWorst,iFastest):
    # todo configure zoom based on route
    # see: https://wiki.openstreetmap.org/wiki/Zoom_levels
    swLat,swLon = mapBounds[0][0],mapBounds[0][1]
    neLat,neLon = mapBounds[1][0],mapBounds[1][1]
    mapCenter = [(neLat+swLat)/2.,(neLon+swLon)/2.]
    m = folium.Map(mapCenter, tiles='CartoDB positron')
    m.fit_bounds(mapBounds)

    # is there a way to feed dataframe directly into polylines?
    for routeIt, route in routesDF.iterrows():
        color='green' if routeIt==iBest else 'blue'
        for iS,segment in enumerate(route.polyLinesSplit):
            encoded = base64.b64encode(open(route.imageNames[iS], 'rb').read())
            html = '<img src="data:image/jpg;base64,{}">'.format
            frame=IFrame(html(encoded.decode('UTF-8')), width=4200, height=3200)
            #folium.PolyLine(segment,color=color, popup=folium.Popup(frame)).add_to(m)
            frame = IFrame(html(encoded.decode('UTF-8')), width=500, height=300)
            #folium.PolyLine(segment,color=color, tooltip=folium.Tooltip(frame)).add_to(m)


            html = '<img src="data:image/png;base64,{}">'.format
            resolution, width, height = 75, 7, 3
            iframe = IFrame(html(encoded), width=(width*resolution)+20, height=(height*resolution)+20)
            popup = folium.Popup(iframe, max_width=2650)
            folium.PolyLine(segment,color=color, tooltip=popup).add_to(m)


        #folium.PolyLine(route.polyLines,color=color).add_to(m)

    return st.markdown(m._repr_html_(), unsafe_allow_html=True)

debug=False

user_inS = st.text_input("Enter your starting point",'4605 springfield ave, philadelphia')
user_inE = st.text_input("Enter your ending point",'philadelphia museum of art')

if user_inS!='' and user_inE!='':
    
    # formatting
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

    images=[] # this will be a list of sublists: each list entry corresponds to a route, each sublist entry corresponds to images along that route
    imageNames=[]
    scores=[] # this will be a list of scores: each list entry corresponds to a route
    times=[] # time for each route. this is read directly from the existing api response. (could be retrieved from the DF but it's not working, idk why)
    polyLines=[] # detailed coordinate system along route, to draw on map
    polyLinesSplit=[] # list of lists, with segments of each route

    routes = gtrj['routes'] # the only other info in the json is the `geocoded_waypoints' which isn't very useful

    # now look at all the returned routes
    for iR,route in enumerate(routes):
        polyLinesSplit.append([])
        images.append([])# initialize list to hold images along route iR
        imageNames.append([])# initialize list to hold image names along route iR
        
        routeScore = 1.

        # get an image every 10 miles = 16km
        # if the route is less than 30 miles, take 3 images
        picFreq = 16000
        picIt = 1
        routeDistance=route['legs'][0]['distance']['value'] # in meters (use 'text' key instead to get a string e.g. '35 mi')
        if routeDistance<3.*picFreq:
            picFreq = routeDistance/4.

        # get the polyLine for the route (there is an alternative method in the commented chunk below)
        thisLine = polyline.decode(route['overview_polyline']['points'])
        polyLines.append(thisLine)

        # split it into segments for each image
        latlon=[] # to store location for images
        distanceTraveled=0 # to track when to collect image
        lineSegments = [thisLine[0]] # this is the list that will go into polyLinesSplit
        # start with second point in list, then segments will be between previous and this point
        for iP,point in enumerate(thisLine[1:]):
            lineSegments.append(point)
            thisDist = geodesic(thisLine[iP-1],point).meters
            distanceTraveled+=thisDist
            if distanceTraveled > picFreq or point==thisLine[-1]:
                # take this point for an image
                latlon.append(point)
                # save this as its own segment, reset lineSegments array
                polyLinesSplit[-1].append(lineSegments)
                lineSegments=[point]
                distanceTraveled=0

        # now get the images
        for imgPoint in (latlon):
            myLat=imgPoint[0]
            myLon=imgPoint[1]
            imageResponse=requests.get('https://maps.googleapis.com/maps/api/streetview?size=600x400&location='+str(myLat)+','+str(myLon)+'&source=outdoor&key='+myGoogleKey)
            if not imageResponse.status_code==200:
                continue
            images[-1].append(imageResponse)

            # start: code that will change once i have a proper cnn
            # get CNN output of this image.
            # first save it to the expected tmp location
            with open('myTest.jpg','wb') as fout:
                fout.write(imageResponse.content)
            probs,classes = run_placesCNN_basic_gen.runBasicCNN()
            # save it again for later
            outName=str(iR)+'_'+str(myLat)+'_'+str(myLon)+'.jpg'
            with open(outName,'wb') as fout:
                fout.write(imageResponse.content)
            imageNames[-1].append(outName)

            # loop through classes and translate to scenery score for this image
            imageScore = 0.
            for i in range(len(probs)):
                if classes[i] not in leighTmpLabels.leighLabels:
                    continue
                imageScore += float(probs[i])*leighTmpLabels.leighLabels[classes[i]]
            routeScore *= imageScore
            # end: code that will change once i have a proper cnn
            
        # route score combined over all images
        scores.append(routeScore)
        times.append(route['legs'][0]['duration']['value'])
        
        # # get actual coordinates along the route with snapToRoads API
        # # this could be useful if i want to draw which segments of each road is most scenic
        # # for now keep it turned off, and figure out the default
        # path='path='
        # for step in route['legs'][0]['steps']:
        #     path+='%.6f,%.6f|' %(step['start_location']['lat'],step['start_location']['lng'])
        #     # for last turn, take the end as well
        #     path+='%.6f,%.6f' %(step['end_location']['lat'],step['end_location']['lng'])
        #     try:
        #         googleRoads = requests.get('https://roads.googleapis.com/v1/snapToRoads?'+path+'&key='+myGoogleKey+'&interpolate=true')
        #     except:
        #         googleRoads = "connection refused"
        #     print(googleRoads)
        #     grj = googleRoads.json()
        #     if debug:
        #         print(json.dumps(grj,sort_keys=True,indent=4))
        #     # make a polyline from the returned coordinates
        #     for segment in grj['snappedPoints']:
        #         latLon=segment['location']
        #         polyLines.append([latLon['latitude'],latLon['longitude']])

    if debug:
        print(len(routes),len(scores),len(times),len(images),len(imageNames),len(polyLines),len(polyLinesSplit))
    routesDF = pd.DataFrame(list(zip(routes,scores,times,images,imageNames,polyLines,polyLinesSplit)),
                            columns=['route', 'score', 'time', 'images','imageNames','polyLines','polyLinesSplit'])

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
    mapRoutes(routesDF,mapBounds,iBest,iWorst,iFastest)
    

    st.write('Your most scenic route is %.0f percent more scenic and %d minutes (%.0f percent) slower than the fastest route' %(100.*(routesDF.iloc[iBest]['score']-routesDF.iloc[iFastest]['score'])/routesDF.iloc[iFastest]['score'],(routesDF.iloc[iBest]['time']-routesDF.iloc[iFastest]['time'])/60.,100.*(routesDF.iloc[iBest]['time']-routesDF.iloc[iFastest]['time'])/routesDF.iloc[iFastest]['time']))

    image = routesDF.iloc[iBest]['images'][0].content
    st.write('Your most scenic route is along '+routesDF.iloc[iBest]['route']['summary'])
    st.image(image, caption='On your most scenic route you will see',  use_column_width=True)

    image = routesDF.iloc[iWorst]['images'][0].content
    st.write('Your least scenic route is along '+routesDF.iloc[iWorst]['route']['summary'])
    st.image(image, caption='On your least scenic route you will see',  use_column_width=True)


