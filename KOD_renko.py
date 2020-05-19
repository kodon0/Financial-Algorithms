#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 19 15:45:58 2020

@author: kieranodonnell
"""


#Renko Indicator ->ohlcv into Renko via stcoktrends library, makes renko much easier

import pandas_datareader as pdr
import datetime
from stocktrends import Renko


#Get historical data
ticker = 'AUDUSD=X'#Currency pair
ohlcv = pdr.get_data_yahoo(ticker, datetime.date.today()-datetime.timedelta(1825),datetime.date.today())

#ATR defined 
#Renko brick size determined by previously defined ATR
def ATR(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['High']-df['Low'])
    df['H-PC']=abs(df['High']-df['Adj Close'].shift(1))
    df['L-PC']=abs(df['Low']-df['Adj Close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return df2

#Using ATR to define brick size in renko
    

def renko_DF(DF):
    "function to convert ohlc data into renko bricks"
    df = DF.copy()
    df.reset_index(inplace=True)
    #Change names to be cosnistent with renko format from stocktrends
    df = df.iloc[:,[0,1,2,3,5,6]]
    df.rename(columns = {"Date" : "date", "High" : "high","Low" : "low", "Open" : "open","Adj Close" : "close", "Volume" : "volume"}, inplace = True)
    df2 = Renko(df)
    df2.brick_size = round(ATR(DF,120)["ATR"][-1],0)#Brick size
    #renko_df = df2.get_bricks() #if get_bricks() does not work try using get_ohlc_data() instead
    renko_df = df2.get_ohlc_data()
    return renko_df

