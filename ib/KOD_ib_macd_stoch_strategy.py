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
from ibapi.order import Order

#Asynch implementation with mutlithreading
import threading
import time 



# {0:{'open', 'high', 'low', 'close'}} -> dict in dict for each ticker

class TradeApp(EWrapper, EClient): 
    def __init__(self): 
        EClient.__init__(self, self) 
        self.data = {}
        self.pos_df = pd.DataFrame(columns=['Account', 'Symbol', 'SecType',
                                            'Currency', 'Position', 'Avg cost'])
        self.order_df = pd.DataFrame(columns=['PermId', 'ClientId', 'OrderId',
                                              'Account', 'Symbol', 'SecType',
                                              'Exchange', 'Action', 'OrderType',
                                              'TotalQty', 'CashQty', 'LmtPrice',
                                              'AuxPrice', 'Status'])
        
    def openOrder(self, orderId, contract, order, orderState):
        super().openOrder(orderId, contract, order, orderState)
        dictionary = {"PermId":order.permId, "ClientId": order.clientId, "OrderId": orderId, 
                      "Account": order.account, "Symbol": contract.symbol, "SecType": contract.secType,
                      "Exchange": contract.exchange, "Action": order.action, "OrderType": order.orderType,
                      "TotalQty": order.totalQuantity, "CashQty": order.cashQty, 
                      "LmtPrice": order.lmtPrice, "AuxPrice": order.auxPrice, "Status": orderState.status}
        self.order_df = self.order_df.append(dictionary, ignore_index=True)
        
    def position(self, account, contract, position, avgCost):
        super().position(account, contract, position, avgCost)
        dictionary = {"Account":account, "Symbol": contract.symbol, "SecType": contract.secType,
                      "Currency": contract.currency, "Position": position, "Avg cost": avgCost}
        self.pos_df = self.pos_df.append(dictionary, ignore_index=True)
    
    def positionEnd(self):
        print("Latest Position Data Extracted!")
        
    def nextValidId(self, orderId: int): # This function generates a subsequent valid orderId 
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)
       
    def historicalData(self, reqId, bar):
        print(f'Time: {bar.date}, Open: {bar.open}, Close: {bar.close}')
        if reqId not in self.data:
            self.data[reqId] = [{"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume}]
        else:
            self.data[reqId].append({"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume})


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


tickers = ["FB","AMZN","INTC","MSFT","AAPL","GOOG","CSCO","CMCSA","ADBE","NVDA",
           "NFLX","PYPL","AMGN","AVGO","TXN","CHTR","QCOM","GILD","FISV","BKNG",
           "INTU","ADP","CME","TMUS","MU"]

# Define starting capital per stock....
capital = 1000

########## Storing Data as Pandas, Order Functions, TA Functions ##########

def dataDataframe(TradeApp_obj,symbols,symbol):
    "returns extracted historical data in dataframe format"
    df = pd.DataFrame(TradeApp_obj.data[symbols.index(symbol)])
    df.set_index("Date",inplace=True)
    TradeApp_obj.data = {}
    return df

def marketOrder(direction, quantity):
    order = Order()
    order.action = direction
    order.orderType = "MKT"
    order.totalQuantity = quantity
    return order

def stopOrder(direction, quantity, stop_price):
    order = Order() 
    order.action = direction
    order.orderType = "STP"
    order.auxPrice = stop_price
    order.totalQuantity = quantity
    return order

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

def main():
    app.reqPositions()
    time.sleep(2)
    pos_df = app.pos_df
    pos_df.drop_duplicates(inplace=True,ignore_index=True) # position callback tends to give duplicate values
    app.reqOpenOrders()
    time.sleep(2)
    ord_df = app.order_df
    for ticker in tickers:
        print("starting passthrough for.....",ticker)
        histData(tickers.index(ticker),usTechStk(ticker),'5 D', '5 mins')
        time.sleep(5)
        df = dataDataframe(app,tickers,ticker)
        df["stoch"] = stochOscltr(df)
        df["macd"] = MACD(df)["MACD"]
        df["signal"] = MACD(df)["Signal"]
        df["atr"] = atr(df,60)
        df.dropna(inplace=True)
        quantity = int(capital/df["Close"][-1])
        if quantity == 0:
            continue
        if len(pos_df.columns)==0: # Have no open trades
            if df["macd"][-1]> df["signal"][-1] and \
               df["stoch"][-1]> 30 and \
               df["stoch"][-1] > df["stoch"][-2]:
                   app.reqIds(-1)
                   time.sleep(2)
                   order_id = app.nextValidOrderId
                   app.placeOrder(order_id,usTechStk(ticker),marketOrder("BUY",quantity))
                   app.placeOrder(order_id+1,usTechStk(ticker),stopOrder("SELL",quantity,round(df["Close"][-1]-df["atr"][-1],1)))
          
        elif len(pos_df.columns)!=0 and ticker not in pos_df["Symbol"].tolist(): # Have an open position, but current ticker is not in open orders df
            if df["macd"][-1]> df["signal"][-1] and \
               df["stoch"][-1]> 30 and \
               df["stoch"][-1] > df["stoch"][-2]:
                   app.reqIds(-1)
                   time.sleep(2)
                   order_id = app.nextValidOrderId
                   app.placeOrder(order_id,usTechStk(ticker),marketOrder("BUY",quantity))
                   app.placeOrder(order_id+1,usTechStk(ticker),stopOrder("SELL",quantity,round(df["Close"][-1]-df["atr"][-1],1)))
                   
        elif len(pos_df.columns)!=0 and ticker in pos_df["Symbol"].tolist(): # Have open trade and ticker is already in open orders df
            if pos_df[pos_df["Symbol"]==ticker]["Position"].sort_values(ascending=True).values[-1] == 0:
                if df["macd"][-1]> df["signal"][-1] and \
                   df["stoch"][-1]> 30 and \
                   df["stoch"][-1] > df["stoch"][-2]:
                   app.reqIds(-1)
                   time.sleep(2)
                   order_id = app.nextValidOrderId
                   app.placeOrder(order_id,usTechStk(ticker),marketOrder("BUY",quantity))
                   app.placeOrder(order_id+1,usTechStk(ticker),stopOrder("SELL",quantity,round(df["Close"][-1]-df["atr"][-1],1)))
            elif pos_df[pos_df["Symbol"]==ticker]["Position"].sort_values(ascending=True).values[-1] > 0: # Cancel existing stoploss, and make a new one
                ord_id = ord_df[ord_df["Symbol"]==ticker]["OrderId"].sort_values(ascending=True).values[-1]
                old_quantity = pos_df[pos_df["Symbol"]==ticker]["Position"].sort_values(ascending=True).values[-1]
                app.cancelOrder(ord_id)
                app.reqIds(-1)
                time.sleep(2)
                order_id = app.nextValidOrderId
                app.placeOrder(order_id,usTechStk(ticker),stopOrder("SELL",old_quantity,round(df["Close"][-1]-df["atr"][-1],1)))

########## Iterative Excecution ##########

starttime = time.time()
timeout = time.time() + 60*60*10
while time.time() <= timeout:
    main()
    time.sleep(300 - ((time.time() - starttime) % 300))
