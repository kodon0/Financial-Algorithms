#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 23 11:18:47 2020

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

'''tickers = ["FB","AMZN","INTC","MSFT","AAPL","GOOG","CSCO","CMCSA","ADBE","NVDA",
           "NFLX","PYPL","AMGN","AVGO","TXN","CHTR","QCOM","GILD","FISV","BKNG",
           "INTU","ADP","CME","TMUS","MU"]'''
tickers = ["FB","AMZN","INTC","MSFT","AAPL","GOOG","CSCO","CMCSA","ADBE","NVDA",]

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

#extract and store historical data in dataframe
historicalData = dataDataframe(tickers,app)

    
#####################################   Back Testing   ##################################
ohlc_dict = deepcopy(historicalData)
tickers_signal = {}
tickers_ret = {}
trade_count = {}
for ticker in tickers:
    print("Calculating MACD & Stochastics for ",ticker)
    ohlc_dict[ticker]["stoch"] = stochOscltr(ohlc_dict[ticker])
    ohlc_dict[ticker]["macd"] = MACD(ohlc_dict[ticker])["MACD"]
    ohlc_dict[ticker]["rsi"] = RSI(ohlc_dict[ticker],20)
    ohlc_dict[ticker]["bb_down"] = bollBnd(ohlc_dict[ticker])["BB_dn"]
    ohlc_dict[ticker]["bb_up"] = bollBnd(ohlc_dict[ticker])["BB_up"]
    ohlc_dict[ticker]["signal"] = MACD(ohlc_dict[ticker])["Signal"]
    ohlc_dict[ticker]["atr"] = atr(ohlc_dict[ticker],60)
    ohlc_dict[ticker].dropna(inplace=True)
    trade_count[ticker] = 0
    tickers_signal[ticker] = ""
    tickers_ret[ticker] = [0]
    
    
#####################################   Signal Generation  ##################################
#Identifying Signals and calculating daily return (Stop Loss factored in)
for ticker in tickers:
    print("Calculating daily returns for ",ticker)
    for i in range(1,len(ohlc_dict[ticker])):
        if tickers_signal[ticker] == "":
            tickers_ret[ticker].append(0)
            if ohlc_dict[ticker]["macd"][i]> ohlc_dict[ticker]["signal"][i] and \
               ohlc_dict[ticker]["stoch"][i]> 30 and \
               ohlc_dict[ticker]["stoch"][i] > ohlc_dict[ticker]["stoch"][i-1] and \
                   ohlc_dict[ticker]["rsi"] < 30 and \
                       ohlc_dict[ticker]["Close"] < ohlc_dict[ticker]["bb_down"]:
                   tickers_signal[ticker] = "Buy"
                   trade_count[ticker]+=1
                     
        elif tickers_signal[ticker] == "Buy":
            if ohlc_dict[ticker]["Low"][i]<ohlc_dict[ticker]["Close"][i-1] - ohlc_dict[ticker]["atr"][i-1]:
                tickers_signal[ticker] = ""
                trade_count[ticker]+=1
                tickers_ret[ticker].append(((ohlc_dict[ticker]["Close"][i-1] - ohlc_dict[ticker]["atr"][i-1])/ohlc_dict[ticker]["Close"][i-1])-1)
            else:
                tickers_ret[ticker].append((ohlc_dict[ticker]["Close"][i]/ohlc_dict[ticker]["Close"][i-1])-1)
                
                
    ohlc_dict[ticker]["ret"] = np.array(tickers_ret[ticker])
    
    
################################## Strategy's KPIs ##################################
strategy_df = pd.DataFrame()
for ticker in tickers:
    strategy_df[ticker] = ohlc_dict[ticker]["ret"]
strategy_df["ret"] = strategy_df.mean(axis=1)

"""
# creating dataframe with daily returns
strategy_df.index = pd.to_datetime(strategy_df.index)
strategy_df.index = strategy_df.index.tz_localize('Asia/Kolkata').tz_convert('America/Indiana/Petersburg')    
daily_ret_df = strategy_df["ret"].resample("D").sum(min_count=1).dropna()

# plotting daily returns
daily_ret_df.plot(kind="bar") 
"""

CAGR(strategy_df)
sharpe(strategy_df,0.025)
max_dd(strategy_df)  


# vizualization of strategy return
(1+strategy_df["ret"]).cumprod().plot()


#calculating individual stock's KPIs
cagr = {}
sharpe_ratios = {}
max_drawdown = {}
for ticker in tickers:
    print("calculating KPIs for ",ticker)      
    cagr[ticker] =  CAGR(ohlc_dict[ticker])
    sharpe_ratios[ticker] =  sharpe(ohlc_dict[ticker],0.025)
    max_drawdown[ticker] =  max_dd(ohlc_dict[ticker])
    
KPI_df = pd.DataFrame([cagr,sharpe_ratios,max_drawdown],index=["Return","Sharpe Ratio","Max Drawdown"])      
KPI_df.T