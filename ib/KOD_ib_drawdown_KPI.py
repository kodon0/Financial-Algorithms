#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 15:30:23 2020

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
    histData(tickers.index(ticker),usTechStk(ticker),'2 Y', '1 day')
    time.sleep(5)

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

################### KPI Definitions #######################


df = historicalData["AMZN"].copy()
df["return"] = df["Close"].pct_change()

def CAGR(DF):
    df = DF.copy()
    df["cum_return"] = (1+df["return"]).cumprod()
    n = len(df)/252 # 252 trading days per year
    # n = len(df)/(252 * 26) # 252 x 26 -> one year... adjust accoridng to candles
    CAGR = (df["cum_return"].to_list()[-1]**(1/n)) - 1
    return CAGR


def volatility(DF):
    df = DF.copy()
    vol = df["return"].std() * np.sqrt(252)
    return vol

def sharpe(DF, rf_rate):
    df = DF.copy()
    return ((CAGR(df) - rf_rate) / volatility(df))

def max_drawdown(DF):
    df = DF.copy()
    df["cum_return"] = (1+df["return"]).cumprod()
    df["max_cum_ret"] = df["cum_return"].cummax()
    df["drawdown"] = df["max_cum_ret"] - df["cum_return"]
    df["drawdown_pct"] = df["drawdown"]/df["max_cum_ret"]
    return df["drawdown_pct"].max()


CAGR(df)
volatility(df)
sharpe(df, 0.03)
max_drawdown(df)

df['cum_return'].plot()