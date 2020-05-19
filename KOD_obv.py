#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 19 16:07:50 2020

@author: kieranodonnell
"""


#OBV Indicator

import pandas_datareader as pdr
import datetime
import numpy as np

#Get historical data
ticker = 'AUDUSD=X'#Currency pair
ohlcv = pdr.get_data_yahoo(ticker, datetime.date.today()-datetime.timedelta(1825),datetime.date.today())
DF = ohlcv

def OBV(DF):
    """function to calculate On Balance Volume"""
    df = DF.copy()
    df['daily_ret'] = df['Adj Close'].pct_change()
    df['direction'] = np.where(df['daily_ret']>=0,1,-1)
    df['direction'][0] = 0
    df['vol_adj'] = df['Volume'] * df['direction']
    df['obv'] = df['vol_adj'].cumsum()
    return df['obv']

