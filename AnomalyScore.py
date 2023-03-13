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

import persim
import numpy as np

#####
# 
#####
def compare(barcode, baseBarcode, method = 0):
    val = 0

    # remove points with non-finite death times
    # i = 0
    # badPairs = []
    # for pair in barcode:
    #     if np.isinf(pair[0]) or np.isinf(pair[1]):
    #         badPairs.append(i)
    #     i = i + 1
    # for index in badPairs:
    #     barcode = np.delete(barcode, index)

    # i = 0
    # badPairs = []
    # for pair in baseBarcode:
    #     if np.isinf(pair[0]) or np.isinf(pair[1]):
    #         badPairs.append(i)
    #     i = i + 1
    # for index in badPairs:
    #     baseBarcode = np.delete(baseBarcode, index)

    if (method == 0):
        val = persim.bottleneck(barcode, baseBarcode)
    elif(method == 1):
        val = persim.sliced_wasserstein(barcode, baseBarcode)
    elif(method == 2):
        val = persim.wasserstein(barcode, baseBarcode)

    return val
