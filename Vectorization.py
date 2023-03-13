#########################################################################################
# Notice: This computer software was prepared by Battelle Memorial Institute, 
# hereinafter the Contractor, under Contract No. DE-AC05-76RL01830 with the 
# Department of Energy (DOE).  All rights in the computer software are reserved 
# by DOE on behalf of the United States Government and the Contractor as provided 
# in the Contract.  You are authorized to use this computer software for 
# Governmental purposes but it is not to be released or distributed to the public.  
# NEITHER THE GOVERNMENT NOR THE CONTRACTOR MAKES ANY WARRANTY, EXPRESS OR IMPLIED, 
# OR ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  This notice including 
# this sentence must appear on any copies of this computer software.
#########################################################################################

import json
from datetime import datetime
import statistics
from scipy import stats

##################################################
# convert time into epoch (seconds)
##################################################
def ConvertTime(original_time, time_format):
    timeEpoch = 0

    if time_format == "epoch":
        timeEpoch = int(original_time)

    elif time_format == "iso":
        dateTimeISO = datetime.fromisoformat(original_time)
        timeEpoch = dateTimeISO.timestamp()

    # yyyy-MM-dd HH:mm:ss variation
    else:
        dateTimeObject = datetime.strptime(original_time, time_format)
        timeEpoch = dateTimeObject.timestamp()

    return timeEpoch

##################################################
# Builds headers for vector based on the specified config file
##################################################
def VectorHeaders(vector_config_file_name):
    headers = []
    fr = open(vector_config_file_name, "r")
    data_vectorization = json.loads(fr.read())
    fr.close()

    # iterate through vector columns defined in the config
    for header_name,header_dict in data_vectorization["VECTOR"].items():
        
        # dynamic header name creation (only for count_values as of now)
        if header_dict["strategy"] == "count_values":
            for value in header_dict["values"]:
                headers.append("{0}_{1}".format(header_name,value))
            if "include_other" in header_dict and header_dict["include_other"]:
                headers.append("{0}_{1}".format(header_name,"phantom_other"))

        # static header name, simply take from config
        else:
            headers.append(header_name)

    headers = sorted(headers)

    print("VecotrHeaders: {0}".format(headers))

    return headers

##################################################
# Main loop that builds the vectorized data using a specified strategy
##################################################
def Vectorize(data, vector_config_file_name, time_field_name, time_format, window_length_seconds, overlap_seconds):
    print("*** VECTORIZE ***")
    vectorized_data = []

    # loop through entire data set
    i = 0
    while(i < len(data)):
        first_row_time = data[i][time_field_name]
        first_row_time = ConvertTime(first_row_time, time_format)
        last_row_time = first_row_time + window_length_seconds
        #print("window start: {0}, window end: {1}".format(first_row_time, last_row_time))

        # build window of raw data
        window_data = []
        j = i
        row = data[j]
        while (ConvertTime(row[time_field_name], time_format) < last_row_time):
            window_data.append(row)
            j = j + 1
            try:
                row = data[j]
            except:
                # end reached
                i = len(data)
                break

        # build vector using a strategy - separate function
        vector = []
        vector = BuildVector(window_data, vector_config_file_name)

        # add vectorized window to list
        vectorized_data.append(vector)

        # find start of next window based on overlap
        if (i < len(data)):
            nextfirst_row_time = first_row_time + overlap_seconds
            row = data[i]
            while (ConvertTime(row[time_field_name], time_format) < nextfirst_row_time):
                try:
                    row = data[i+1]
                    i = i + 1
                except:
                    break
    
    #print("")
    print("vectorized_data:")
    i = 0
    for vector in vectorized_data:
        print("{0}:\t{1}".format(i, vector))
        i = i + 1
    print("vector count: {0}".format(len(vectorized_data)))
    print("")

    return vectorized_data


##################################################
# vectorization strategy that follows rules set in a config
# can combine multiple strategies to form one vector
##################################################
def BuildVector(window_data, vector_config_file_name):
    
    fr = open(vector_config_file_name, "r")
    data_vectorization = json.loads(fr.read())
    fr.close()

    vector_dictionary = {}

    # iterate over every column in the config file
    for header_name,header_dict in data_vectorization["VECTOR"].items():
        
        ##############################
        # handle each strategy
        ##############################

        # count_unique
        if header_dict["strategy"] == "count_unique":
            # prep set of unique values
            unique_values = set()
            for row in window_data:
                if header_dict["field"] in row:
                    unique_values.add(row[header_dict["field"]])
            vector_dictionary[header_name] = len(unique_values)

        # count_values
        if header_dict["strategy"] == "count_values":
            # prep counts at 0
            for value in header_dict["values"]:
                vector_dictionary["{0}_{1}".format(header_name,value)] = 0
            if "include_other" in header_dict and header_dict["include_other"]:
                vector_dictionary["{0}_phantom_other".format(header_name)] = 0

            # fill counts
            for row in window_data:
                if header_dict["field"] in row:
                    if row[header_dict["field"]] in header_dict["values"]:
                        vector_dictionary["{0}_{1}".format(header_name,row[header_dict["field"]])] = vector_dictionary["{0}_{1}".format(header_name,row[header_dict["field"]])] + 1
                    elif "include_other" in header_dict and header_dict["include_other"]:
                        vector_dictionary["{0}_phantom_other".format(header_name)] = vector_dictionary["{0}_phantom_other".format(header_name)] + 1

        # min_value
        if header_dict["strategy"] == "min_value":
            vector_dictionary[header_name] = None
            # find the min
            for row in window_data:
                if header_dict["field"] in row:
                    if vector_dictionary[header_name] == None:
                        vector_dictionary[header_name] = float(row[header_dict["field"]])
                    if float(row[header_dict["field"]]) < float(vector_dictionary[header_name]):
                        vector_dictionary[header_name] = float(row[header_dict["field"]])
            
            # default to 0
            if vector_dictionary[header_name] == None:
                vector_dictionary[header_name] = 0

        # max_value
        if header_dict["strategy"] == "max_value":
            vector_dictionary[header_name] = None
            # find the max
            for row in window_data:
                if header_dict["field"] in row:
                    if vector_dictionary[header_name] == None:
                        vector_dictionary[header_name] = float(row[header_dict["field"]])
                    if float(row[header_dict["field"]]) > float(vector_dictionary[header_name]):
                        vector_dictionary[header_name] = float(row[header_dict["field"]])
            
            # default to 0
            if vector_dictionary[header_name] == None:
                vector_dictionary[header_name] = 0

        # mean_values
        if header_dict["strategy"] == "mean_values":
            value_list = []

            for row in window_data:
                if header_dict["field"] in row:
                    value_list.append(float(row[header_dict["field"]]))

            vector_dictionary[header_name] = statistics.mean(value_list)

        # median_values
        if header_dict["strategy"] == "median_values":
            value_list = []

            for row in window_data:
                if header_dict["field"] in row:
                    value_list.append(float(row[header_dict["field"]]))

            vector_dictionary[header_name] = statistics.median(value_list)

        # mode_values
        if header_dict["strategy"] == "mode_values":
            value_list = []

            for row in window_data:
                if header_dict["field"] in row:
                    value_list.append(float(row[header_dict["field"]]))

            vector_dictionary[header_name] = stats.mode(value_list)[0][0]

        # sum_values
        if header_dict["strategy"] == "sum_values":
            vector_dictionary[header_name] = 0
                        
            for row in window_data:
                if header_dict["field"] in row:
                    vector_dictionary[header_name] = vector_dictionary[header_name] + float(row[header_dict["field"]])

        # count_grouping
        if header_dict["strategy"] == "count_grouping":
            vector_dictionary[header_name] = 0

            for row in window_data:
                matches_found = 0
                matches_needed = len(header_dict["fields"].keys())
                for search_field, search_values in header_dict["fields"].items():
                    if search_field in row:
                        if row[search_field] in search_values:
                            matches_found = matches_found + 1
                            # continue to next search_field, do not double count
                            continue
                
                # all matched
                if matches_found == matches_needed:
                    vector_dictionary[header_name] = vector_dictionary[header_name] + 1


    # convert to vector
    vector = []
    for fieldKey in sorted(vector_dictionary.keys()):
        #for valKey in sorted(vector_dictionary[fieldKey].keys()):
            # vector.append(vector_dictionary[fieldKey][valKey])
        vector.append(vector_dictionary[fieldKey])
    
    return vector