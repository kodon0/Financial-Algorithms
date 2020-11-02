#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 27 12:24:17 2020

@author: kieranodonnell
"""

import pandas as pd
import numpy as np
from copy import deepcopy
#IB API Client & Wrapper Classes

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

#Asynch implementation with mutlithreading
import threading
import time 



class TradeApp(EWrapper, EClient): 
    def __init__(self): 
        EClient.__init__(self, self) 
        self.data = {}
        
    def historicalData(self, reqId, bar):
        if reqId not in self.data:
            self.data[reqId] = [{"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume}]
        else:
            self.data[reqId].append({"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume})
        print("reqID:{}, date:{}, open:{}, high:{}, low:{}, close:{}, volume:{}".format(reqId,bar.date,bar.open,bar.high,bar.low,bar.close,bar.volume))

def usTechStk(symbol,sec_type="STK",currency="USD",exchange="ISLAND"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract 

def histData(req_num,contract,duration,candle_size):
    """extracts historical data"""
    app.reqHistoricalData(reqId=req_num, 
                          contract=contract,
                          endDateTime='',
                          durationStr=duration,
                          barSizeSetting=candle_size,
                          whatToShow='ADJUSTED_LAST',
                          useRTH=1,
                          formatDate=1,
                          keepUpToDate=0,
                          chartOptions=[])	 # EClient function to request contract details

def websocket_con():
    app.run()
    
app = TradeApp()
app.connect(host='127.0.0.1', port=7497, clientId=23) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()
time.sleep(1) # some latency added to ensure that the connection is established

tickers = ["FB","AMZN","INTC","MSFT","AAPL","GOOG","CSCO","CMCSA","ADBE","NVDA",
           "NFLX","PYPL","AMGN","AVGO","TXN","CHTR","QCOM","GILD","FISV","BKNG",
           "INTU","ADP","CME","TMUS","MU"]
'''tickers = ["FB","AMZN","INTC","MSFT","AAPL","GOOG","CSCO","CMCSA","ADBE","NVDA",]'''

for ticker in tickers:
    try:
        histData(tickers.index(ticker),usTechStk(ticker),'1 Y', '15 mins')
        time.sleep(60)
    except Exception as e:
        print(e)
        print("unable to extract data for {}".format(ticker))
################### Storing trade app object in dataframe #######################
def dataDataframe(symbols,TradeApp_obj):
    "returns extracted historical data in dataframe format"
    df_data = {}
    for symbol in symbols:
        df_data[symbol] = pd.DataFrame(TradeApp_obj.data[symbols.index(symbol)])
        df_data[symbol].set_index("Date",inplace=True)
    return df_data

# Extract and store historical data in dataframe
historicalData = dataDataframe(tickers,app)

####################### Technical Indicators for strategy ######################

def bollBnd(DF,n=20):
    "function to calculate Bollinger Band"
    df = DF.copy()
    #df["MA"] = df['close'].rolling(n).mean()
    df["MA"] = df['Close'].ewm(span=n,min_periods=n).mean()
    df["BB_up"] = df["MA"] + 2*df['Close'].rolling(n).std(ddof=0) #ddof=0 is required since we want to take the standard deviation of the population and not sample
    df["BB_dn"] = df["MA"] - 2*df['Close'].rolling(n).std(ddof=0) #ddof=0 is required since we want to take the standard deviation of the population and not sample
    df["BB_width"] = df["BB_up"] - df["BB_dn"]
    df.dropna(inplace=True)
    return df

def RSI(DF,n=20):
    
    "Function to calculate RSI"
    
    df = DF.copy()
    df['delta']=df['Close'] - df['Close'].shift(1)
    df['gain']=np.where(df['delta']>=0,df['delta'],0)
    df['loss']=np.where(df['delta']<0,abs(df['delta']),0)
    avg_gain = []
    avg_loss = []
    gain = df['gain'].tolist()
    loss = df['loss'].tolist()
    for i in range(len(df)):
        if i < n:
            avg_gain.append(np.NaN)
            avg_loss.append(np.NaN)
        elif i == n:
            avg_gain.append(df['gain'].rolling(n).mean()[n])
            avg_loss.append(df['loss'].rolling(n).mean()[n])
        elif i > n:
            avg_gain.append(((n-1)*avg_gain[i-1] + gain[i])/n)
            avg_loss.append(((n-1)*avg_loss[i-1] + loss[i])/n)
    df['avg_gain']=np.array(avg_gain)
    df['avg_loss']=np.array(avg_loss)
    df['RS'] = df['avg_gain']/df['avg_loss']
    df['RSI'] = 100 - (100/(1+df['RS']))
    return df['RSI']


def MACD(DF,a=12,b=26,c=9):
    """function to calculate MACD
       typical values a(fast moving average) = 12; 
                      b(slow moving average) =26; 
                      c(signal line ma window) =9"""
    df = DF.copy()
    df["MA_Fast"]=df["Close"].ewm(span=a,min_periods=a).mean()
    df["MA_Slow"]=df["Close"].ewm(span=b,min_periods=b).mean()
    df["MACD"]=df["MA_Fast"]-df["MA_Slow"]
    df["Signal"]=df["MACD"].ewm(span=c,min_periods=c).mean()
    df.dropna(inplace=True)
    return df

def ADX(DF,n=20):
    
    '''Function to calculate ADX: 0-25 = terrible, 25-50= OK,
    50-75= Awesome, 75+ = EPIC. Non-directionals!'''
    df2 = DF.copy()
    df2['H-L']=abs(df2['High']-df2['Low'])
    df2['H-PC']=abs(df2['High']-df2['Close'].shift(1))
    df2['L-PC']=abs(df2['Low']-df2['Close'].shift(1))
    df2['TR']=df2[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df2['+DM']=np.where((df2['High']-df2['High'].shift(1))>(df2['Low'].shift(1)-df2['Low']),df2['High']-df2['High'].shift(1),0)
    df2['+DM']=np.where(df2['+DM']<0,0,df2['+DM'])
    df2['-DM']=np.where((df2['Low'].shift(1)-df2['Low'])>(df2['High']-df2['High'].shift(1)),df2['Low'].shift(1)-df2['Low'],0)
    df2['-DM']=np.where(df2['-DM']<0,0,df2['-DM'])

    df2["+DMMA"]=df2['+DM'].ewm(span=n,min_periods=n).mean()
    df2["-DMMA"]=df2['-DM'].ewm(span=n,min_periods=n).mean()
    df2["TRMA"]=df2['TR'].ewm(span=n,min_periods=n).mean()

    df2["+DI"]=100*(df2["+DMMA"]/df2["TRMA"])
    df2["-DI"]=100*(df2["-DMMA"]/df2["TRMA"])
    df2["DX"]=100*(abs(df2["+DI"]-df2["-DI"])/(df2["+DI"]+df2["-DI"]))
    
    df2["ADX"]=df2["DX"].ewm(span=n,min_periods=n).mean()

    return df2['ADX']

def stochOscltr(DF,a=20,b=3):
    """function to calculate Stochastics
       a = lookback period
       b = moving average window for %D"""
    df = DF.copy()
    df['C-L'] = df['Close'] - df['Low'].rolling(a).min()
    df['H-L'] = df['High'].rolling(a).max() - df['Low'].rolling(a).min()
    df['%K'] = df['C-L']/df['H-L']*100
    #df['%D'] = df['%K'].ewm(span=b,min_periods=b).mean()
    return df['%K'].rolling(b).mean()

def atr(DF,n):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    df['H-L']=abs(df['High']-df['Low'])
    df['H-PC']=abs(df['High']-df['Close'].shift(1))
    df['L-PC']=abs(df['Low']-df['Close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    #df['ATR'] = df['TR'].rolling(n).mean()
    df['ATR'] = df['TR'].ewm(com=n,min_periods=n).mean()
    return df['ATR']

def CAGR(DF):
    "function to calculate the Cumulative Annual Growth Rate of a trading strategy"
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()
    n = len(df)/(252*26)
    CAGR = (df["cum_return"].tolist()[-1])**(1/n) - 1
    return CAGR

def volatility(DF):
    "function to calculate annualized volatility of a trading strategy"
    df = DF.copy()
    vol = df["ret"].std() * np.sqrt(252*26)
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

def winRate(DF):
    "function to calculate win rate of intraday trading strategy"
    df = DF["return"]
    pos = df[df>1]
    neg = df[df<1]
    return (len(pos)/len(pos+neg))*100

def meanretpertrade(DF):
    df = DF["return"]
    df_temp = (df-1).dropna()
    return df_temp[df_temp!=0].mean()

def meanretwintrade(DF):
    df = DF["return"]
    df_temp = (df-1).dropna()
    return df_temp[df_temp>0].mean()

def meanretlostrade(DF):
    df = DF["return"]
    df_temp = (df-1).dropna()
    return df_temp[df_temp<0].mean()

def maxconsectvloss(DF):
    df = DF["return"]
    df_temp = df.dropna(axis=0)
    df_temp2 = np.where(df_temp<1,1,0)
    count_consecutive = []
    seek = 0
    for i in range(len(df_temp2)):
        if df_temp2[i] == 0:
            seek = 0
        else:
            seek = seek + 1
            count_consecutive.append(seek)
    return max(count_consecutive)

#extract and store historical data in dataframe
historicalData = dataDataframe(tickers,app)

    
#####################################   Back Testing   ##################################

ohlc_dict = deepcopy(historicalData)
tickers_signal = {}
tickers_ret = {}
trade_count = {}
trade_data = {}
for ticker in tickers:
    print("Calculating MACD & Stochastics for ",ticker)
    ohlc_dict[ticker]["stoch"] = stochOscltr(ohlc_dict[ticker])
    ohlc_dict[ticker]["macd"] = MACD(ohlc_dict[ticker])["MACD"]
    ohlc_dict[ticker]["signal"] = MACD(ohlc_dict[ticker])["Signal"]
    ohlc_dict[ticker]["rsi"] = RSI(ohlc_dict[ticker],20)
    ohlc_dict[ticker]["atr"] = atr(ohlc_dict[ticker],60)
    ohlc_dict[ticker]["adx"] = ADX(ohlc_dict[ticker],20)
    ohlc_dict[ticker]["bb_down"] = bollBnd(ohlc_dict[ticker])["BB_dn"]
    ohlc_dict[ticker]["bb_up"] = bollBnd(ohlc_dict[ticker])["BB_up"]
    ohlc_dict[ticker].dropna(inplace=True)
    trade_count[ticker] = 0
    tickers_signal[ticker] = ""
    tickers_ret[ticker] = [0]
    trade_data[ticker] = {}
    

 ##################################### Identifying Signals and calculating daily return (Stop Loss factored in) #####################################
for ticker in tickers:
    print("Calculating daily returns for ",ticker)
    for i in range(1,len(ohlc_dict[ticker])):
        if tickers_signal[ticker] == "":
            tickers_ret[ticker].append(0)
            if ohlc_dict[ticker]["macd"][i]> ohlc_dict[ticker]["signal"][i] and \
               ohlc_dict[ticker]["stoch"][i]> 30 and \
               ohlc_dict[ticker]["stoch"][i] > ohlc_dict[ticker]["stoch"][i-1] and \
               ohlc_dict[ticker]["rsi"][i] > 20 and \
               ohlc_dict[ticker]["Close"][i] > ohlc_dict[ticker]["bb_down"][i-1] and \
               ohlc_dict[ticker]["adx"][i] > 60:
                   tickers_signal[ticker] = "Buy"
                   trade_count[ticker]+=1
                   trade_data[ticker][trade_count[ticker]] = [ohlc_dict[ticker]["Close"][i]]
                     
        elif tickers_signal[ticker] == "Buy":
            if ohlc_dict[ticker]["Low"][i]<ohlc_dict[ticker]["Close"][i-1] - ohlc_dict[ticker]["atr"][i-1]:
                tickers_signal[ticker] = ""
                trade_data[ticker][trade_count[ticker]].append(ohlc_dict[ticker]["Close"][i-1] - ohlc_dict[ticker]["atr"][i-1])
                trade_count[ticker]+=1
                tickers_ret[ticker].append(((ohlc_dict[ticker]["Close"][i-1] - ohlc_dict[ticker]["atr"][i-1])/ohlc_dict[ticker]["Close"][i-1])-1)
            else:
                tickers_ret[ticker].append((ohlc_dict[ticker]["Close"][i]/ohlc_dict[ticker]["Close"][i-1])-1)
                
                
    if trade_count[ticker]%2 != 0:
        trade_data[ticker][trade_count[ticker]].append(ohlc_dict[ticker]["Close"][i])
    
    ohlc_dict[ticker]["ret"] = np.array(tickers_ret[ticker])

    
##################################### Calculating overall strategy's KPIs #####################################
trade_df = {}
for ticker in tickers:
    trade_df[ticker] = pd.DataFrame(trade_data[ticker]).T
    trade_df[ticker].columns = ["trade_entry_pr","trade_exit_pr"]
    trade_df[ticker]["return"] = trade_df[ticker]["trade_exit_pr"]/trade_df[ticker]["trade_entry_pr"]


##################################### Calculating individual stock's  #####################################
win_rate = {}
mean_ret_pt = {}
mean_ret_pwt = {}
mean_ret_plt = {}
max_cons_loss = {}
for ticker in tickers:
    print("calculating intraday KPIs for ",ticker)
    win_rate[ticker] =  winRate(trade_df[ticker])      
    mean_ret_pt[ticker] =  meanretpertrade(trade_df[ticker])
    mean_ret_pwt[ticker] =  meanretwintrade(trade_df[ticker])
    mean_ret_plt[ticker] =  meanretlostrade(trade_df[ticker])
    max_cons_loss[ticker] =  maxconsectvloss(trade_df[ticker])

KPI_df = pd.DataFrame([win_rate,mean_ret_pt,mean_ret_pwt,mean_ret_plt,max_cons_loss],
                      index=["Win Rate","Mean Return Per Trade","MR Per WR", "MR Per LR", "Max Cons Loss"])      
KPI_df.T

##################################### Mean win rates #####################################
filtered_vals = [v for _, v in win_rate.items() if v != 0]
average = sum(filtered_vals) / len(filtered_vals)
print("Average win rate:", average)
