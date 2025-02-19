## Energy & Weather Analytics (Demo)

This code is demonstration code for analyzing some sample weather and electricity 
meter data from a particular region in the world. The code first visualizes the 
existing data and produces html graphs. It then goes ahead and uses kmeans clustering 
to determine how meter energy consumption patterns over a year may be related to 
establish distinct clusters of meters that can be grouped together as similar. 
An html graph is used to map this data into a map and identify differences in clusters. 
It then brings weather information into the mix to determine the multivariate 
correlation (linear) between various weather parameters such as GHI, Wind, 
Irradiance, etc. and between meter energy consumption. This is then used with 
autoencoders to determine distinct possible load patterns existing among meters 
relative to weather. Highly correlated meteers would exhibit high correlation 
suggesting use of air conditioning to higher levels. 

### On HTML Rendering

Note that rendering times for some of the HTML files generated could be a bit
slow. So be patient when loading. I haven't really done any optimization for
rendering into a web browser

This code, when executed without parameters should take about a three minutes or
so to fully run and will produce four sets of html graphs that can be 
viewed in a web browser. These graphs will automatically load up in your default 
browser. But patience needed!

### On Documentation

Detailed API documentation is provided as an autogenerated html file called
**main.html**. This is generated using the command 

<pre>pdoc main --html --output-dir . --force</pre>

Additional documentation is embedded directly in the code. 

### Visualization of Energy Analytics Results
There are four different visualizatons that are produced as below. Note that some
limited conclusions can be drawn from analyzing the data. Refer below. The user
need not run the code as the HTML files have already been pre-generated for convenience

Note that the input used for generating visuals are the files:
a. **weather.xlsx** (modified to remove top row from original **weather_original.xlsx**)
b. **electricity.xlsx**


1. **graph_energy_meter.html**
This graph just graphs al the meters for all areas into a single HTML for
viewing the relationship between meters on a month by month and area by area
level. Good for just trying to understand some things about the data. Though
maybe a bit overkill and thus less useful. 

2. **graph_weather_energy_month.html**
This graph contains a yearly view per graph for every meter as organized
on an area by area basis. This is more useful than the previous graph. The 
weather parameters such as temperature, humidity are also graphed ontop of
each graph just to provide a relative baseline for energy consumption patterns. 
Again this graph is purely to better understand and visualize the data. 

3. **graph_energy_meter_clusters.html**
This graph does some ML and takes all the meter energy data for a year
and compares all meters to each other. The more closely clustered these
energy values are after normalization the more likely they are part of a single
cluster of energy consumption patterns. Optimal cluster graph is provided where
the code automatically determines the clusters, then the meters are pinned on
to a map and colour coded by those that have similar energy consumption patterns
And finally distinct cluster mean energies are mapped to show how th clusters vary
across the year in energy consumption. 

Meters are operating in about 5 distinct energy consumption profile patterns. 
This could suggest higher occupancy, lower energy efficiency of household or even
which groups of houses contain richer or poorer people.  

4. **graph_weather_energy_meter_clusters.html**
This graph looks at the relationship of energy consumption of meters and its
correlation with weather patterns. The first heat map shows a simple linear
pearson correlation while the second uses MSO style linear regression and plots
correlations. These correlations are then clustered and optimal number of clusters
determined. Finally, the clustering technique used is autoencoding and it is 
used to seperate different meters according to how closely they correlate with
weather. These are pinned to a map and colour coded. And clusters are also 
graphed as bar charts to show the variation in cluster correlation means. 

This result might be used for say, determining the type of load to be air conditioning 
(which might be highly correlated with weather or temperature) for particular households.
Of course, we note that while there is clustering of data, clusters are not as clearly
delineated and so different runs of the algoritm might yield different results. This 
suggests that load consumption patterns for the houses is not that distinct in the region 


### Running the code

TO RUN this code simply call:

1. If using conda, create python 3.11. conda environment and activate 
   <pre>conda create --name myenv python=3.11</pre>

2. Install requrements 
   <pre>pip install -r requirements.txt</pre> 

3. Run main.py 
   <pre>python main.py</pre>

4. To regenerate docs use
   
   <pre>pdoc main --html --output-dir . --force</pre>


### On Bugs and Future Work

I've noted a few bugs with the current code. For instance

1. ~~The use of tempfile to store html temp files mean that the html doesn't persist. For casuaul users this means that the html map data is not available for viewing unless the code is rerun~~ FIXED
2. Autoencoder based clustering doesn't work deterministically and gives different clusters for different runs. This is problematic as some consistency is needed. 
3. Current GPS location is not correct. Need to get the correct format as data should be from Doha. 
4. Fix tensor flow warning on execution and double check pip requirements.txt file. 


**Future Work**

1. Some kind of predictive formula should be generated from the work to provide a meaingful insights. Clusters need to be labeled with meaningful labels that provide predictive insights on the type of household to feedback into policy infrastructure on energy consumption controls
2. Need to get correct GPS coordinate format from HBKU
3. Need to incorporate other household data to work out the meaning behind clusters. Some data to be provided by HBKU
4. Paper publication to provide meaningful insights to users.  


### Author & License

This code was authored by Siraj Sabihuddin with last edits on Dec 15, 2024. It is released
under GPL v2 license

**Data Credit:** 
Data provided by HBKU 