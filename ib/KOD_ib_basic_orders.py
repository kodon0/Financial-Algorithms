#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 16 13:20:32 2020

@author: kieranodonnell
"""

# IB API Client & Wrapper Classes

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order


#Asynch implementation with multithreading
import threading
import time

class TradingApp(EWrapper,EClient):
    def __init__(self):
        EClient.__init__(self,self)
                
    def nextValidId(self, orderId: int): # This function generates a subsequent valid orderId 
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)
        
def websocket_con():
    app.run() # start connection, is persistent, so needs to be closed!!
    
app = TradingApp() # Instantiate class (self defined)
app.connect("127.0.0.1", 7497 , clientId=1) #Establish websocket connection

connection_thread = threading.Thread(target=websocket_con, daemon=True) # pass app.run
connection_thread.start()
time.sleep(1) # make a lag


contract = Contract() # create contract object from class, with all required attributes
contract.symbol = "FB"
contract.secType = "STK"
contract.currency = "USD"
contract.exchange = "ISLAND"

order = Order()
order.action = "BUY"
order.orderType = "LMT"
order.totalQuantity = 3
order.lmtPrice = 80

app.placeOrder(app.nextValidOrderId, contract, order) #connect contracts to app
time.sleep(5) # close daemon thread!