#import{
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import time
from plotly.offline import plot
import os
#}import

def main():
    start = time.time()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'DATA.csv')

    #reading the csv measurement file
    data = pd.read_csv(file_path, header = None)

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

    THETA = THETA.reshape(s_power.shape[0],s_power.shape[1])
    PHI = PHI.reshape(s_power.shape[0],s_power.shape[1])
    R = R.reshape(s_power.shape[0],s_power.shape[1])

    sin_theta = np.sin(THETA)
    cos_phi = np.cos(PHI)
    cos_theta = np.cos(THETA)
    sin_phi = np.sin(PHI)

    X = np.asarray(R * sin_theta * cos_phi)
    Y = np.asarray(R * sin_theta * sin_phi)
    Z = np.asarray(R * cos_theta)

    if np.any(sin_theta * cos_phi> 1):
        print("sin math invalid")

#main{
if __name__ == "__main__":
    main()
#}main
