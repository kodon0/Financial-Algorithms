#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 19 13:56:14 2020

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
        self.position_df = pd.DataFrame(columns=['Account', 'Symbol', 'SecType',
                                            'Currency', 'Position', 'Avg cost'])
        
    def position(self, account, contract, position, avgCost):
        super().position(account, contract, position, avgCost)
        dictionary = {"Account":account, "Symbol": contract.symbol, "SecType": contract.secType,
                      "Currency": contract.currency, "Position": position, "Avg cost": avgCost}
        self.position_df = self.position_df.append(dictionary, ignore_index=True)
        

def websocket_con():
    app.run() # start connection, is persistent, so needs to be closed!!
    

app = TradingApp() # Instantiate class (self defined, global)
app.connect("127.0.0.1", 7497 , clientId=5) #Establish websocket connection

connection_thread = threading.Thread(target=websocket_con, daemon=True) # pass app.run
connection_thread.start()
time.sleep(1) # make a lag

app.reqPositions()
time.sleep(1)
position_df = app.position_df
time.sleep(5)

