#import{
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import time
from plotly.offline import plot
#}import

def main():
    start = time.time()

    #reading the csv measurement file
    data = pd.read_csv('DATA.csv', header = None)

    phi = np.asarray(data.iloc[1:,0])
    theta = np.asarray(data.iloc[0,1:])
    s_power = np.asarray(data.iloc[1:,1:])

    s_power = 10**(s_power/10)

    X, Y, Z, THETA, PHI, R = [[] for _ in range(6)]

    for p in range(0, len(phi)):
        for t in range(0, len(theta)):
            PHI.append(float(phi[p])) #append all values as floats to an empty list
            THETA.append(float(theta[t]))
            R.append(float(s_power[p,t]))

    THETA = np.deg2rad(np.asarray(THETA))
    PHI = np.deg2rad(np.asarray(PHI))
    R = np.asarray(R)

    print(THETA.shape)

#main{
if __name__ == "__main__":
    main()
#}main
