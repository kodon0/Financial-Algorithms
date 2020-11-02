#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 19 16:57:24 2020

@author: kieranodonnell
"""

import pandas as pd
import numpy as np 
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

tickers = ["FB","AMZN","INTC"]
for ticker in tickers:
    histData(tickers.index(ticker),usTechStk(ticker),'5 D', '5 mins')
    time.sleep(2)

################### Storing trade app object in dataframe #######################

def dataDataframe(symbols,TradeApp_obj):
    "returns extracted historical data in dataframe format"
    df_data = {}
    for symbol in symbols:
        df_data[symbol] = pd.DataFrame(TradeApp_obj.data[symbols.index(symbol)])
        df_data[symbol].set_index("Date",inplace=True)
    return df_data

####################### Defining Stochastic Oscillator #######################

def stochasticOscillator(DF,a = 20, b = 3):
    
    '''Main idea is that before any price change, momentum (i.e. dy/dx of price MUST change!
    Between 0 and 100, and as current price approachas 100 -> price probs is at its highest over the lookback period .
    Values avove 80 represent overbought, values lower than 20 is oversold. Only works well in trending markets
    a = lookback period, b = moving average over a (%D)'''
    
    df = DF.copy()
    df['C-L'] = df['Close'] - df['Low'].rolling(a).min()
    df['H-L'] = df['High'].rolling(a).max() - df['Low'].rolling(a).min()
    df['%K'] = df['C-L']/df['H-L']*100
    df['%D'] = df['%K'].ewm(span=b,min_periods=b).mean()
    return df[['%K','%D']]

####################### Make Stochastich Oscillators for all Tickers #######################

# Extract and store historical data in dataframe
historicalData = dataDataframe(tickers,app)

# Calculate Bollinger Bands values for all tickers and srore them in a dataframe
stoch = {}
for ticker in tickers:
    stoch[ticker] = stochasticOscillator(historicalData[ticker],20,3)