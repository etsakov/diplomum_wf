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
    trade_list = list()

    for trade in trades_data:
        open_datetime = datetime.strptime(trade['openTime'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
        trade_item_info = {
            'tradeID' : trade['id'],
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
            del(ask_rates[0])
            del(bid_rates[0])
        yield instant_rates, ask_rates, bid_rates


def iter_trades_pip_margin_indicator(stream_generator, trade_state):
    # Generates stream data with profit in pips by trade
    for rate in stream_generator:
        time_now = str(datetime.utcnow()).split('.')[0]
        print("Current time: ", time_now)
        ask_rate = float(rate['asks'][0]['price'])
        bid_rate =  float(rate['bids'][0]['price'])
        break

    if trade_state[-1]['currentUnits'] > 0:
        pip_profit_first_trade = bid_rate - trade_state[-1]['initial_price']
        pip_profit_last_trade = bid_rate - trade_state[0]['initial_price']
    else:
        pip_profit_first_trade = trade_state[-1]['initial_price'] - ask_rate
        pip_profit_last_trade = trade_state[0]['initial_price'] - ask_rate
    profit_in_pips = {
        'trade_amount' : trade_state[0]['currentUnits'],
        'first_trade' : float(format((pip_profit_first_trade) * 10000, '.1f')),
        'last_trade' : float(format((pip_profit_last_trade) * 10000, '.1f'))
    }
    return profit_in_pips


def shows_trade_units_available(ACCESS_TOKEN, ACCOUNT_ID):
    # Gives the amount of trade units still available for trade
    client = oandapyV20.API(access_token = ACCESS_TOKEN)
    account_statement = accounts.AccountDetails(ACCOUNT_ID)
    client.request(account_statement)
    units_available = format(float(account_statement.response["account"]["marginAvailable"]) / float(account_statement.response["account"]["marginRate"]), '.0f')
    return units_available


def make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, take_profit_price, direction):
    # Just trading engine for the usage in following functions
    data = {
            "order": {
            "timeInForce": "FOK",
            "instrument": INSTRUMENTS,
            "units": direction + units_quantity,  
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


def create_first_trade(ACCESS_TOKEN, ACCOUNT_ID, trade_units_available, structured_price_data, stream_generator, INSTRUMENTS):
    # Chooses direction for the first deal and makes the first trade
    print('trade_units_available: ', trade_units_available)
    # take_profit_price = 0
    for prices in structured_price_data:
        ask_prices = prices[1]
        bid_prices = prices[2]
        if len(ask_prices) < 5:
            print(len(ask_prices))
            print("Not enough data to choose the direction :((")
            continue

        last_five_prices = ask_prices[-5:]
        print('Las FIVE prices: ', last_five_prices)
        last_five_avg = float(format(mean(last_five_prices), '.5f'))
        print('Las FIVE average: ', last_five_avg)
        break

    for price in stream_generator:
        last_price_ask = float(price['asks'][0]['price'])
        print('ASK: ', last_price_ask)
        last_price_bid = float(price['bids'][0]['price'])
        print('BID: ', last_price_bid)
        break

 
    if last_price_ask > last_five_avg:
        direction = '-'
        take_profit_price = last_price_bid - 0.0001
        print('Go Short')
    else:
        direction = ''
        take_profit_price = last_price_ask + 0.0001
        print('Go Long')


    print('Take profit price: ', take_profit_price)
    units_quantity = str(int(trade_units_available) // 10)
    print('units_quantity: ', units_quantity)
    take_profit_price = format(take_profit_price, '.5f')
    print('Take profit price: ', take_profit_price)
    make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, take_profit_price, direction)
    print('The initial order has been put. Good luck!')
        

def following_trades_creator(ACCESS_TOKEN, ACCOUNT_ID, trade_state, profit_in_pips, trade_units_available, stream_generator, INSTRUMENTS):
    # Once the initial trade is open makes further trades
    for price in stream_generator:
        ask_rate = float(price['asks'][0]['price'])
        bid_rate = float(price['bids'][0]['price'])
        break
    number_of_tr_items = len(trade_state)
    trade_amount = profit_in_pips['trade_amount']
    first_trade_profit = profit_in_pips['first_trade']
    last_trade_profit = profit_in_pips['last_trade']
    print('We currently have ', len(trade_state), ' active trade(s).')
    print('Last trade amount: ', trade_amount)
    print('Unrealized profit for the first trade: ', first_trade_profit)
    print('Current ASK rate: ', format(ask_rate, '.5f'))
    print('Current BID rate: ', format(bid_rate, '.5f'))
    print('Trade units left: ', trade_units_available)

    if int(trade_units_available) < abs(int(trade_amount * 0.92)):
        print('Les jeux sont faits! Rien ne va plus.')
        return
    else:
        print('Money still available')
    take_profit_price = 0
    if first_trade_profit <= (-2 * number_of_tr_items) and last_trade_profit <= -2 and trade_amount > 0:
        take_profit_price = ask_rate + 0.0001
    elif first_trade_profit <= (-2 * number_of_tr_items) and last_trade_profit <= -2 and trade_amount <= 0:
        take_profit_price = bid_rate - 0.0001
    elif last_trade_profit >= 2 and trade_amount > 0:
        take_profit_price = ask_rate + 0.0001
    elif last_trade_profit >= 2 and trade_amount <= 0:
        take_profit_price = bid_rate - 0.0001
    else:
        pass
    
    if take_profit_price == 0:
        print('No need for another trade')
        pass
    else:
        print('Take Profit condition: ', take_profit_price)
        units_quantity = str(int(trade_amount * 0.92))
        take_profit_price = format(take_profit_price, '.5f')
        print('TRADE SUPPOSED TO BE MADE')
        direction = ''
        make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, take_profit_price, direction)
        pass

if __name__=="__main__":
    stream_generator = stream_rates_generator(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS)
    structured_price_data = read_stream_data_generator(stream_generator)

    while True:
        trade_state = fetch_trades_info(ACCESS_TOKEN, ACCOUNT_ID)
        trade_units_available = shows_trade_units_available(ACCESS_TOKEN, ACCOUNT_ID)
        if len(trade_state) == 0:
            print('*******************************************')
            print('Trade units available: ', trade_units_available)
            create_first_trade(ACCESS_TOKEN, ACCOUNT_ID, trade_units_available, structured_price_data, stream_generator, INSTRUMENTS)
            print('*******************************************')
            time.sleep(1)
            pass
        else:
            print('*******************************************')
            trade_state
            trade_units_available
            profit_in_pips = iter_trades_pip_margin_indicator(stream_generator, trade_state)
            print('Profit in PIPs for the FIRST trade: ', profit_in_pips['first_trade'])
            print('Profit in PIPs for the LAST trade: ', profit_in_pips['last_trade'])
            following_trades_creator(ACCESS_TOKEN, ACCOUNT_ID, trade_state, profit_in_pips, trade_units_available, stream_generator, INSTRUMENTS)
            print('I am active. The fund is working. Relax!')
            print('*******************************************')
            pass