# TreeRoutes
Recommends the most scenic route for your roadtrip

## This currently only works locally on data I have on my laptop.

## Setup
You will need access to google maps and streetview APIs.
Create an account if you don't have one, and set up an API key.

https://cloud.google.com/maps-platform/

Create a file in the top directory called `myKeys.py` with the structure: 
`keys={'google':[your-API-key]}`
`[your-API-key]` should be replaced with your API key, as a string.

## To run the route recommender on existing trained data
`streamlit run myUI.py`

This will open an interactive tab in your browser where you can input your start and endpoints.

## To train the CNN:
Currently this is hacky but will improve soon.
`python runPlacesCnnOnScenicOrNotImages___leighLabels.py`

## To validate the CNN:

## To do some EDA on the tree coverage data:

## To do some EDA on the nature sightings data:

## To do some EDA on the scenery score:

## Data needed for each script:
| Script | Expected filename | Description | Where to download |
| --- | --- | --- | --- |
| `runPlacesCnnOnScenicOrNotImages___leighLabels.py` | `data/images.tsv` | Contains scenery scores and (links to) 200k images | http://scenicornot.datasciencelab.co.uk/ |
