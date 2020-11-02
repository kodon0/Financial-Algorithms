#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 14:00:16 2020

@author: kieranodonnell
"""

#IB API Client & Wrapper Classes

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

#Asynch implementation with mutlithreading
import threading
import time

class TradingApp(EWrapper,EClient):
    def __init__(self):
        EClient.__init__(self,self)
        
    def error(self, reqId, errorCode, errorString):
        print("Error {} {} {}".format(reqId,errorCode,errorString))
        
    def contractDetails(self, reqId, contractDetails):
        print("reqId: {}, Contract Details: {}".format(reqId, contractDetails))
        
def websocket_con():
    app.run() # start connection, is persistent, so needs to be closed!!
    
app = TradingApp() # Instantiate class (self defined)
app.connect("127.0.0.1", 7497 , clientId=1) #Establish websocket connection

connection_thread = threading.Thread(target=websocket_con, daemon=True) # pass app.run
connection_thread.start()
time.sleep(1) # make a lag


contract = Contract() # create contract object from class, with all required attributes
contract.symbol = "BRKM5"
contract.secType = "STK"
contract.currency = "BRL"
contract.exchange = "BOVESPA"

app.reqContractDetails(100, contract) #connect contracts to app
time.sleep(5) # close daemon thread!
