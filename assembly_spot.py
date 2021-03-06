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
import ast
import matplotlib.pyplot as plt
import numpy as np 
from sklearn.svm import SVR
from statistics import mean
import re

def fetch_quasi_trades_info(ACCESS_TOKEN, ACCOUNT_ID):
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
            'state' : trade['state'],
            'instrument' : trade['instrument'],
            'open_time' : datetime.strftime(open_datetime, '%Y-%m-%dT%H:%M:%SZ'),
            'currentUnits' : int(trade['currentUnits']),
            'initial_price' : float(trade['price']),
            'take_profit_price' : float(trade['takeProfitOrder']['price']),
            'take_profit_pips' : format((float(trade['takeProfitOrder']['price']) - float(trade['price'])) * 10000, '.1f'),
            'unrealized_PL' : float(trade['unrealizedPL']),
            'financing' : float(trade['financing']),
        }
        trade_list.append(trade_item_info)

    return trade_list


# def quasi_stream_trades_info_generator(ACCESS_TOKEN, ACCOUNT_ID):
#     while True:
#         yield fetch_quasi_trades_info(ACCESS_TOKEN, ACCOUNT_ID)


def stream_rates_generator(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS):
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
                yield response
            # else:
            #     print('HEARTBEAT')
            #     pass


def read_stream_data_generator(stream_generator):
    # Interprets the raw rate stream info to the stream of operable instances
    ask_rates = list()
    bid_rates = list()

    for rate in stream_generator:
        if rate['type'] != 'PRICE':
            print(">>> No data available <<<")
            continue

        instant_time = datetime.strptime(rate['time'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
        instant_rates = {
            'time' : datetime.strftime(instant_time, '%d.%m.%Y %H:%M:%S'),
            'status' : rate['status'],
            'ask' : float(rate['asks'][0]['price']),
            'bid' : float(rate['bids'][0]['price']),
            'spread' : float('%.5f' % (float(rate['asks'][0]['price']) - float(rate['bids'][0]['price']))),
        }
        
        ask_rates.append(float(rate['asks'][0]['price']))
        bid_rates.append(float(rate['bids'][0]['price']))

        if len(ask_rates) == 151:
            print('TO DELETE from analysed ASK list:', ask_rates[0])
            print('TO DELETE from analysed BID list:', bid_rates[0])
            del(ask_rates[0])
            del(bid_rates[0])
            
        yield instant_rates, ask_rates, bid_rates


def iter_trades_pip_margin_indicator(stream_generator, trade_state):
    # Generates stream data with profit in pips by trade
    for rate in stream_generator:
        # print(rate)
        # time.sleep(1)
        time_now = str(datetime.utcnow()).split('.')[0]
        print("Current time: ", time_now)
        ask_rate = float(rate['asks'][0]['price'])
        bid_rate =  float(rate['bids'][0]['price'])
        # print('ask_rate: ', ask_rate)
        # print('bid_rate: ', bid_rate)
        break

    if trade_state[0]['currentUnits'] > 0:
        pip_profit_by_trade = bid_rate - trade_state[0]['initial_price']
    else:
        pip_profit_by_trade = trade_state[0]['initial_price'] - ask_rate
    profit_in_pips = {
        'trade_amount' : trade_state[0]['currentUnits'],
        'last_trade' : float(format((pip_profit_by_trade) * 10000, '.1f'))
    }
    # print('Profit in PIPs for the last trade: ', profit_in_pips['last_trade'])
    return profit_in_pips


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


def sleep_sweet():
    # Regulates the timing for the programm
    # Script doesn't support timezones for now!!!
    time_now_mow = datetime.now()
    today = date.today()
    close_time = today+relativedelta(weekday=FR, hour=23, minutes=59)
    open_time = today+relativedelta(weekday=MO, minutes=1)
    next_start_trading_time = today+relativedelta(weekday=MO, hour=1)

    if time_now_mow < open_time:
        close_time = today+relativedelta(weeks=-1, weekday=FR, hour=23, minutes=59)
    elif time_now_mow < next_start_trading_time:
        open_time = today+relativedelta(weeks=-1, weekday=MO, minutes=1)

    if close_time < time_now_mow and time_now_mow < open_time:
        command = 'SLEEP'
    elif open_time < time_now_mow and time_now_mow < next_start_trading_time:
        command = 'COLLECT'
    else:
        command = 'WORK'
        return command

    print('Time now MOW: ', str(time_now_mow).split('.')[0])
    print('Close time ', close_time)
    print('Open time ', open_time)
    print('Start_trading_time ', next_start_trading_time)
    print('Command: ', command)
    return command


def create_first_trade(ACCESS_TOKEN, ACCOUNT_ID, trade_units_available, structured_price_data, INSTRUMENTS):
    # Chooses direction for the first deal and makes the first trade
    print('trade_units_available: ', trade_units_available)
    # take_profit_price = 0
    for prices in structured_price_data:
        ask_prices = prices[1]
        bid_prices = prices[2]
        # take_profit_price = 0
        if len(ask_prices) < 5:
            print(len(ask_prices))
            print("Not enough data to choose the direction :((")
            continue
        last_price_ask = float(ask_prices[-1])
        last_price_bid = float(bid_prices[-1])
        last_five_prices = ask_prices[-5:]
        last_five_avg = float(format(mean(last_five_prices), '.5f'))
        print('Last price ASK: ', last_price_ask)
        print('Last price BID: ', last_price_bid)
        print('Las FIVE average: ', last_five_avg)
        
        if last_price_ask < last_five_avg:
            # go short
            direction = '-'
            take_profit_price = last_price_bid - 0.0003
            print('Go Short')
        else:
            # go long
            direction = ''
            take_profit_price = last_price_ask + 0.0003
            print('Go Long')

        print('Direction: ', direction)
        print('Take profit price: ', take_profit_price)
        units_quantity = str(int(trade_units_available) // 10)
        print('units_quantity: ', units_quantity)
        take_profit_price = format(take_profit_price, '.5f')
        print('Take profit price: ', take_profit_price)
        make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, take_profit_price)
        print('The initial order has been put. Good luck!')
        break

def following_trades_creator(ACCESS_TOKEN, ACCOUNT_ID, trade_state, profit_in_pips, trade_units_available, stream_generator, INSTRUMENTS):
    # Once the initial trade is open makes further trades
    for prices in stream_generator:
        ask_rate = float(prices[0]['ask'])
        bid_rate = float(prices[0]['bid'])
        break
    number_of_tr_items = len(trade_state)
    trade_amount = profit_in_pips['trade_amount']
    trade_profit = profit_in_pips['last_trade']
    print('We currently have ', len(trade_state), ' active trade(s).')
    print('Last trade amount: ', trade_amount)
    print('Unrealized profit for the last trade: ', trade_profit)
    print('Current ASK rate: ', format(ask_rate, '.5f'))
    print('Current BID rate: ', format(bid_rate, '.5f'))
    print('Trade units left: ', trade_units_available)

    if int(trade_units_available) < abs(trade_amount):
        print('Les jeux sont faits! Rien ne va plus.')
        return
    else:
        print('Money still available')
    take_profit_price = 0
    if trade_profit <= -3 and trade_amount > 0:
        take_profit_price = ask_rate + 0.0001
    elif trade_profit <= -3 and trade_amount <= 0:
        take_profit_price = bid_rate - 0.0001
    elif trade_profit >= 1 and trade_amount > 0:
        take_profit_price = ask_rate + 0.0001
    elif trade_profit >= 1 and trade_amount <= 0:
        take_profit_price = bid_rate - 0.0001
    else:
        pass

    print('Take Profit condition: ', take_profit_price)
    if take_profit_price == 0:
        print('Not sufficient margine for another support trade')
        pass
    else:
        units_quantity = str(trade_amount)
        take_profit_price = format(take_profit_price, '.5f')
        print('TRADE SUPPOSED TO BE MADE')
        make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, take_profit_price)
        pass

if __name__=="__main__":
    # trade_state = fetch_quasi_trades_info(ACCESS_TOKEN, ACCOUNT_ID)
    # trade_state_stream = quasi_stream_trades_info_generator(ACCESS_TOKEN, ACCOUNT_ID)
    stream_generator = stream_rates_generator(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS)
    structured_price_data = read_stream_data_generator(stream_generator)
    # profit_in_pips = iter_trades_pip_margin_indicator(stream_generator, trade_state)
    # trade_units_available = shows_trade_units_available(ACCESS_TOKEN, ACCOUNT_ID)
    # for i in structured_price_data:
    #     print(i)
    
    # following_trades_creator(ACCESS_TOKEN, ACCOUNT_ID, trade_state, profit_in_pips, trade_units_available, structured_price_data, INSTRUMENTS)

    while True:
        if sleep_sweet() == 'SLEEP':
            time.sleep(5)
            pass
        elif sleep_sweet() == 'COLLECT':
            # stream_generator
            structured_price_data
            time.sleep(5)
        elif sleep_sweet() == 'WORK':
            trade_state = fetch_quasi_trades_info(ACCESS_TOKEN, ACCOUNT_ID)
            trade_units_available = shows_trade_units_available(ACCESS_TOKEN, ACCOUNT_ID)
            # for h in trade_state:
            if len(trade_state) == 0:
                print('*******************************************')
                print('Trade units available: ', trade_units_available)
                create_first_trade(ACCESS_TOKEN, ACCOUNT_ID, trade_units_available, structured_price_data, INSTRUMENTS)
                print('*******************************************')
                time.sleep(1)
                pass
            else:
                print('*******************************************')
                trade_state
                trade_units_available
                # print('trade_state', trade_state)
                profit_in_pips = iter_trades_pip_margin_indicator(stream_generator, trade_state)
                # print('profit_in_pips', profit_in_pips)
                # print('trade_units_available', trade_units_available)
                following_trades_creator(ACCESS_TOKEN, ACCOUNT_ID, trade_state, profit_in_pips, trade_units_available, structured_price_data, INSTRUMENTS)
                print('I am active. The fund is working. Relax!')
                print('*******************************************')
                pass
        else:
            print('The Schedule machine is broken')
    # TIME NOW?? datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%SZ')