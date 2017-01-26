#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trajectory model based on Equations of Motion in Chung & Lee (?)
Created on Mon Nov 28 15:50:50 2016

@author: tr1010

Geocentric frame of reference i.e. not actually lat/long but declination and 
right ascenscion. Maybe I should write something which changes between
different frames of reference

"""

import numpy as np
import atmospheres as atmo
import AeroSolvers as Aero

def traj(y, t, sc, J, earth):
    # Extract variables
    r, lat, lon, V, psi, gam, q1, q2, q3, q4, wx, wy, wz = y
    mu, RE, J2, ome = earth
    m, A, Cd = sc
    if r <= earth[1]:
        dydt = np.zeros((13,))
    else:
        # Atmosphere calculation at new altitude
        rho, P, T, mfp, eta, MolW = atmo.US62_76(r)
        
        # Find Cd 
        Kn = mfp/A**0.5
        R = 8314.32/MolW
        RT = R*T
        SoS = (1.4*RT)**0.5
        Ma = V/SoS
        Cd, Ext = Aero.Aero_Calc(geom, Ma, Kn, V, RT, V, psi, gam, q1, q2, q3, q4, wx, wy, wz) # Ext is external torque around the body's centre of mass       
        
        # Drag calculation
        D = 0.5*rho*V**2*A*Cd
        
        # Calculate trig functions
        slat = np.sin(lat)
        clat = np.cos(lat)
        tlat = np.tan(lat)
        sgam = np.sin(gam)
        cgam = np.cos(gam)
        tgam = np.tan(gam)
        spsi = np.sin(psi)
        cpsi = np.cos(psi)
        
        #Pdot matrix eqs
        Jinv = np.linalg.inv(J)
        S = np.array([[0., -wz, wy],
                     [wz, 0., -wx],
                     [-wy, wx, 0.]])
        
        temp = np.dot(Jinv,Ext) - np.dot(np.dot(Jinv,S),np.dot(J,np.array([[wx],[wy],[wz]])))
        wxdot = temp[0]
        wydot = temp[1]
        wzdot = temp[2]
    
        # Gravity equations
        phi = np.pi/2 - lat
        cphi = np.cos(phi)
        sphi = np.sin(phi)
        gc = mu*(1 - 1.5*J2*(3*cphi**2 - 1)*(RE/r)**2)/r**2
        gd = -3*mu*J2*sphi*cphi*(RE/r)*(RE/r)/r**2
        
        dydt = [V*sgam,
                V*cgam*cpsi/r,
                V*cgam*spsi/(r*clat),
                -D/m - gc*sgam + gd*cgam*cpsi - ome**2*r*clat*(cgam*cpsi*slat - sgam*clat),
                V*cgam*spsi*tlat/r - gd*spsi/(V*cgam) + ome**2*r*spsi*slat*clat/(V*cgam) - (2*ome)*(tgam*cpsi*clat - slat),
                (V/r - gc/V)*cgam - gd*sgam*cpsi/V + ome**2*r*clat*(sgam*cpsi*slat + cgam*clat)/V + 2*ome*spsi*clat,
                0.5*(wz*q2 - wy*q3 + wx*q4), # Now rotational
                0.5*(-wz*q1 + wx*q3 + wy*q4),
                0.5*(wy*q1 - wx*q2 + wz*q4),
                0.5*(-wx*q1 - wy*q2 - wz*q3),
                wxdot,
                wydot,
                wzdot]


    return dydt