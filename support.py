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
            'tradeID' : trade['takeProfitOrder']['tradeID'],
            'open_time' : open_datetime,
            'currentUnits' : int(trade['currentUnits']),
            'take_profit_price' : float(trade['takeProfitOrder']['price']),
            # 'unrealized_PL' : float(trade['unrealizedPL']),
            # 'financing' : float(trade['financing']),
            'net_profit' : float(trade['unrealizedPL']) + float(trade['financing']),
            'comment' : trade['clientExtensions']['comment']
            # 'trade_status' : 'suspended'
        }
        if datetime.now() - timedelta(hours=60) > open_datetime:
            trade_item_info['trade_status'] = 'suspended'
        else:
            trade_item_info['trade_status'] = 'fresh'
        trade_list.append(trade_item_info)

    return trade_list


def shows_trade_units_available(ACCESS_TOKEN, ACCOUNT_ID):
    # Gives the amount of trade units still available for trade
    client = oandapyV20.API(access_token = ACCESS_TOKEN)
    account_statement = accounts.AccountDetails(ACCOUNT_ID)
    client.request(account_statement)
    units_available = format(float(account_statement.response["account"]["marginAvailable"]) / float(account_statement.response["account"]["marginRate"]), '.0f')
    return units_available


def make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity):
    # Just trading engine for the usage in following functions
    data = {
            "order": {
            "timeInForce": "FOK",
            "instrument": INSTRUMENTS,
            "units": units_quantity,  
            "type": "MARKET",
            "positionFill": "DEFAULT",
            "clientExtensions": {
                "comment": "SUPPORT"
            }
            # "takeProfitOnFill": {
            #     "timeInForce": "GTC",
            #     "price": take_profit_price
            # }
        }
    }

    client = oandapyV20.API(access_token = ACCESS_TOKEN)
    r = orders.OrderCreate(accountID = ACCOUNT_ID, data = data)
    rv = client.request(r)
    print(r.response)


def transactions_close(ACCESS_TOKEN, ACCOUNT_ID, units_quantity, trade_id):
    # Close a trade according to its id and quantity of units
    client = oandapyV20.API(access_token = ACCESS_TOKEN)
    data = {
        "units" : units_quantity
    }

    r = trades.TradeClose(accountID = ACCOUNT_ID, data = data, tradeID = trade_id)
    client.request(r)
    print(r.response)


def get_support_trades(trades_info, units_available):
    # Describes logics for the support trades
    for suspended_trade in trades_info:
        if suspended_trade['trade_status'] == 'suspended':
            count_down = 4
            while count_down != 0 and suspended_trade['currentUnits'] < units_available:
                units_quantity = suspended_trade['currentUnits']
                make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity)
                count_down -= 1
        else:
            pass


def merge_trades(trades_info):
    # Creates the joint list for suspended and support trades
    suspended_and_support_trades = list()
    for suspended_trade in trades_info:
        if suspended_trade['trade_status'] == 'suspended' or suspended_trade['trade_status'] == 'SUPPORT':
            suspended_and_support_trades.append(suspended_trade)

    return suspended_and_support_trades


def count_overall_sum(suspended_and_support_trades):
    # Counts the overall sum for this trades
    overall_sum = 0
    for value in suspended_and_support_trades:
        overall_sum += value['net_profit']
    return overall_sum


if __name__ == "__main__":
    trades_info = fetch_trades_info(ACCESS_TOKEN, ACCOUNT_ID)
    units_available = shows_trade_units_available(ACCESS_TOKEN, ACCOUNT_ID)
    create_support_trades = get_support_trades(trades_info, units_available)
    suspended_and_support_trades = merge_trades(trades_info)
    suspend_support_level = count_overall_sum(suspended_and_support_trades)
    print('TRADES INFO', trades_info)
    print('UNITS AVAILABLE: ', units_available)
    trades_info
    units_available
    create_support_trades
    # Lear how to make a particular amount of trades!!!
    while True:
        suspended_and_support_trades
        suspend_support_level
        print('SUSPENDED AND SUPPORT: ', suspended_and_support_trades)
        print('SUSPEND/SUPPORT LEVEL: ', suspend_support_level)
        if suspend_support_level > 0:
            for item in suspended_and_support_trades:
                units_quantity = item['currentUnits']
                trade_id = item['tradeID']
                transactions_close(ACCESS_TOKEN, ACCOUNT_ID, units_quantity, trade_id)
    # print(datetime.now() - trades_info[0]['open_time'])

