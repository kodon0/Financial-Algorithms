#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 14 12:02:51 2020

@author: kieranodonnell
"""

import pandas as pd
#IB API Client & Wrapper Classes

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

#Asynch implementation with mutlithreading
import threading
import time 



# {0:{'open', 'high', 'low', 'close'}} -> dict in dict for each ticker

class TradingApp(EWrapper,EClient):
    def __init__(self):
        EClient.__init__(self,self)
        self.data = {} # Storing data as a dict
        
    def historicalData(self, reqId, bar):
        if reqId not in self.data: # If reqId is NOT part of self.data -> create it (the key)!
            self.data[reqId] = [{"Date":bar.date, "Open":bar.open, 
                                "High":bar.high, "Low":bar.low,
                                "Close":bar.close, "Volume":bar.volume}] 
        if reqId in self.data:# If reqId IS part of self.data -> append new data!
            self.data[reqId].append({"Date":bar.date, "Open":bar.open, 
                                "High":bar.high, "Low":bar.low,
                                "Close":bar.close,"Volume":bar.volume})
        print("ReqId:{}, Date:{}, Open:{}, High:{}, Low:{}, Close:{}, Volume:{}".format(reqId, bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume))
        
        
def websocket_con():
    app.run() # start connection, is persistent, so needs to be closed!!
    

def usTechStk(symbol, secType="STK", currency ="USD", exchange="ISLAND"):
    contract = Contract() 
    contract.symbol = symbol
    contract.secType = secType
    contract.currency = currency
    contract.exchange = exchange
    return contract
    
def histData(req_num, contract, duration, candle_size):
    app.reqHistoricalData(reqId = req_num,
                          contract = contract,
                          endDateTime = '',
                          durationStr = duration,
                          barSizeSetting = candle_size,
                          whatToShow = 'ADJUSTED_LAST',
                          useRTH = 1,
                          formatDate = 1,
                          keepUpToDate = 0,
                          chartOptions = [])

app = TradingApp() # Instantiate class (self defined, global)
app.connect("127.0.0.1", 7497 , clientId=5) #Establish websocket connection

connection_thread = threading.Thread(target=websocket_con, daemon=True) # pass app.run
connection_thread.start()
time.sleep(1) # make a lag



########## Storing Data as Pandas ##########

def dataDataFrame(tradeapp_object, tickers):
    df_dict = {}
    for ticker in tickers:
        df_dict[ticker] = pd.DataFrame(tradeapp_object.data[tickers.index(ticker)])
        df_dict[ticker].set_index("Date", inplace=True)
    return df_dict

tickers = ["FB", "AMZN", "NVDA"] # Define tickers list


########## Iterative Excecution ##########
starttime = time.time()
timeout = starttime + 60*5
while time.time() <= timeout:
    for ticker in tickers:
        histData(tickers.index(ticker), usTechStk(ticker), '3600 S', '30 secs')
        time.sleep(3) # add some latency to ensure all details are pulled
    historical_data = dataDataFrame(app, tickers)
    time.sleep(30 - ((time.time() - starttime)%30)) # Sleeptime for next iteration
    
