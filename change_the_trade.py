import json
import requests
import oandapyV20
from oandapyV20 import API
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.accounts as accounts
from config import ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS
from datetime import date, datetime, timedelta
from dateutil.relativedelta import *
import calendar
import time
from statistics import mean
import re


def fetch_trades_info(ACCESS_TOKEN, ACCOUNT_ID):
    # Provides a current state for transactions
    api = API(access_token = ACCESS_TOKEN)
    r = trades.TradesList(ACCOUNT_ID)

    trades_full_info = api.request(r)
    trades_data = trades_full_info['trades']

    return trades_data


def change_the_trade(ACCESS_TOKEN, ACCOUNT_ID, trade_state):
    # Sets take_profit_price condition over the newly opened trade
    
    # print(trade_state[0])
    tradeID = trade_state[0]['id']
    # print('TRADE ID (__): ', tradeID)
    # print('PRICE (___): ', trade_state[0]['price'])
    take_profit_price = 0
    if int(trade_state[0]['initialUnits']) > 0:
        take_profit_price = str(float(trade_state[0]['price']) + 0.0001)
        # take_profit_price = trade_state[0]['price'] + 0.0001 * number_of_tr_items
    elif int(trade_state[0]['initialUnits']) < 0:
        take_profit_price = str(float(trade_state[0]['price']) - 0.0001)
    else:
        print('!!! SOMETHING WENT WRONG IN change_the_trade FUNCTION !!!')
        pass

    data = {
        'takeProfit': {
            'timeInForce': 'GTC',
            'price': take_profit_price
        }
    }

    client = oandapyV20.API(access_token = ACCESS_TOKEN)
    r = trades.TradeCRCDO(accountID = ACCOUNT_ID, tradeID=tradeID, data = data)
    client.request(r)
    print(r.response)
    print('TAKE PROFIT PRICE: ', take_profit_price)