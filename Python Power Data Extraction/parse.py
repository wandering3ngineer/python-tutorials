#-----------------------------------------------------------------------------
# Parse Data
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import json                        # JSON library for parsing JSON files
import zipfile                     # zipfile library for extracting zip data
import os                          # os functions for filename path
import re                          # regular expressions library
import datetime                    # grab the date and time library
import pandas                      # for iterating over date range
import numpy as np                 # for getting datatypes
import matplotlib.pyplot as plt    # pylab plotting with matplotlib


#-----------------------------------------------------------------------------
# Extract power data from a Zip file and grab the JSON data inside. This func
# is specific to the taipower data set 
#-----------------------------------------------------------------------------
def extract(filename, time_range):
    # Open zip file
    zf = zipfile.ZipFile(filename, 'r')
    
    # Grab file metadata
    zfdat = zf.infolist()

    # Regular expression to capture files that are not relevant log files
    # e.g. 2020-05-02/ or __MAXOSX/..... Only keep the log files. 
    regex = "((^__.*$)|(^.*\/$))"
    zfpat = re.compile(regex)
    
    # Go through and remove the MAC files from our list of files to extract
    # This uses LIST COMPREHENSION syntax which grabs each element i in zfdat 
    # and makes sure that its not equal to the regular expression. Then it 
    # applies the function func to it. 
    func=lambda x: x
    zfdat = [func(i) for i in zfdat if not re.match(zfpat, i.filename)]
    
    # Setup pandas date range (this is a DataFrame)
    time_range = pandas.date_range(start=time_range[0], end=time_range[1], freq='10min')
    
    # Regular expression to get specific dates of records from the zip file    
    regex = ""
    for i in time_range:
        regex = regex + "(" + i.strftime("%Y-%m-%d") + "\/" + i.strftime("%H_%M") + ".log" + "$)"
        regex = regex + "|"
    regex=regex[:-1]
    zfpat = re.compile(regex)
    
    # Go through and grab only those files associated with the given date range.
    zfdat = [i for i in zfdat if re.match(zfpat, i.filename)]

    # Open each file from the zip file and grab the JSON data
    data=[]
    for i in zfdat:
        with zf.open(i.filename) as zfdatfile:  
            data.append(json.loads(zfdatfile.read()))  
    
    # Sort the data in ascending order by time. This defines a call back 
    # function using lambda which takes input k and produces output k['time']
    data = sorted(data, key=lambda d: d['time']) 
    
    # Close the zip file
    zf.close()
    
    return data

#-----------------------------------------------------------------------------
# Restructure power data to be in a form that's more easily accessible for 
# for further processing
#-----------------------------------------------------------------------------
def restructure(data):    
    # Time of measurement 
    data_time=[i['time'] for i in data] 
    
    # Power plant info data structure data for each time measurement period
    data_info=[i['info'] for i in data] 

    # Initialize an empty Data frame for output.
    data_cols=['time','type','used','capacity']
    data=pandas.DataFrame(data=None, columns = data_cols)

    # Now iterate through for each time (grab the index and data at index 
    # using the enumerate function
    for t, tdata in enumerate(data_info):
        # Create an duplicate array for time that is as long as the data for
        # time t.
        data_time_t=[data_time[t]]*len(tdata)
        
        # Grab the type info for all power plants at time t
        data_info_t_type=[i['type'] for i in tdata]
    
        # Grab the generated and capacity power for all plants at a given time 
        data_info_t_Pgen=[i['used'] for i in tdata]
        data_info_t_Pcap=[i['capacity'] for i in tdata]
    
        # Create a data frame to store the {time, type, used, capacity} 
        # variables directly
        data_buf = [data_time_t, data_info_t_type, data_info_t_Pgen, data_info_t_Pcap]
        data_buf = pandas.DataFrame(data_buf).T
        data_buf.columns=data_cols
        
        # Append the current data frame rows to the existing data frame
        # used for storing results. 
        data= pandas.concat([data, data_buf], axis=0, ignore_index=True)
    
    return data

#-----------------------------------------------------------------------------
# Aggregate the data and do some computations and calculations on it to extract
# interesting power related information about the grid.
#-----------------------------------------------------------------------------
def calculate(data, plant_type): 
    # Setup an empty dataframe for storing the regrouped values from the data
    # extracted so far
    pd_cols=['time','type','Pgen','Pcap']
    pd = pandas.DataFrame([],columns=pd_cols)

    data_time = list(set(data['time']))

    # Grab the unique types of plant indices
    pt_=sorted(list(set(data['type'])))
    pt = sorted(list(set(data['type']).intersection(plant_type)))
    if pt==[]:
        pt = pt_
    
    # Iterate through all unique times and sum the data for total generation
    # capacity and actual total generation amount
    for t in data_time:
        # Search for all power plants with the same time 
        ps=data.loc[((t==data['time']) & (data['type'].isin(pt))).tolist()]
        
        # Build a buffer for storing the summed generation for all power plants
        # generating at the same time
        pb = [t, pt, sum(ps['used']), sum(ps['capacity'])]
        pb = pandas.DataFrame(pb).T
        pb.columns = pd_cols
        
        # Store and append the sum for a the given time t into a dataframe
        pd = pandas.concat([pd, pb], axis=0, ignore_index=True)

    # Return the relevant data records
    return pd

#-----------------------------------------------------------------------------
# Visualization function for doing some interesting visualizations
#-----------------------------------------------------------------------------
def visualize(data):
    plt.style.use('seaborn-whitegrid')
    x = np.linspace(0, 10, 1000)
    plt.plot(data.index, data['Pgen'])       
    plt.axis('tight');
    plt.title("The Total Power Generated and Total Capacity Available")
    plt.xlabel("Time [days]")
    plt.ylabel("Total Power [MW]");
    plt.legend();
    return data
    
#-----------------------------------------------------------------------------
# Main Function for analyzing power data
#-----------------------------------------------------------------------------
def main(filename, time_range, plant_type):
    # Grab the data from the zip file for the time range
    data=extract(filename, time_range)
    
    # Restructure the data for improved searchability
    data=restructure(data)

    # Do some additional restructuring and calculations to extract useful
    # power systems related information from the initial data set.
    data = calculate(data, plant_type)
    
    # Visualize the data in some meaningful way
    data = visualize(data)
    
    return data

#-----------------------------------------------------------------------------
# Main 
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    # Data source filenames
    pow_filename = os.path.join( "./","power-data.zip")
    #pow_filename = os.path.join( "G:/", "My Drive", "AFC Project", "Historical Data","Sources", "Taipower", "power data.zip")

    # Extract just relevant file names from the list
    pdata = main(pow_filename, ["2019-03-20-00:00:00", "2019-03-22-00:10:00"], [])




