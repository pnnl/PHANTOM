# PHANTOM

## Disclaimer
This material was prepared as an account of work sponsored by an agency of the United States Government.  Neither the United States Government nor the United States Department of Energy, nor Battelle, nor any of their employees, nor any jurisdiction or organization that has cooperated in the development of these materials, makes any warranty, express or implied, or assumes any legal liability or responsibility for the accuracy, completeness, or usefulness or any information, apparatus, product, software, or process disclosed, or represents that its use would not infringe privately owned rights.  
Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer, or otherwise does not necessarily constitute or imply its endorsement, recommendation, or favoring by the United States Government or any agency thereof, or Battelle Memorial Institute. The views and opinions of authors expressed herein do not necessarily state or reflect those of the United States Government or any agency thereof.  
  
<p style="text-align: center;">PACIFIC NORTHWEST NATIONAL LABORATORY</p>  
<p style="text-align: center;">operated by</p>  
<p style="text-align: center;">BATTELLE</p>  
<p style="text-align: center;">for the</p>  
<p style="text-align: center;">UNITED STATES DEPARTMENT OF ENERGY</p>  
<p style="text-align: center;">under Contract DE-AC05-76RL01830</p>  
  
## BSD
Copyright 2022 Battelle Memorial Institute  
  
Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:  
1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.  
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.  
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  

## What Is PHANTOM? And what does it do?
PHANTOM stands for "Persistent Homology Anomalous Tracking Observation Monitor." The PHANTOM application uses topological structure of vector data derived from temporal log data to discover how similar new data is to an evolving baseline set

## High Level Steps
1. Gather data from some source (or generate random sample set) - CSV or JSON with required "time" field for each row/entry
2. Partition data into time intervals
3. Create vectors for each partitioned set of data
4. Build a baseline from multiple initial vectors
5. Calculate how much adding a single vector of new data (corresponding to a new time window) would change the topology of the collection of baseline vectors
	* If the change is not found significant (the new data is not anomalous compared to the baseline) update the baseline to include the current vector
	* If the change is found significant, do not update the baseline to include the anomalous data
7. Record anomaly score for the new window. Return to step 5.

# Running PHANTOM
## Prerequisites
1. Python3  
	* version 3.7  
2. Python3 packages:  
	* numpy  
	* scipy  
	* ripser  
	* persim  
	* matplotlib  

## Installation
1. Install Python 3.7  
2. Enter root directory  
3. Run install.sh (this will install the appropriate prerequisite packages, no need to run this if you have already installed the packages listed above)
```sh util/setup/install.sh```

## Execution
Before running the following steps you will need to have data in the right format and created appropriate `config.json` and vectorization config files. See **Data** and **Configuration** sections below. Once those are set, complete the following steps to execute PHANTOM on your data.

1. Enter root directory  
2. Run PHANTOM  
```python main.py```  
results and debug logs will display to console  
```python -W ignore main.py```  
hides warning messages (recommended for now)  

## Viewing Results
View `results.txt` and `Anomaly_Plot.png` files for results. 

# Data

## Providing your own raw data
If you do not have raw data to test on, see the **Generating data** subsection below to generate simple test data for PHANTOM.  

Raw data needs to be provided in a file in PHANTOM's root directory in either JSON or CSV format.  

If providing JSON-formatted data, the exact format must be a list of dictionaries, each dictionary being a single entry of data with at least a timestamp field. The timestamp field name and timestamp format must be set in the configuration file, see the **Configuration** section below. These examples use the epoch format.

JSON Example:  
```
[  
{"timestamp": 1640390400, "field_01": "value_01", "field_02": "value_02"},  
{"timestamp": 1640390410, "field_01": "value_03", "field_02": "value_04"},  
{"timestamp": 1640390420, "field_01": "value_05", "field_02": "value_06"},  
... 
]
```  

CSV Example:  
```
timestamp,field_01,field_02  
1640390400,value_01,value_02  
1640390410,value_03,value_04  
1640390420,value_05,value_06  
...
```  

## Generating data
The main purpose of the data generation feature is to help validate that the PHANTOM application can run in an environment. This should not be considered as realistic data. To start, first update `data_template.json`. Edit this file to configure how many fields of data are generated, the values each field can be, and the odds of each value. The data generation algorithm also uses two fields in `config.json`: **BASELINE_LENGTH_SECONDS** (to make sure that length of data does not contain any anomalies), and **TOTAL_RECORDS** (to know how many records to generate). Make sure these two fields are filled in before running `generateRaw.py`.

For each `field:value` pair of data being generated, a random number is generated from 0.0 to 1.0. If the random number is less than or equal to the decimal in the "odds" array, the corresponding "value" will be used to populate the field, otherwise it will check against the next decimal in "odds", and so on.  

Example:  
```
...  
{  
    "field": "username",  
    "odds": [0.33333, 0.66666, 0.99999, 1.0],  
    "values": ["alice", "bob", "cathy", "hacker"]  
},  
...
```  
For the field "username", there is a ~33.333% chance of the generated value being "alice", "bob" and "cathy", but a 0.001% chance of the generated value being "hacker". Theoretically, the PHANTOM app would deem vectors including data with the "hacker" username to be anomalous, given the low chances of that username appearing throughout the entire dataset (and baseline).  

Once you have set up `data_template.json` run the following steps to create your data

1. Enter root directory  
2. Generate raw data  
```python generateRaw.py```  

This will create raw.csv and raw.json in the root directory.

# Vectorization
The `Vectorization.py` file is where raw data is broken down into separate windows (based on the timing configuration settings) and converted into vectorized data. How each window of raw data is converted into a vectorized form is determined by the contents of the vector config file (set by **VECTOR_CONFIG_FILE_NAME** in `config.json`, see details in **Configuration** below).  

The raw data being sent to the `Vectorize()` function is expected to be in the format of a chronological list object, where each element in the list is a dictionary object containing key/value pairs for the data from a single timestamp, including a key/value pair for the timestamp itself. The `Vectorize()` method will build windows based on the timestamp field in each dictionary object, which can be configured in the `config.json` file.  

The `BuildVector()` function will refer to the vector config file to determine how to build each individual column in the vector. There are a variety of vectorization strategies that can be used to build each column. See details in the **Vector Config File** section below.  

## Adding options to the vectorization strategies
Additional vectorization strategies can be implemented within the `Vectorization.py` file by doing the following:  
1. In the `Vectorization.py` file, find the `BuildVector()` function. This is where each window of data is converted into a vector format. The main loop in this function iterates over each vector column defined in the vector config file and creates each column one at a time.  
2. To add a new strategy, add an "if" statement to the block to handle the name of your new strategy. Within that if statement, you will have access to the entire window of data to build the specific column however is necessary.  
3. Update the contents of the vector config file to include your new strategy in a column definition.  

# Configuration
There are two configuration files that need to be created in order to execute PHANTOM's main.py. The first is the overall configuration (`config.json`) including identifying the correct data file, setting window and baseline time lengths, anomaly score threshold, and more. The second is the vectorization configuration. This can be any filename, and that filename must be specified in `config.json`.

## config.json
The following fields must be set:

* **WINDOW_LENGTH_SECONDS**  
Length of time in seconds (integer).  
This controls how much data to include in each window/vector when building the vectorized data.  
  
* **OVERLAP_SECONDS**  
Length of time in seconds (integer).  
This controls length of time between the start of one window to the start of the next.  
  
* **BASELINE_LENGTH_SECONDS**  
Length of time in seconds (integer).  
Must be greater than WINDOW_LENGTH_SECONDS.  
This controls how much of the input data will be used to generate the initial baseline.  
  
* **BASELINE_PROBABILITY**  
Decimal from 0.0 to 1.0.  
This determines the probability for each vectorized window of data, starting from the first up until the baseline length in seconds is reached, to be included in the initial baseline.  
  
* **ANOMALY_THRESHOLD**  
Decimal value.  
The rolling baseline will be updated with vectors that have anomaly scores lower than ANOMALY_THRESHOLD.
  
* **VECTOR_CONFIG_FILE_NAME**  
Name of the config file that defines the vectorization strategy that will be used in `Vectorize.py`.  
  
* **RAW_DATA_FILE_NAME**  
File name for the raw data to be read in. Raw data file must be in root directory.  
  
* **RAW_DATA_FORMAT**  
The format of the raw data. "json" or "csv" are currently implemented options.  
  
* **TIME_FIELD_NAME**  
Field name in the raw data that contains the timestamp.  
  
* **TIME_FORMAT**  
The format of timestamps found in the raw data. "epoch" or "iso" are currently implemented options. If your timestamp format is different than epoch or iso, you may provide the formatting in a "%d %B %Y" style or similar fashion. Refer to [Python strftime cheatsheet](https://strftime.org/). The Python code will attempt to parse the timestamp field best it can.  
  
* **TOTAL_RECORDS**  
Total number of records to include in generated data (integer).  
  
## Vector Config File
The Vector Config File (set in the **VECTOR_CONFIG_FILE_NAME** field in `config.json`) is used to define how vectors will be created from each window of data. The config file must be in json format that contains a "VECTOR" block. The "VECTOR" block will define each vector column individually, the key being the column name and the value being the dictionary definition. The dictionary definition must include a "strategy" key, which will need to match the "if" block in the `BuildVector()` function in `Vectorization.py` (see the **Adding options to the vectorization strategies** section above). The "strategy" will determine the other keys necessary within the dictionary definition. Most also include a "field" key. Refer to the **Currently Implemented Strategies** section below and the `BuildVector()` function to see how each column is handled for examples.  
  
### Currently Implemented Vectorization Strategies
* **count_unique**  
Count the number of unique values of a field within a window.  
```
...  
{  
    "strategy": "count_unique",  
    "field": "<field name found in raw data>"  
}  
...
```  
* **count_values**  
Count the occurrences of each specified value of a field within a window. Can be configured to include counts of all other values not specified. This strategy will produce as many columns in the vectorization as values being counted (plus one if `include_other=true`).  
```
...  
{  
    "strategy": "count_values",  
    "field": "<field name found in raw data>",  
    "values": [<exact value to count>, <exact value to count>, ...],  
    "include_other": <true/false>  
}  
...
```  
* **min_value**  
The minimum value of a field found within a window.  
```
...  
{  
    "strategy": "min_value",  
    "field": "<field name found in raw data>"  
}  
...
```  
* **max_value**  
The maximum value of a field found within a window.  
```
...  
{  
    "strategy": "max_value",  
    "field": "<field name found in raw data>"  
}  
...
```  
* **mean_values**  
The mean of values of a field within a window.  
```
...  
{  
    "strategy": "mean_values",  
    "field": "<field name found in raw data>"  
}  
...
```  
* **median_values**  
The median of values of a field within a window.  
```
...  
{  
    "strategy": "median_values",  
    "field": "<field name found in raw data>"  
}  
...
```  
* **mode_values**  
The mode of values of a field within a window.  
```
...  
{  
    "strategy": "mode_values",  
    "field": "<field name found in raw data>"  
}  
...
```  
* **sum_values**  
The sum of values of a field within a window.  
```
...  
{  
    "strategy": "sum_values",  
    "field": "<field name found in raw data>"  
}  
...
```  
* **count_grouping**  
Count the occurrences of specified values of fields being found in the same record together within a window. Each field specified is treated as an "AND", values within each field are treated as an "OR".  
```
...  
{  
    "strategy": "count_grouping",  
    "fields": {  
        "<field name>": ["<exact value to match>", "<exact value to match>, ..."],  
        "<field name>": ["<exact value to match>, ..."],  
        ...  
    }  
}  
...
```  
  
# **Notice**  
This computer software was prepared by Battelle Memorial Institute, hereinafter the Contractor, under Contract No. DE-AC05-76RL01830 with the Department of Energy (DOE).  All rights in the computer software are reserved by DOE on behalf of the United States Government and the Contractor as provided in the Contract.  You are authorized to use this computer software for Governmental purposes but it is not to be released or distributed to the public.  NEITHER THE GOVERNMENT NOR THE CONTRACTOR MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  This notice including this sentence must appear on any copies of this computer software.