#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 17:26:28 2020

@author: kieranodonnell
"""


import pandas as pd
import fxcmpy
import numpy as np
from stocktrends import Renko
import statsmodels.api as sm
import time
import copy
import matplotlib.pyplot as plt

#initiating API connection and defining trade parameters
token_path = "path"
con = fxcmpy.fxcmpy(access_token = open(token_path,'r').read(), log_level = 'error', server='demo')

#Strategy parameters
pair = 'AUD/USD'
pos_size = 10 #max capital allocated/position size for any currency pair

#How many points for calculation of slope
n = 10
#How many renko bars
r_bars = 2
#Renko brick size ATR period
atr_period = 12

data = con.get_candles(pair, period='m5', number=1000)
ohlc = data.iloc[:,[0,1,2,3,8]] #we are taking only Bid prices in this example
ohlc.columns = ["open","close","high","low","volume"] #convert names of columns to this

def MACD(DF,a,b,c):
    """function to calculate MACD
       typical values a = 12; b =26, c =9"""
    df = DF.copy()
    df["MA_Fast"]=df["close"].ewm(span=a,min_periods=a).mean()
    df["MA_Slow"]=df["close"].ewm(span=b,min_periods=b).mean()
    df["MACD"]=df["MA_Fast"]-df["MA_Slow"]
    df["Signal"]=df["MACD"].ewm(span=c,min_periods=c).mean()
    df.dropna(inplace=True)
    return (df["MACD"],df["Signal"])

def ATR(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['high']-df['low'])
    df['H-PC']=abs(df['high']-df['close'].shift(1))
    df['L-PC']=abs(df['low']-df['close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    #df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
    df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return df2

def slope(ser,n):
    "function to calculate the slope of n consecutive points on a plot"
    slopes = [i*0 for i in range(n-1)]
    for i in range(n,len(ser)+1):
        y = ser[i-n:i]
        x = np.array(range(n))
        y_scaled = (y - y.min())/(y.max() - y.min())
        x_scaled = (x - x.min())/(x.max() - x.min())
        x_scaled = sm.add_constant(x_scaled)
        model = sm.OLS(y_scaled,x_scaled)
        results = model.fit()
        slopes.append(results.params[-1])
    slope_angle = (np.rad2deg(np.arctan(np.array(slopes))))
    return np.array(slope_angle)

def renko_DF(DF):
    "function to convert ohlc data into renko bricks"
    df = DF.copy()
    df.reset_index(inplace=True)
    df = df.iloc[:,[0,1,2,3,4,5]]
    df.columns = ["date","open","close","high","low","volume"]

    df2 = Renko(df)
    df2.brick_size = max(0.0001,round(ATR(ohlc,atr_period)["ATR"][-1],4)) #Change atr_period in Strategy parameters
    renko_df = df2.get_ohlc_data()
    renko_df["bar_num"] = np.where(renko_df["uptrend"]==True,1,np.where(renko_df["uptrend"]==False,-1,0))
    for i in range(1,len(renko_df["bar_num"])):
        if renko_df["bar_num"][i]>0 and renko_df["bar_num"][i-1]>0:
            renko_df["bar_num"][i]+=renko_df["bar_num"][i-1]
        elif renko_df["bar_num"][i]<0 and renko_df["bar_num"][i-1]<0:
            renko_df["bar_num"][i]+=renko_df["bar_num"][i-1]
    renko_df.drop_duplicates(subset="date",keep="last",inplace=True)
    return renko_df

def CAGR(DF):
    "function to calculate the Cumulative Annual Growth Rate of a trading strategy"
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()
    n = len(df)/(252*78)
    CAGR = (df["cum_return"].tolist()[-1])**(1/n) - 1
    return CAGR

def volatility(DF):
    "function to calculate annualized volatility of a trading strategy"
    df = DF.copy()
    vol = df["ret"].std() * np.sqrt(252*78)
    return vol

def sharpe(DF,rf):
    "function to calculate sharpe ratio ; rf is the risk free rate"
    df = DF.copy()
    sr = (CAGR(df) - rf)/volatility(df)
    return sr

def max_dd(DF):
    "function to calculate max drawdown"
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()
    df["cum_roll_max"] = df["cum_return"].cummax()
    df["drawdown"] = df["cum_roll_max"] - df["cum_return"]
    df["drawdown_pct"] = df["drawdown"]/df["cum_roll_max"]
    max_dd = df["drawdown_pct"].max()
    return max_dd

#Merging renko df with original ohlc df
tickers = pair
ohlc_renko = {}
df = copy.deepcopy(ohlc)
tickers_signal = {}
tickers_ret = {}
for ticker in tickers:
    renko = renko_DF(ohlc)
    renko.columns = ["date","open","high","low","close","uptrend","bar_num"]
    #df["Date"] = ohlc.index
    ohlc_renko = ohlc.merge(renko.loc[:,["date","bar_num"]],how="outer",on="date")
    ohlc_renko["bar_num"].fillna(method='ffill',inplace=True)
    ohlc_renko["macd"]= MACD(ohlc_renko,12,26,9)[0]
    ohlc_renko["macd_sig"]= MACD(ohlc_renko,12,26,9)[1]
    ohlc_renko["macd_slope"] = slope(ohlc_renko["macd"],n) #Change n in Strategy parameters for optimisation ^^
    ohlc_renko["macd_sig_slope"] = slope(ohlc_renko["macd_sig"],n)
    tickers_signal = ""
    tickers_ret = []

#Identifying signals and calculating daily return
#Change r_bars in Strategy parameters for optimisation ^^
for i in range(len(ohlc)):
    if tickers_signal == "":
        tickers_ret.append(0)
        if i > 0:
            if ohlc_renko["bar_num"][i] >= r_bars and ohlc_renko["macd"][i] < ohlc_renko["macd_sig"][i] and \
                ohlc_renko["macd_slope"][i] < ohlc_renko["macd_sig_slope"][i]:
                tickers_signal = "Buy"

            elif ohlc_renko["bar_num"][i] <= -r_bars and ohlc_renko["macd"][i] > ohlc_renko["macd_sig"][i] and \
                ohlc_renko["macd_slope"][i] > ohlc_renko["macd_sig_slope"][i]:
                tickers_signal = "Sell"

    elif tickers_signal == "Sell":
        try:
            tickers_ret.append((ohlc_renko["close"][i] / ohlc_renko["close"][i-1])-1)
        except:
            tickers_ret.append((ohlc_renko["close"][i+1] / ohlc_renko["close"][i])-1)
        if i > 0:
            if ohlc_renko["bar_num"][i] <= -r_bars and ohlc_renko["macd"][i] > ohlc_renko["macd_sig"][i] and \
                ohlc_renko["macd_slope"][i] > ohlc_renko["macd_sig_slope"][i]:
                tickers_signal = "Buy"

            elif ohlc_renko["macd"][i] > ohlc_renko["macd_sig"][i] and \
                ohlc_renko["macd_slope"][i] > ohlc_renko["macd_sig_slope"][i]:
                tickers_signal = ""

    elif tickers_signal == "Buy":
        try:
            tickers_ret.append((ohlc_renko["close"][i] / ohlc_renko["close"][i-1])-1)
        except:
            tickers_ret.append((ohlc_renko["close"][i+1] / ohlc_renko["close"][i])-1)
        if i > 0:
            if ohlc_renko["bar_num"][i] >= r_bars and ohlc_renko["macd"][i] < ohlc_renko["macd_sig"][i] and \
                ohlc_renko["macd_slope"][i] < ohlc_renko["macd_sig_slope"][i]:
                tickers_signal = "Sell"

            elif ohlc_renko["macd"][i] < ohlc_renko["macd_sig"][i] and \
                ohlc_renko["macd_slope"][i] < ohlc_renko["macd_sig_slope"][i]:
                tickers_signal = ""

ohlc_renko["ret"] = np.array(tickers_ret)

profits = []
losses = []

for i in range(len(ohlc_renko)):
    if ohlc_renko['ret'][i] > 0:
        profits.append(1)
    if ohlc_renko['ret'][i] < 0:
        losses.append(1)

#calculating strategy's KPIs
CAGR(ohlc_renko)
sharpe(ohlc_renko,0.025)
max_dd(ohlc_renko)

print("Comulative annual growth return is:", str(round((CAGR(ohlc_renko)*100), 2)), "%")
print("Sharpe ratio is:", str(round(sharpe(ohlc_renko,0.025), 3)))
print("Max drawdown is:", str(round((max_dd(ohlc_renko)*100), 3)), "%")
print("--------------------------------------------")
print("Number of Trades:", len(profits + losses))
print("Number of Profits:", len(profits))
print("Number of Losses:", len(losses))
print("Winning percentage:", str(round(len(profits) / (len(profits) + len(losses)) * 100, 2)), "%")

#visualizing strategy returns
plt.figure(figsize=(16,8))
plt.title("Return of strategy", fontsize = 18)
plt.plot(ohlc_renko['date'], (1+ohlc_renko['ret']).cumprod(), color = 'm')
plt.xlabel('Date', fontsize = 12)
plt.ylabel('Performance', fontsize = 12);

con.close()
