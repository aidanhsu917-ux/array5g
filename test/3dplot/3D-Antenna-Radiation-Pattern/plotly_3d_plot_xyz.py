# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 13:10:38 2019

@author: slaxman
"""
#import{
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import time
from plotly.offline import plot
#}import

#modules{
def main():
    start = time.time()

    #reading the csv measurement file
    data = pd.read_csv('DATA.csv', header = None)

    phi = np.asarray(data.iloc[1:,0])
    theta = np.asarray(data.iloc[0,1:])
    s_power = np.asarray(data.iloc[1:,1:])

    s_power = 10**(s_power/10)#converting from db to watt

    #converting from spherical to cartesian coords
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

    X = R * np.sin(THETA) * np.cos(PHI)
    Y = R * np.sin(THETA) * np.sin(PHI)
    Z = R * np.cos(THETA) 

    print(X.ravel()) #has negative values- how?

    #setup layout and plot on 3d surface
    #axis ranges do not match input values
    #ex: np.min(X) is -16, 0 least shown on graph
    #layout = go.Layout(title = "3D Radiation Pattern of 5G CW data", xaxis = dict(nticks = s_power.shape[0], range=[np.min(X),np.max(X)]), yaxis = dict(nticks = s_power.shape[1], range=[np.min(Y),np.max(Y)]))
    fig = go.Figure(data=[go.Mesh3d(x=X.ravel(), y=Y.ravel(), z=Z.ravel(), intensity = R, colorscale='jet', colorbar = dict(title = "Gain", thickness = 50, xpad = 500))])
    fig.update_layout(autosize = True, scene = dict(xaxis = dict(nticks = 10, range=[np.min(X),np.max(X)]), yaxis = dict(nticks = 10, range=[np.min(Y),np.max(Y)]), zaxis = dict(nticks = 10, range = [np.min(Z), np.max(Z)])), margin = dict(l = 50, r = 50, t = 250, b = 250))
    fig.show()
    print("Time elapsed: ",time.time() - start, " seconds")
#}modules

#main{
if __name__ == "__main__":
    main()
#}main
