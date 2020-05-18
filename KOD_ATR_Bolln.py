#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 18 15:30:54 2020

@author: kieranodonnell
"""


#ATR and Bollinger Bands
import pandas_datareader as pdr
import datetime

#Get historical data
ticker = 'AUDUSD=X'#Currency pair
ohlcv = pdr.get_data_yahoo(ticker, datetime.date.today()-datetime.timedelta(1825),datetime.date.today())

def ATR(DF,n):
    #This calculates TRUE RANGE and AVERAGE TRUE RANGE 
    #Need to find adequate n periods
    df= DF.copy()
    df['H-L'] = abs(df['High']-df['Low'].shift(1))
    df['H-PC'] = abs(df['High']-df['Adj Close'].shift(1))
    df['L-PC'] = abs(df['Low']-df['Adj Close'].shift(1))
    df['TR'] = df[['H-L','H-PC','L-PC']].max(axis = 1, skipna= False)
    #df['ATR'] = df['TR'].rolling(n).mean() #Can use exponential mean below
    df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
    df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return df2

def BollBnd(DF,n):
    #This function calculates the bollinger bands up and down
    df = DF.copy()
    df["MA"] = df['Adj Close'].rolling(n).mean()
    df["BB_up"] = df["MA"] + 2*df['Adj Close'].rolling(n).std(ddof=0) #ddof=0 is required since we want to take the standard deviation of the population and not sample
    df["BB_dn"] = df["MA"] - 2*df['Adj Close'].rolling(n).std(ddof=0) #ddof=0 is required since we want to take the standard deviation of the population and not sample
    df["BB_width"] = df["BB_up"] - df["BB_dn"]
    df.dropna(inplace=True)
    return df

#ATR visualisation
ATR(ohlcv,20).iloc[-100:,[-1]].plot(title="ATR")

#Bollinger Visualisation
BollBnd(ohlcv,20).iloc[-100:,[-4,-3,-2]].plot(title="BollingerBands")