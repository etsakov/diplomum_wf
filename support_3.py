import json
import requests
import oandapyV20
from oandapyV20 import API
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.accounts as accounts
from config import ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS
from collections import deque
from datetime import date, datetime, timedelta
from dateutil.relativedelta import *
import calendar
import time

set_target = 5 #Total sum in EUR when close all trades
unit = 'EUR'

def fetch_trades_info(ACCESS_TOKEN, ACCOUNT_ID):
    # Provides a current state for transactions
    api = API(access_token = ACCESS_TOKEN)
    r = trades.TradesList(ACCOUNT_ID)
    trades_full_info = api.request(r)
    trades_data = trades_full_info['trades']

    trade_list = list()
    for trade in trades_data:
        open_datetime = datetime.strptime(trade['openTime'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
        trade_item_info = {
            'tradeID' : trade['id'],
            'open_time' : open_datetime,
            'currentUnits' : int(trade['currentUnits']),
            'trade_price' : float(trade['price']),
            'net_profit' : float(trade['unrealizedPL']) + float(trade['financing']),
        }
        trade_list.append(trade_item_info)
    return trade_list


def transactions_close(ACCESS_TOKEN, ACCOUNT_ID, units_quantity, trade_id):
    # Close a trade according to its id and quantity of units
    client = oandapyV20.API(access_token = ACCESS_TOKEN)
    data = {
        "units" : units_quantity
    }

    r = trades.TradeClose(accountID = ACCOUNT_ID, data = data, tradeID = trade_id)
    client.request(r)
    print(r.response)


def count_overall_sum(trades_info):
    # Counts the overall sum for this trades
    overall_sum = 0
    for value in trades_info:
        overall_sum += value['net_profit']
    return overall_sum


if __name__=="__main__":
    while True:
        trades_info = fetch_trades_info(ACCESS_TOKEN, ACCOUNT_ID)
        target_level = count_overall_sum(trades_info)
        print(datetime.now())
        print('Sum for ALL open trades: ', format(target_level, '.5f'))
        if target_level > set_target:
            print('******************************')
            for trade in trades_info:
                
                print('ITEM: ', trade)
                units_quantity = str(trade['currentUnits']).replace('-', '')
                print(type(units_quantity))
                trade_id = trade['tradeID']
                # transactions_close(ACCESS_TOKEN, ACCOUNT_ID, units_quantity, trade_id)
            print('******************************')
            print('!!!ALL TRANSACTIONS CLOSED!!!')
            print('******************************\n\n')        
        else:
            print('Target sum of ' + str(set_target) + ' ' + unit + ' not acheeved.\n\n')
        time.sleep(2)
