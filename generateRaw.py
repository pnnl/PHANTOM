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

import sys
import random
import json

increment_seconds = 1
startTime = 1640390400 # xmas 2021

try:
    fr = open("data_template.json", "r")
    data_generation_list = json.loads(fr.read())
    fr.close()
except Exception as e:
    print("ERROR reading data_template.json: {0}".format(e))
    sys.exit()

# read config file
try:
    fr = open("config.json", "r")
    config = json.loads(fr.read())
    fr.close()
except Exception as e:
    print("ERROR reading config.json: {0}".format(e))
    sys.exit()
totalRecords = config["TOTAL_RECORDS"]
baselineLength = config["BASELINE_LENGTH_SECONDS"]

rawDictionary = []

i = 0
time = startTime

fw = open("raw.csv", "w+")
fw.write(config["TIME_FIELD_NAME"])
for data_dictionary in data_generation_list:
    fw.write(",{0}".format(data_dictionary["field"]))
fw.write("\n")

while i < totalRecords:

    new_data = {}
    fw.write("{0}".format(time))
    new_data[config["TIME_FIELD_NAME"]] = time
    
    for data_dictionary in data_generation_list:
        roll = random.random()
        
        # clean baseline with no anomalies
        if i < baselineLength:
            roll = roll - 0.001

        index = 0
        for decimal in data_dictionary["odds"]:
            if roll <= decimal:
                break
            index = index + 1
        
        fw.write(",{0}".format(data_dictionary["values"][index]))
        new_data[data_dictionary["field"]] = data_dictionary["values"][index]
    
    fw.write("\n")
    rawDictionary.append(new_data)

    time = time + increment_seconds
    i = i + 1

fw.close()

fw = open("raw.json", "w+")
fw.write(json.dumps(rawDictionary))
fw.close()