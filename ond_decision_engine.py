import requests
import json
from config import ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS
from oandapyV20 import API
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np 
from sklearn import linear_model


def get_raw_data(td, granularity):
    # Function gets the historical data for td-period till now
    time_now = datetime.utcnow()
    starting_time = time_now - td
    _from = starting_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    _to = time_now.strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
        "from": _from,
        "to": _to,
        "granularity": granularity,
    }

    for r in InstrumentsCandlesFactory(instrument=instrument, params=params):
        client.request(r)
        timeframe_price_data = r.response.get('candles')
        return timeframe_price_data

def prepare_the_data(timeframe_price_data):
    # Makes several lists of instances for future usage
    x_dates = list()
    y_prices = list()

    item = 0
    for row in timeframe_price_data:

        x_dates.append(int(timeframe_price_data[item]['time'].split('.')[0].split('T')[1].replace(':', '')))
        y_prices.append(float(timeframe_price_data[item]['mid']['c']))
        item += 1
        
    return x_dates, y_prices

def linear_prediction(x, y):
    

if __name__=='__main__':
    client = API(access_token = ACCESS_TOKEN)
    instrument = INSTRUMENTS
    granularity = "S5"
    td = timedelta(hours=1)
    timeframe_price_data = get_raw_data(td, granularity)
    x = prepare_the_data(timeframe_price_data)[0]
    y = prepare_the_data(timeframe_price_data)[1]
    
    # i = 0
    # for item in x:
    #     print(type(x[i]), '' , type(y[i]))
    #     i += 1

    linear_prediction(x, y)
