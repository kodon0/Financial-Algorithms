#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 19 14:07:49 2020

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



class TradingApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self,self)
        self.acc_summary = pd.DataFrame(columns=['ReqId', 'Account', 'Tag', 'Value', 'Currency'])
        self.pnl_summary = pd.DataFrame(columns=['ReqId', 'DailyPnL', 'UnrealizedPnL', 'RealizedPnL'])

    def accountSummary(self, reqId, account, tag, value, currency):
        super().accountSummary(reqId, account, tag, value, currency)
        dictionary = {"ReqId":reqId, "Account": account, "Tag": tag, "Value": value, "Currency": currency}
        self.acc_summary = self.acc_summary.append(dictionary, ignore_index=True)
        
    def pnl(self, reqId, dailyPnL, unrealizedPnL, realizedPnL):
        super().pnl(reqId, dailyPnL, unrealizedPnL, realizedPnL)
        dictionary = {"ReqId":reqId, "DailyPnL": dailyPnL, "UnrealizedPnL": unrealizedPnL, "RealizedPnL": realizedPnL}
        self.pnl_summary = self.pnl_summary.append(dictionary, ignore_index=True)
   
        
def websocket_con():
    app.run() # start connection, is persistent, so needs to be closed!!
    

app = TradingApp() # Instantiate class (self defined, global)
app.connect("127.0.0.1", 7497 , clientId=1) #Establish websocket connection

connection_thread = threading.Thread(target=websocket_con, daemon=True) # pass app.run
connection_thread.start()
time.sleep(1) # make a lag

app.reqAccountSummary(1, "All", "$LEDGER:ALL")
time.sleep(1)
acc_summ_df = app.acc_summary

app.reqPnL(2, "DU111519", "")
time.sleep(1)
pnl_summ_df = app.pnl_summary

time.sleep(5)