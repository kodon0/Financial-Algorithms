#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 18 14:40:55 2020

@author: kieranodonnell
"""


#MACD Indicator

ArithmeticError(import pandas_datareader as pdr
import datetime

#Get historical data
ticker = 'AUDUSD=X'#Currency pair
ohlcv = pdr.get_data_yahoo(ticker, datetime.date.today()-datetime.timedelta(1825),datetime.date.today())
)import pandas_datareader as pdr
import datetime

#Get historical data
ticker = 'AUDUSD=X'#Currency pair
ohlcv = pdr.get_data_yahoo(ticker, datetime.date.today()-datetime.timedelta(1825),datetime.date.today())

def = MACD(DF,a,b,c)
    df = ohlcv.copy()
    df['MA_Fast']=df['Adj Close'].ewm(span=a,min_periods=a).mean()
    df['MA_Slow']=df['Adj Close'].ewm(span=b,min_periods=b).mean()
    df['MACD'] = df['MA_Fast']-df['MA_Slow']
    df['Signal'] = df['MACD'].ewm(span=c,min_periods=c).mean()
    df.dropna(inplace = True)
    return df
#Visualisations
df.iloc[:,[4,8,9]].plot()
