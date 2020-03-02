# TreeRoutes
## Make the journey your destination.
This is the framework used to train, validate, and run the scenic route recommender.

It uses [Google](https://cloud.google.com/maps-platform/) 
and [iNaturalist](https://www.inaturalist.org/) 
APIs to collect data according to the user's input start and endpoints,
including Google Streetview images along the route.
It then calculates the scenery score of each image using a custom-trained convolutional neural network (CNN).
This CNN retrained the last layer of the [Places365 CNN](http://places.csail.mit.edu/),
with [Scenic Or Not](http://scenicornot.datasciencelab.co.uk/) labeled data.
The retraining procedure consists of code that can be found in the submodule `places365` 
(forked and updated from the original research group's [repo](https://github.com/CSAILVision/places365)).

## Setup
To access the app, you can simply go to http://treeroutes.xyz:8501/ .
If you would prefer to run the app locally, you will need access to google maps and streetview APIs.
Create an account if you don't have one, and set up an API key.

https://cloud.google.com/maps-platform/

Create a file in the top directory called `myKeys.py` with the structure: 
`keys={'google':[your-API-key]}`
`[your-API-key]` should be replaced with your API key, as a string.

You will additionally need some specific python libraries:

 * `pip install torch`
 * `pip install streamlit`
 * `pip install pillow==6.1`
 * `pip install folium`
 * `pip install polyline`
 * `pip install geopy`

## To run the route recommender (on the existing trained model):
`streamlit run myUI.py`

This will open an interactive tab in your browser where you can input your start and endpoints.

## To train the CNN:
This is designed to run on GoogleColab and it takes quite a while. Be patient and only start when you can leave it running (e.g. overnight)!
The actual training happens in `places365/train_placesCNNColab.py`.
There are some additional steps that need to be taken to set up the colab environment, 
which are outlined in `train_placesSceneryScoreCNNColab.ipynb`

## To validate the performance of the CNN:
This exists in `places365/plotModelResults.ipynb`.

## EDA on the scenic or not data:
This exists in `ScenicOrNotEDA.ipynb`.

## EDA on the iNaturalist data:
This exists in `iNaturalistEDA.ipynb`.

