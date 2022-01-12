# ripe-alerts-AI

This code base serves as an area to experiment with different anomaly detection methods and machine learning techniques that can be applied to the Ripe Alerting tool. Most code is setup in Jupyter notebooks, altough some of the modules that can be directly used in the Alerting tool are written as separete modules.

## Instalation

To install the code make a conda environment, other environment tools might work, but require to delete some of the conda specific dependencies. Other environments have not been tested.

Than simply open the traceroute_anomaly_detection_comparison.ipynb, select the correct kernel.

## Finding measurements

Measurements can be downloaded from https://atlas.ripe.net/measurements/#tab-anchor. Select a measurement of type Traceroute (by clicking on the id), that mentions IPv4 (IPv6 might work, but this has not been tested yet). Than going to the Downloads tab, and selecting the start and stop date (it is recomended to select just one day, not the standard three days). After downloading measurement data add the path to the dataset in the path to dataset variable under the chapter 'Import Data'. Importing the data for the first time takes longer since the json is being converted to a more manageble format (feather), and the AS numbers are collected from the Ripe Stat api. This process can take rougly 4 minutes but is dependent on the size of the dataset being imported. Ones the process is done  running it a second time will be faster, cause now the feather will be used.