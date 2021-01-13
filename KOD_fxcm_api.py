#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 12 14:56:11 2020

@author: kieranodonnell
"""

#Import libraries

import fxcmpy
import socketio
import time

#Connect API and define trade parameters

token_path = "path"
con = fxcmpy.fxcmpy(access_token = open(token_path, 'r').read(), log_level = 'error', server = 'demo')

pair = "EUR/USD"

#Get histroy data
data = con.get_candles(pair, period='m5', number=250)

#Periods can be m1, m5, m15, m30, H1, H2.....H8, D1, W1, M1

'''This section allows for real time data streaming'''
#streaming data - first need to subscribe to a currency pair
con.subscribe_market_data("EUR/USD")
con.get_last_price("EUR/USD")
con.get_prices("EUR/USD")
con.unsubscribe_market_data("EUR/USD")

#Using time recursion for continuous exectution

starttime = time.time()
timeout = time.time() + 60*2*0.2 #I.e. two minutes duration

while time.time() <= timeout:
    print(con.get_last_price("EUR/USD")[0])
    #Make sure to unsub after!

#Get account info and account data
    #Use transpose to view df
con.get_accounts().T
con.get_open_positions().T
con.get_open_positions_summary().T
con.get_closed_positions()
con.get_orders()


#Dealing with new orders
#Running these will make them appear on the web
con.create_market_sell_order("EUR/USD", 1)
con.create_market_buy_order("EUR/USD", 1)


#Can also do it with much more detail:
order = con.open_trade("EUR/USD", is_buy=True,
                       is_in_pips=False,
                       amount=1,time_in_force = 'GTC',
                       stop=1.08, trailing_step=True,
                       order_type="AtMarket", limit=1.45)

con.close_trade(trade_id,1000)#This needs trade ID which is a pain
con.close_all_for_symbol("EUR/USD")#This is better

con.close()#Always close when done
