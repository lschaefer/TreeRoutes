# TreeRoutes
## Make the journey your destination.
This is the framework used to train, validate, and run the scenic route recommender.
Users enter their start and endpoints and the most scenic route is recommended.

This app uses [Google APIs](https://cloud.google.com/maps-platform/) 
and [iNaturalist data](https://www.inaturalist.org/) 
via [the Global Biodiversity Information Facility API](https://www.gbif.org/)
to collect data along users' input start and endpoints,
including Google Streetview images along the route.
It then calculates the scenery score of each image using a custom-trained convolutional neural network (CNN).
This CNN was trained on the last layer of the [Places365 CNN](http://places.csail.mit.edu/),
with [Scenic Or Not](http://scenicornot.datasciencelab.co.uk/) labeled data.
The retraining procedure consists of code that can be found in the submodule `places365` 
(forked and updated from the original research group's [repo](https://github.com/CSAILVision/places365)).

## Setup
To access the app, you can simply go to http://treeroutes.xyz:8501/ .

If you would prefer to run the app locally, there are a few steps you should take.

1. You will need access to google maps and streetview APIs.
Create an account if you don't have one, and set up an API key.
https://cloud.google.com/maps-platform/
(The GBIF API can be used without setting up an account.)

2. Create a file in the top directory called `myKeys.py` with the structure: 
`keys={'google':[your-API-key]}`
`[your-API-key]` should be replaced with your API key, as a string.

3. You will additionally need some specific python libraries:

 * `pip install torch`
 * `pip install streamlit`
 * `pip install pillow==6.1`
 * `pip install folium`
 * `pip install polyline`
 * `pip install geopy`

## To run the route recommender (on the existing trained model):
`streamlit run myUI.py`

This will open an interactive tab in your browser where you and your friends can input your start and endpoints.

## To train the CNN:
This is designed to run on GoogleColab and it takes quite a while. Be patient and only start when you can leave it running (e.g. overnight)!
The actual training happens in `places365/train_placesCNNColab.py`.
There are some additional steps that need to be taken to set up the colab environment, 
which are outlined in `train_placesSceneryScoreCNNColab.ipynb`

## Validation of the performance of the CNN:
This exists in `places365/plotModelResults.ipynb`.

## EDA on the scenic or not data:
This exists in `ScenicOrNotEDA.ipynb`.

## EDA on the iNaturalist data:
This exists in `iNaturalistEDA.ipynb`.

