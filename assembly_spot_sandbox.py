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

def quasi_stream_trades_info_generator(ACCESS_TOKEN, ACCOUNT_ID):
    # Generates a stream of current transactions info and converts it into the operable lists
    api = API(access_token = ACCESS_TOKEN)
    r = trades.TradesList(ACCOUNT_ID)

    while True:
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

        yield trade_list


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
            yield json.loads(decoded_line)


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


def iter_trades_pip_margin_indicator(stream_generator, structured_price_data, trades_stream_data):
    # Generates stream data with profit in pips by trade
    for rate in structured_price_data:
        time_now = str(datetime.utcnow()).split('.')[0]
        print("Current time: ", time_now)
        ask_rate = float(rate[0]['ask'])
        bid_rate =  float(rate[0]['bid'])

        
        for trades_list in trades_stream_data:
            number_of_tr_items = len(trades_list)
            break
        tr_item = 0
        trades_profits = list()
        for trade_price in trades_stream_data:
            if trade_price[tr_item]['currentUnits'] > 0:
                pip_profit_by_trade = bid_rate - trade_price[tr_item]['initial_price']
            else:
                pip_profit_by_trade = trade_price[tr_item]['initial_price'] - ask_rate
            profit_in_pips = {
                'trade_amount' : trade_price[tr_item]['currentUnits'],
                'trade_' + str(number_of_tr_items - tr_item) : float(format((pip_profit_by_trade) * 10000, '.1f'))
            }
            trades_profits.append(profit_in_pips)
            tr_item += 1
            break
        yield trades_profits


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


def create_first_trade(ACCESS_TOKEN, ACCOUNT_ID, trade_units_available, structured_price_data, INSTRUMENTS):
    # Chooses direction for the first deal and makes the first trade
    print('trade_units_available: ', trade_units_available)
    for prices in structured_price_data:
        ask_prices = prices[1]
        if len(ask_prices) < 5:
            print("Not enough data to choose the direction :((")
            continue

        last_price = float(ask_prices[-1])
        last_five_prices = ask_prices[-5:]
        last_five_avg = float(format(mean(last_five_prices), '.5f'))
        if last_price < last_five_avg:
            # go short
            direction = '-'
            take_profit_price = last_price - 0.0003
            print('Go Short')
        else:
            # go long
            direction = ''
            take_profit_price = last_price + 0.0003
            print('Go Long')

        print('direction: ', direction)
        print('take_profit_price: ', take_profit_price)
        break

    take_profit_price_str = format(take_profit_price, '.5f')
    amount_of_units = int(trade_units_available) // 10
    units_quantity = amount_of_units
    make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, take_profit_price_str)


def following_trades_creator(ACCESS_TOKEN, ACCOUNT_ID, trades_stream_data, profit_in_pips, trade_units_available, structured_price_data, INSTRUMENTS):
    # Once the initial trade is open makes further trades
    
    for curent_trade_state in trades_stream_data:
        number_of_tr_items = len(curent_trade_state)
        print('We currently have ', len(curent_trade_state), ' active trade(s).')
        break

    for trade in profit_in_pips:
    # trade = next(profit_in_pips)
        trade_amount = 0
        trade_profit = 0
        trade_amount = trade[0]['trade_amount']
        trade_profit = trade[0]['trade_' + str(number_of_tr_items)]
        print('Last trade amount: ', trade_amount)
        print('Unrealized profit for the last trade: ', trade_profit)
        break

    for prices in structured_price_data:
    # prices = next(structured_price_data)
        ask_rate = prices[1][-1]
        bid_rate = prices[2][-1]
        print('Current ASK rate: ', ask_rate)
        print('Current BID rate: ', bid_rate)
        print('Trade units left: ', trade_units_available)
        break

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

    if take_profit_price == 0:
        print('Not sufficient margine for a support trade')
        pass
    else:
        make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, str(trade_amount), format(take_profit_price, '.5f'))


def sleep_sweet():
    # Regulates the timing for the programm
    time_now_mow = datetime.now()
    today = date.today()
    next_close_time = today+relativedelta(weekday=FR, hour=23, minutes=59)
    next_open_time = today+relativedelta(weekday=MO, minutes=1)
    next_start_trading_time = today+relativedelta(weekday=MO, hour=1)

    if next_close_time < time_now_mow and time_now_mow < next_open_time:
        command = 'SLEEP'
    elif next_open_time < time_now_mow and time_now_mow < next_start_trading_time:
        command = 'COLLECT'
    else:
        command = 'WORK'

    yield command
    time.sleep(3)


if __name__=="__main__":
    # trade_state = fetch_quasi_trades_info(ACCESS_TOKEN, ACCOUNT_ID)
    trades_stream_data = quasi_stream_trades_info_generator(ACCESS_TOKEN, ACCOUNT_ID)
    stream_generator = stream_rates_generator(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS)
    structured_price_data = read_stream_data_generator(stream_generator)
    profit_in_pips = iter_trades_pip_margin_indicator(stream_generator, structured_price_data, trades_stream_data)
    
    
    # for i in profit_in_pips:
    #     print('length profit_in_pips: ', len(i))
    #     print(i)
    # following_trades_creator(ACCESS_TOKEN, ACCOUNT_ID, trades_stream_data, profit_in_pips, trade_units_available, structured_price_data, INSTRUMENTS)

    for h in trades_stream_data:
        if len(h) == 0:
            print('*******************************************')
            create_first_trade(ACCESS_TOKEN, ACCOUNT_ID, trade_units_available, structured_price_data, INSTRUMENTS)
            print('The initial order has been put. Good luck!')
            print('*******************************************')
            time.sleep(1)
            continue
        else:
            print('*******************************************')
            trade_units_available = shows_trade_units_available(ACCESS_TOKEN, ACCOUNT_ID)
            following_trades_creator(ACCESS_TOKEN, ACCOUNT_ID, trades_stream_data, profit_in_pips, trade_units_available, structured_price_data, INSTRUMENTS)
            print('I am active. The fund is working. Relax!')
            print('*******************************************')
            pass
    # TIME NOW?? datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%SZ')