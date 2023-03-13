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

import os
import sys
import json
import csv
import Baseline
import Vectorization
import AnomalyScore

import numpy as np
import scipy.spatial
from scipy.spatial import distance_matrix
import ripser
import matplotlib.pyplot

resultsWriter = None

def printResults(text):
    global resultsWriter
    print(text)
    if resultsWriter is not None:
        resultsWriter.write("{0}\n".format(text))

if __name__ == "__main__":
    print("main() start\n")

    # prep results file
    resultsWriter = open("results.txt", "w+")

    # read config file
    try:
        fr = open("config.json", "r")
        config = json.loads(fr.read())
        fr.close()
    except Exception as e:
        print("ERROR reading config.json: {0}".format(e))
        sys.exit()

    # sanitize config input

    # baseline must be at least 2x multiple of window length
    if config["BASELINE_LENGTH_SECONDS"] < config["WINDOW_LENGTH_SECONDS"]*2:
        config["BASELINE_LENGTH_SECONDS"] = config["WINDOW_LENGTH_SECONDS"]*2
        print("CONFIG ERROR - Baseline length must be at least 2x multiple of window length. Changing BASELINE_LENGTH_SECONDS to: {0}".format(config["BASELINE_LENGTH_SECONDS"]))

    # overlap must be equal to or less than window length
    if config["OVERLAP_SECONDS"] > config["WINDOW_LENGTH_SECONDS"]:
        config["OVERLAP_SECONDS"] = config["WINDOW_LENGTH_SECONDS"]
        print("CONFIG ERROR - Overlap length must be <= window length. Changing OVERLAP_SECONDS to: {0}".format(config["OVERLAP_SECONDS"]))

    # read raw sample data file
    try:
        fr = open(config["RAW_DATA_FILE_NAME"], "r")
        
        data = []
        if config["RAW_DATA_FORMAT"] == "json":
            data = json.loads(fr.read())
        elif config["RAW_DATA_FORMAT"] == "csv":
            csvReader = csv.DictReader(fr)
            for row in csvReader:
                data.append(row)
        else:
            print("CONFIG ERROR - RAW_DATA_FORMAT must be json or csv.")
            sys.exit()
        
        # for debug purposes, print data
        # print(data[:5])

        # fill vector headers
        vector_headers = Vectorization.VectorHeaders(config["VECTOR_CONFIG_FILE_NAME"])

    except Exception as e:
        print("ERROR opening raw data file. Please provide proper raw data or run generateRaw.py script first. {0}".format(e))
        sys.exit()

    # vectorize entire set of sample data, segment into windows
    vectorized_data = Vectorization.Vectorize(data, config["VECTOR_CONFIG_FILE_NAME"], config["TIME_FIELD_NAME"], config["TIME_FORMAT"], config["WINDOW_LENGTH_SECONDS"], config["OVERLAP_SECONDS"])

    # instantiate baseline object
    baseline = Baseline.Baseline()
    rows_in_baseline = int(config["BASELINE_LENGTH_SECONDS"] / config["WINDOW_LENGTH_SECONDS"])
    baseline.Initialize(vectorized_data, rows_in_baseline, config["BASELINE_PROBABILITY"])
    baseline.Compute()
    
    # ripser with dmatrix
    baseBarcode = ripser.ripser(baseline.DMatrix, distance_matrix=True)["dgms"][0]
    #print("baseBarcode:\n{0}".format(baseBarcode))

    # initial distance matrix created from baseline distance matrix
    [nr, nc] = baseline.DMatrix.shape
    DMatrix = np.zeros((nr + 1, nc + 1))
    DMatrix[:nr, :nc] = baseline.DMatrix


    print("")

    Scores = {}
    # skip rows used in initial baseline
    i = rows_in_baseline
    printResults("*** ANOMALY SCORES ***")
    print(sorted(vector_headers))
    printResults("----- Baseline vectors:")
    i = 0
    for vector in baseline.vecs:
        printResults("{0}:\t{1}:\t0.0".format(i, vector))
        i = i + 1
    printResults("----- Vectors (skipped baseline):")

    yData = []

    for vector in vectorized_data[rows_in_baseline:]:
        # generate distance matrix
        vectorNP = np.asarray(vector, dtype = float)
        baselineVecsNP = np.asarray(baseline.vecs, dtype = float)
        Y = scipy.spatial.distance.cdist([vectorNP], baselineVecsNP, metric = 'seuclidean', V = baseline.var)[0]
        DMatrix[nr, :nc] = Y
        DMatrix[:nr, nc] = Y

        # ripser with dmatrix
        barcode = ripser.ripser(DMatrix, distance_matrix=True)["dgms"][0]

        # compare barcode to baseline barcode
        val = AnomalyScore.compare(barcode, baseBarcode, 2)
        Scores["{0}".format(i)] = {}
        Scores["{0}".format(i)]["val"] = val
        yData.append(val)
                
        # update baseline if non-anomalous
        if val < config["ANOMALY_THRESHOLD"] and i >= rows_in_baseline:
            #print("adding vec {0} to baseline".format(i))
            baseline.vecs.pop(0)
            baseline.vecs.append(vector)
            #print("UPDATED baselineVecs:")
            #for vec in baseline.vecs:
            #    print(vec)
        
            baseline.Compute()
            baseBarcode = ripser.ripser(baseline.DMatrix, distance_matrix=True)["dgms"][0]
            DMatrix[:nr, :nc] = baseline.DMatrix
            printResults("{0}:\t{1}:\t{2}".format(i, vector, val))

        # do not update baseline, log anomaly
        elif val >= config["ANOMALY_THRESHOLD"]:
            try:
                closeBase = baselineVecsNP[np.argmin(Y),:]
                compdists = np.sqrt(np.divide(np.square(vectorNP-closeBase),baseline.var))
                topInds = np.argsort(-compdists)[:3]
                topVals = compdists[topInds]

                window_scores = {}
                index = 0
                for topInd in topInds:
                    window_scores[vector_headers[topInd]] = topVals[index]
                    index = index + 1
                Scores["{0}".format(i)]["details"] = window_scores
                printResults("{0}:\t{1}:\t{2}\t{3}".format(i, vector, val, window_scores))
            except Exception as e:
                print("ERR: {0}".format(e))
                printResults("{0}:\t{1}:\t{2}".format(i, vector, val))
        
        # count window
        i = i + 1

    # plot scores
    fig = matplotlib.pyplot.figure(dpi=100)
    # 111
    ax = fig.add_subplot()
    xRange = range(rows_in_baseline, rows_in_baseline + len(vectorized_data[rows_in_baseline:]))
    ax.plot(xRange, yData)
    ax.set_xlabel("Window Number")
    ax.set_ylabel("Anomaly Score")
    matplotlib.pyplot.savefig("Anomaly_Plot.png")

    resultsWriter.close()
    print("")
    print("main() exit")