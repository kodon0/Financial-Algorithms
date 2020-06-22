#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 11 15:39:10 2020

@author: kieranodonnell
"""


import numpy as np
import time

#Fibbo

def fibonacci(n):
    if n <=1:
        return n
    else:
        return (fibonacci(n-1)+fibonacci(n-2))

#Main
def main():
    num = np.random.randint(1,25)
    print("{}th fibonacci number is : {}".format(num,fibonacci(num)))
    
#Continuous exectution
    
starttime = time.time()
timeout = time.time() + 60*2 #I.e. two minutes duration

while time.time() <= timeout:
    
    try:
        main()
        time.sleep(5 - ((time.time()-starttime)% 5.0))
    except KeyboardInterrupt:
        print("\n' Keyboard interrupt found - Exiting...")
        exit()