import pandas as pd
import numpy as np

import requests

from PIL import Image
from places365 import run_placesCNN_basic_gen
import leighTmpLabels

import streamlit as st
import pydeck as pk
import polyline
import folium
from folium.plugins import HeatMap

import myKeys
myGoogleKey = myKeys.keys['google']
myMapBoxKey = myKeys.keys['mapbox']

"""
# TreeRoutes
Helping drivers find scenic routes
"""

# @st.cache

def mapRoutes(routesDF,mapCenter,iBest,iWorst,iFastest):
    # todo configure zoom based on route
    # see: https://wiki.openstreetmap.org/wiki/Zoom_levels
    m = folium.Map(mapCenter, tiles='CartoDB positron', zoom_start=10)

    # is there a way to feed dataframe directly into polylines?
    for routeIt, route in routesDF.iterrows():
        color='green' if routeIt==iBest else 'blue'
        folium.PolyLine(route.polyLines,color=color).add_to(m)

    return st.markdown(m._repr_html_(), unsafe_allow_html=True)

debug=True

user_inS = st.text_input("Enter your starting point","4605 springfield ave, philadelphia")
user_inE = st.text_input("Enter your ending point", "272 summit ave")

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
    scores=[] # this will be a list of scores: each list entry corresponds to a route
    times=[] # time for each route. this is read directly from the existing api response. (could be retrieved from the DF but it's not working, idk why)
    polyLines=[] # detailed coordinate system along route, to draw on map

    routes = gtrj['routes'] # the only other info in the json is the `geocoded_waypoints' which isn't very useful

    # now look at all the returned routes
    for iR,route in enumerate(routes):
        images.append([])# initialize list to hold images along route iR
        
        routeScore = 1.

        # get images along route.
        # meh for now just choose 2 images for each route, the first after 1/3 and the second after 2/3 
        numPics = 2
        picIt = 1
        routeDistance=route['legs'][0]['distance']['value'] # in meters (use 'text' key instead to get a string e.g. '35 mi')
        distanceTraveled=0
        latlon=[]
        # step through steps of route until you've reached the desired distance
        # need to fix this to work if there are fewer steps than intervals
        # (in this case it's safe to just take the middle between)
        for step in route['legs'][0]['steps']:

            distanceTraveled+=step['distance']['value']
            if distanceTraveled>=picIt*routeDistance/float(numPics+1):
                picIt+=1
                # just choose the end of this step. 
                # trying to do something fancy like picking halfway between the lat and long could find somewhere not at all on the route
                thisLat=step['end_location']['lat']
                thisLon=step['end_location']['lng']
                latlon.append([thisLat,thisLon])
            if picIt>numPics:
                break

        for it in range(numPics):
            myLat=latlon[it][0]
            myLon=latlon[it][1]
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

        # here is the default
        # use the alternate (in the commented chunk below) to get individual segments
        polyLines.append(polyline.decode(route['overview_polyline']['points']))
        
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
        print(len(routes),len(scores),len(times),len(images),len(polyLines))
    routesDF = pd.DataFrame(list(zip(routes,scores,times,images,polyLines)),
            columns=['route', 'score', 'time', 'images','polyLines'])

    st.write ('scores: ' ,scores)
    st.write ('times: ' ,times)
    # now choose the best route
    iBest = routesDF['score'].idxmax()
    iWorst = routesDF['score'].idxmin()
    iFastest = routesDF['time'].idxmin()

    # draw them all on the map
    # color corresponding to green
    # segments coresponding to score if I use snapToRoads API
    mapCenterLat = (routesDF.iloc[0].route['bounds']['northeast']['lat']+routesDF.iloc[0].route['bounds']['southwest']['lat'])/2.
    mapCenterLon = (routesDF.iloc[0].route['bounds']['northeast']['lng']+routesDF.iloc[0].route['bounds']['southwest']['lng'])/2.
    mapRoutes(routesDF,[mapCenterLat,mapCenterLon],iBest,iWorst,iFastest)
    

    st.write ('best: ',iBest,'; worst: ',iWorst,'; fastest: ',iFastest)
    st.write('Your most scenic route is %.0f percent more scenic and %d minutes (%.0f percent) slower than the fastest route' %(100.*(routesDF.iloc[iBest]['score']-routesDF.iloc[iFastest]['score'])/routesDF.iloc[iFastest]['score'],(routesDF.iloc[iBest]['time']-routesDF.iloc[iFastest]['time'])/60.,100.*(routesDF.iloc[iBest]['time']-routesDF.iloc[iFastest]['time'])/routesDF.iloc[iFastest]['time']))

    image = routesDF.iloc[iBest]['images'][0].content
    st.write('Your most scenic route is along '+routesDF.iloc[iBest]['route']['summary'])
    st.image(image, caption='On your most scenic route you will see',  use_column_width=True)

    image = routesDF.iloc[iWorst]['images'][0].content
    st.write('Your least scenic route is along '+routesDF.iloc[iWorst]['route']['summary'])
    st.image(image, caption='On your least scenic route you will see',  use_column_width=True)


