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
            'tradeID' : trade['id'],
            'open_time' : open_datetime,
            'currentUnits' : int(trade['currentUnits']),
            'trade_price' : float(trade['price']),
            # 'take_profit_price' : float(trade['takeProfitOrder']['price']),
            # 'unrealized_PL' : float(trade['unrealizedPL']),
            # 'financing' : float(trade['financing']),
            'net_profit' : float(trade['unrealizedPL']) + float(trade['financing']),
            # 'comment' : trade['clientExtensions']['comment']
            # 'trade_status' : 'suspended'
        }
        if datetime.now() - timedelta(hours=60) > open_datetime:
            trade_item_info['trade_status'] = 'suspended'
        else:
            trade_item_info['trade_status'] = 'fresh'
        trade_list.append(trade_item_info)
    return trade_list


def get_suspended_trades_list(trades_info):
    # Creates the joint list for suspended and support trades
    suspended_trades = list()
    for suspended_trade in trades_info:
        if suspended_trade['trade_status'] == 'suspended':
            suspended_trades.append(suspended_trade)
    return suspended_trades


def get_market_rates(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS):
    # Connects to the rate stream and re-generates rate in a stream
    url = 'https://stream-fxpractice.oanda.com/v3/accounts/' + ACCOUNT_ID + '/pricing/stream'
    params = {
        'instruments': INSTRUMENTS,
    }
    head = {'Content-type':"application/json",
            'Accept-Datetime-Format':"RFC3339",
            'Authorization':"Bearer " + ACCESS_TOKEN}

    r = requests.get(url, params = params, headers = head, stream = True)
    for line in r.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            response = json.loads(decoded_line)
            if response['type'] != 'HEARTBEAT':
                return response


def shows_trade_units_available(ACCESS_TOKEN, ACCOUNT_ID):
    # Gives the amount of trade units still available for trade
    client = oandapyV20.API(access_token = ACCESS_TOKEN)
    account_statement = accounts.AccountDetails(ACCOUNT_ID)
    client.request(account_statement)
    units_available = format(float(account_statement.response["account"]["marginAvailable"]) / float(account_statement.response["account"]["marginRate"]), '.0f')
    return units_available


def make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, take_profit_price):
    # Just trading engine for the usage in following functions
    data = {
            "order": {
            "timeInForce": "FOK",
            "instrument": INSTRUMENTS,
            "units": units_quantity,  
            "type": "MARKET",
            "positionFill": "DEFAULT",
            # "clientExtensions": {
            #     "comment": "SUPPORT"
            # }
            "takeProfitOnFill": {
                "timeInForce": "GTC",
                "price": take_profit_price
            }
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


def get_support_trades(suspended_trades, units_available, market_rates):
    # Describes logics for the support trades

    if len(suspended_trades) > 0:
        count_down = 4
        while count_down != 0 and suspended_trades[-1]['currentUnits'] > int(units_available):
            units_quantity = suspended_trades[-1]['currentUnits']
            if units_quantity > 0:
                ask_rate = market_rates['asks'][0]['price']
                take_profit_price = ask_rate + 0.0050
            else:
                ask_rate = market_rates['bids'][0]['price']
                take_profit_price = bid_rate - 0.0050
             
            make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, take_profit_price)
            count_down -= 1
    else:
        pass


def count_overall_sum(trades_info):
    # Counts the overall sum for this trades
    overall_sum = 0
    for value in trades_info:
        overall_sum += value['net_profit']
    return overall_sum


if __name__=="__main__":
    while True:
        trades_info = fetch_trades_info(ACCESS_TOKEN, ACCOUNT_ID)
        suspended_trades = get_suspended_trades_list(trades_info)
        # print(suspended_trades[-1]) - data for the first trade in list
        market_rates = get_market_rates(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS)
        units_available = shows_trade_units_available(ACCESS_TOKEN, ACCOUNT_ID)
        get_support_trades(suspended_trades, units_available, market_rates)
        support_level = count_overall_sum(trades_info)
        print(datetime.now())
        print('Sum for ALL open trades: ', format(support_level, '.5f'))
        if len(suspended_trades) > 0 and support_level > 0:
            for trade in trades_info:
                print('******************************')
                print('ITEM: ', trade)
                units_quantity = str(trade['currentUnits']).replace('-', '')
                print(type(units_quantity))
                trade_id = trade['tradeID']
                transactions_close(ACCESS_TOKEN, ACCOUNT_ID, units_quantity, trade_id)
                print('!!!ALL TRANSACTIONS CLOSED!!!')
                print('******************************\n\n')
        elif len(suspended_trades) > 0 and support_level < 0:
            print('Not sufficient support level for suspended trades.\n\n')
        elif len(suspended_trades) == 0:
            print('No suspended trades for now.\n\n')
        else:
            pass
        # time.sleep(2)

