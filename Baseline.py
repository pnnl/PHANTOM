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

import random
import numpy as np
import scipy.spatial
from scipy.spatial import distance_matrix

class Baseline:
    def __init__(self):
        self.vecs = []
        self.var = None
        self.DMatrix = None

    ###############################################################################
    #
    ###############################################################################
    def Initialize(self, vectorized_data, rows_in_baseline, baseline_probability):
        print("*** INITIALIZE BASELINE ***")
        i = 0
        j = 0

        while(j < rows_in_baseline and i < len(vectorized_data)):
            if (random.random() < baseline_probability):
                self.vecs.append(vectorized_data[i])
                j = j + 1
            i = i + 1
            
        print("baselineVecs:")
        for vec in self.vecs:
            print(vec)

    ###############################################################################
    # Compute()
    # Computes the initial baseline that the anomaly detection is based off. 
    ###############################################################################
    def Compute(self):
        #print("*** COMPUTE BASELINE ***")
        # standard deviation of each variable of 

        baselineVecsNP = np.asarray(self.vecs, dtype = float)
        self.var = np.var(baselineVecsNP, axis = 0, ddof = 1)
        
        for i in range(len(self.var)):
            if self.var[i] == 0.0:
                self.var[i] = 1.0 #np.finfo(float).eps
                
        # distance matrix for vectors
        self.DMatrix = scipy.spatial.distance.squareform(scipy.spatial.distance.pdist(baselineVecsNP, "seuclidean", V = self.var))
        
        #print("baseVar: {0}".format(self.var))
        #print("baseDMatrix: {0}".format(self.DMatrix))
        #print("")