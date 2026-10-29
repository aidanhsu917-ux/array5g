# -*- coding: utf-8 -*-
################################################
##
## Adapted from REctPatch.py hosted on Github
##     https://gist.github.com/johngrantuk/73e0742fac6a6a17e7b42ae34cfde56e
##
## 2021, Feb 14
##
##
################################################

import math
import matplotlib.pyplot as plt
import numpy as np
from math import cos, sin, sqrt, atan2, acos
import pyvista as pv
    

##################################################
### utility functions
##################################################

def sph2cart1(r, th, phi):
  x = r * cos(phi) * sin(th)
  y = r * sin(phi) * sin(th)
  z = r * cos(th)

  return x, y, z
  
def cart2sph1(x, y, z):
  r = sqrt(x**2 + y**2 + z**2) + 1e-15
  th = acos(z / r)
  phi = atan2(y, x)

  return r, th, phi


##################################################
### function to predict the field strength in a given direction
##################################################

def PatchFunction(thetaInDeg, phiInDeg, Freq, W, L, h, Er):
    """
    Taken from Design_patchr
    Calculates total E-field pattern for patch as a function of theta and phi
    Patch is assumed to be resonating in the (TMx 010) mode.
    E-field is parallel to x-axis
    W......Width of patch (m)
    L......Length of patch (m)
    h......Substrate thickness (m)
    Er.....Dielectric constant of substrate
    Refrence C.A. Balanis 2nd Edition Page 745
    """
    lamba = 3e8 / Freq

    theta_in = math.radians(thetaInDeg)
    phi_in = math.radians(phiInDeg)

    ko = 2 * math.pi / lamba

    xff, yff, zff = sph2cart1(999, theta_in, phi_in)                            # Rotate coords 90 deg about x-axis to match array_utils coord system with coord system used in the model.
    xffd = zff
    yffd = xff
    zffd = yff
    r, thp, php = cart2sph1(xffd, yffd, zffd)
    phi = php
    theta = thp

    if theta == 0:
        theta = 1e-9                                                              # Trap potential division by zero warning

    if phi == 0:
        phi = 1e-9

    Ereff = ((Er + 1) / 2) + ((Er - 1) / 2) * (1 + 12 * (h / W)) ** -0.5        # Calculate effictive dielectric constant for microstrip line of width W on dielectric material of constant Er

    F1 = (Ereff + 0.3) * (W / h + 0.264)                                        # Calculate increase length dL of patch length L due to fringing fields at each end, giving total effective length Leff = L + 2*dL
    F2 = (Ereff - 0.258) * (W / h + 0.8)
    dL = h * 0.412 * (F1 / F2)

    Leff = L + 2 * dL

    Weff = W                                                                    # Calculate effective width Weff for patch, uses standard Er value.
    heff = h * sqrt(Er)

    # Patch pattern function of theta and phi, note the theta and phi for the function are defined differently to theta_in and phi_in
    Numtr2 = sin(ko * heff * cos(phi) / 2)
    Demtr2 = (ko * heff * cos(phi)) / 2
    Fphi = (Numtr2 / Demtr2) * cos((ko * Leff / 2) * sin(phi))

    Numtr1 = sin((ko * heff / 2) * sin(theta))
    Demtr1 = ((ko * heff / 2) * sin(theta))
    Numtr1a = sin((ko * Weff / 2) * cos(theta))
    Demtr1a = ((ko * Weff / 2) * cos(theta))
    Ftheta = ((Numtr1 * Numtr1a) / (Demtr1 * Demtr1a)) * sin(theta)

    # Due to groundplane, function is only valid for theta values :   0 < theta < 90   for all phi
    # Modify pattern for theta values close to 90 to give smooth roll-off, standard model truncates H-plane at theta=90.
    # PatEdgeSF has value=1 except at theta close to 90 where it drops (proportional to 1/x^2) to 0

    rolloff_factor = 0.5                                                       # 1=sharp, 0=softer
    theta_in_deg = theta_in * 180 / math.pi                                          # theta_in in Deg
    F1 = 1 / (((rolloff_factor * (abs(theta_in_deg) - 90)) ** 2) + 0.001)       # intermediate calc
    PatEdgeSF = 1 / (F1 + 1)                                                    # Pattern scaling factor

    UNF = 1.0006                                                                # Unity normalisation factor for element pattern

    if theta_in <= math.pi / 2:
        Etot = Ftheta * Fphi * PatEdgeSF * UNF                                   # Total pattern by pattern multiplication
    else:
        Etot = 0

    return Etot

##################################################
### calculates the field over phi and theta in polar coordinates
##################################################

def GetPatchFields(PhiStart, PhiStop, ThetaStart, ThetaStop, Freq, W, L, h, Er):
    """"
    Calculates the E-field for range of thetaStart-thetaStop and phiStart-phiStop
    Returning a numpy array of form - fields[phiDeg][thetaDeg] = eField
    W......Width of patch (m)
    L......Length of patch (m)
    h......Substrate thickness (m)
    Er.....Dielectric constant of substrate
    """
    fields = np.ones((PhiStop, ThetaStop))                                      # Create initial array to hold e-fields for each position

    for phiDeg in range(PhiStart, PhiStop):
            for thetaDeg in range(ThetaStart, ThetaStop):                       # Iterate over all Phi/Theta combinations
                eField = PatchFunction(thetaDeg, phiDeg, Freq, W, L, h, Er)     # Calculate the field for current Phi, Theta
                fields[phiDeg][thetaDeg] = eField                               # Update array with e-field

    return fields

##################################################
### Plot the field using Matplotlib
##################################################

def SurfacePlot(Fields):
    """Plots 3D surface plot over given theta/phi range in Fields by calculating cartesian coordinate equivalent of spherical form."""

    print("Processing SurfacePlot...")

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    phiSize = Fields.shape[0]                                                                                   # Finds the phi & theta range
    thetaSize = Fields.shape[1]

    X = np.ones((phiSize, thetaSize))                                                                           # Prepare arrays to hold the cartesian coordinate data.
    Y = np.ones((phiSize, thetaSize))
    Z = np.ones((phiSize, thetaSize))

    for phi in range(phiSize):                                                                                  # Iterate over all phi/theta range
        for theta in range(thetaSize):
            e = Fields[phi][theta]

            xe, ye, ze = sph2cart1(e, math.radians(theta), math.radians(phi))                                   # Calculate cartesian coordinates

            X[phi, theta] = xe                                                                                  # Store cartesian coordinates
            Y[phi, theta] = ye
            Z[phi, theta] = ze

    ax.plot_surface(X, Y, Z, color='b')                                                                         # Plot surface
    plt.ylabel('Y')
    plt.xlabel('X')                                                                                             # Plot formatting
    #plt.title("Patch: \nW=" + str(W) + " \nL=" + str(L) +  "\nEr=" + str(Er) + " h=" + str(h) + " \n@" + str(Freq) + "Hz")
    plt.show()
    
##################################################
### Generate the same plot sureface as in Matplot lib and export as a ply file
##################################################
def PlotAndExport(Fields):
    phiSize = Fields.shape[0]                                                                                   # Finds the phi & theta range
    thetaSize = Fields.shape[1]

    X = np.ones((phiSize+1, thetaSize))                                                                           # Prepare arrays to hold the cartesian coordinate data.
    Y = np.ones((phiSize+1, thetaSize))
    Z = np.ones((phiSize+1, thetaSize))

    radii = np.ones((phiSize+1, thetaSize))

    for phi in range(phiSize+1):                                                                                  # Iterate over all phi/theta range
        for theta in range(thetaSize):
            e = fields[phi%phiSize][theta]

            xe, ye, ze = sph2cart1(e, math.radians(theta), math.radians(phi))                                   # Calculate cartesian coordinates

            X[phi, theta] = xe                                                                                  # Store cartesian coordinates
            Y[phi, theta] = ye
            Z[phi, theta] = ze

            radii[phi, theta] = math.sqrt(X[phi, theta]**2 + Y[phi, theta]**2 + Z[phi, theta]**2)

    
    # create a mesh that can be displayed
    mesh = pv.StructuredGrid(X, Y, Z)

    mesh["Field Strength (Radius)"] = radii.ravel(order='F')
    
    # Show the result in a plotter window
    p = pv.Plotter()
    p.add_mesh(mesh, scalars="Field Strength (Radius)", cmap="rainbow4", show_edges=False, smooth_shading=True)
    p.add_axes()
    p.show()
    
    # save the mesh as a ply file, can be saved in many formats
    pv.save_meshio("plot_mesh.ply",mesh)




if __name__ == "__main__":

    # define the patch
    freq = 14e9
    W = 37.77e-3
    L = 11.29e-3
    h = 3e-3
    Er = 2.5

    # calculate the field from the patch antenna design         
    fields = GetPatchFields(0, 360, 0, 90, freq, W, L, h, Er)
    # plot the field using matplotlib
    # SurfacePlot(fields, freq, W, L, h, Er)
    SurfacePlot(fields)

    #Plot and explort using PyVista
    PlotAndExport(fields)