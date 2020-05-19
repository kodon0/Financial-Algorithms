#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 19 16:16:06 2020

@author: kieranodonnell
"""


#Chart slopes implementation

import pandas_datareader as pdr
import datetime
import pandas as pd
import numpy as np
import statsmodels.api as sm

#Get historical data
ticker = 'AUDUSD=X'#Currency pair
ohlcv = pdr.get_data_yahoo(ticker, datetime.date.today()-datetime.timedelta(200),datetime.date.today())

def slope(ser,n):
    #This caluclates the slope for n points
    #Based on a series - not a DF
    #Like a rolling slope
    slopes = [i*0 for i in range(n-1)]
    for i in range(n,len(ser)+1):
        y = ser[i-n:i]
        x = np.array(range(n))
        #Need to scale x and y (otherwise slopes will be meaningless)
        y_scaled = (y - y.min())/(y.max() - y.min())
        x_scaled = (x - x.min())/(x.max() - x.min())
        #Need constant, dont want 0 intercept
        x_scaled = sm.add_constant(x_scaled)
        #Now fit OLS from statsmodels
        model = sm.OLS(y_scaled,x_scaled)
        results = model.fit()
        #results.summary() gives summary of curve fitting
        #results.params
        slopes.append(results.params[-1])
    slope_angle = (np.rad2deg(np.arctan(np.array(slopes)))) #Perpendicular distance is tangent, and we want degrees
    return np.array(slope_angle)

#Visualise
df = ohlcv.copy()
df['slope']= slope(ohlcv['Adj Close'],5)

df.iloc[:,[5,6]].plot(subplots = True, layout = (2,1))