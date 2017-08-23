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

# TO DO - find out what is os.execl(sys.executable, sys.executable, *sys.argv)
# https://blog.petrzemek.net/2014/03/23/restarting-a-python-script-within-itself/
# https://stackoverflow.com/a/30247200


def fetch_trades_info(ACCESS_TOKEN, ACCOUNT_ID):
    # Provides a current state for transactions
    api = API(access_token = ACCESS_TOKEN)
    r = trades.TradesList(ACCOUNT_ID)

    trades_full_info = api.request(r)
    trades_data = trades_full_info['trades']

    return trades_data


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

        # instant_time = datetime.strptime(rate['time'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
        # print('STATE TIME: ', instant_time)
        instant_rates = {
            # 'time' : datetime.strftime(instant_time, '%d.%m.%Y %H:%M:%S'),
            # 'status' : rate['status'],
            'ask' : float(rate['asks'][0]['price']),
            'bid' : float(rate['bids'][0]['price'])
            # 'spread' : float('%.5f' % (float(rate['asks'][0]['price']) - float(rate['bids'][0]['price']))),
        }
        
        ask_rates.append(float(rate['asks'][0]['price']))
        bid_rates.append(float(rate['bids'][0]['price']))

        if len(ask_rates) == 51:
            del(ask_rates[0])
            del(bid_rates[0])
            
        yield instant_rates, ask_rates, bid_rates


def shows_trade_units_available(ACCESS_TOKEN, ACCOUNT_ID):
    # Gives the amount of trade units still available for trade
    client = oandapyV20.API(access_token = ACCESS_TOKEN)
    account_statement = accounts.AccountDetails(ACCOUNT_ID)
    client.request(account_statement)
    units_available = format(float(account_statement.response["account"]["marginAvailable"]) / float(account_statement.response["account"]["marginRate"]), '.0f')
    return units_available


def make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, direction):
    # Just trading engine for the usage in following functions
    data = {
            "order": {
            "timeInForce": "FOK",
            "instrument": INSTRUMENTS,
            "units": direction + units_quantity,  
            "type": "MARKET",
            "positionFill": "DEFAULT"
        }
    }

    client = oandapyV20.API(access_token = ACCESS_TOKEN)
    r = orders.OrderCreate(accountID = ACCOUNT_ID, data = data)
    rv = client.request(r)
    print(r.response)


def change_the_trade(ACCESS_TOKEN, ACCOUNT_ID):
    # Sets take_profit_price condition over the newly opened trade
    
    trade_state = fetch_trades_info(ACCESS_TOKEN, ACCOUNT_ID)
    tradeID = trade_state[0]['id']
    take_profit_price = 0
    if int(trade_state[0]['initialUnits']) > 0:
        take_profit_price = format(float(trade_state[0]['price']) + 0.0002, '.5f')
        # take_profit_price = trade_state[0]['price'] + 0.0001 * number_of_tr_items
    elif int(trade_state[0]['initialUnits']) < 0:
        take_profit_price = format(float(trade_state[0]['price']) - 0.0002, '.5f')
    else:
        print('!!! SOMETHING WENT WRONG IN change_the_trade FUNCTION !!!')
        pass

    data = {
        'takeProfit': {
            'timeInForce': 'GTC',
            'price': take_profit_price
        }
    }
    print(data)
    client = oandapyV20.API(access_token = ACCESS_TOKEN)
    r = trades.TradeCRCDO(accountID = ACCOUNT_ID, tradeID = tradeID, data = data)
    client.request(r)
    print(r.response)


def create_first_trade(ACCESS_TOKEN, ACCOUNT_ID, trade_units_available, structured_price_data, stream_generator, INSTRUMENTS):
    # Chooses direction for the first deal and makes the first trade
    print('trade_units_available: ', trade_units_available)
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
        print('Go Short')
    else:
        direction = ''
        print('Go Long')

    units_quantity = str(int(trade_units_available) // 10)
    print('units_quantity: ', units_quantity)
    make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, direction)
    change_the_trade(ACCESS_TOKEN, ACCOUNT_ID)
    print('The initial order has been put. Good luck!')
    time.sleep(1)
    return
    


def following_trades_creator(ACCESS_TOKEN, ACCOUNT_ID, trade_state, trade_units_available, stream_generator, INSTRUMENTS):
    # Once the initial trade is open makes further trades
    # print('LAST TRADE ID: ', trade_state[0]['id'])

    for price in stream_generator:
        ask_rate = float(price['asks'][0]['price'])
        bid_rate = float(price['bids'][0]['price'])
        break

    trade_amount = int(trade_state[0]['initialUnits'])

    if trade_amount > 0:
        pip_profit_first_trade = bid_rate - float(trade_state[-1]['price'])
        pip_profit_last_trade = bid_rate - float(trade_state[0]['price'])
        direction = ''
    else:
        pip_profit_first_trade = float(trade_state[-1]['price']) - ask_rate
        pip_profit_last_trade = float(trade_state[0]['price']) - ask_rate
        direction = '-'

    first_trade_profit = float(format((pip_profit_first_trade) * 10000, '.1f'))
    last_trade_profit = float(format((pip_profit_last_trade) * 10000, '.1f'))

    number_of_tr_items = len(trade_state)
    print('We currently have ', number_of_tr_items, ' active trade(s).')
    print('Current ASK rate: ', format(ask_rate, '.5f'))
    print('Current BID rate: ', format(bid_rate, '.5f'))
    print('Last trade amount: ', trade_amount)
    print('Profit in PIPs for the last trade: ', last_trade_profit)
    print('Profit in PIPs for the first trade: ', first_trade_profit)
    print('Trade units left: ', trade_units_available)

    if int(trade_units_available) < abs(int(trade_amount * 0.91)):
        print('Les jeux sont faits! Rien ne va plus.')
        return
    else:
        print('Money still available')

    if first_trade_profit <= (-2 * number_of_tr_items) and last_trade_profit <= -2:
        units_quantity = str(int(trade_units_available) // 10)
        print('TRADE SUPPOSED TO BE MADE')
        make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, direction)
        change_the_trade(ACCESS_TOKEN, ACCOUNT_ID)
        time.sleep(1)
        pass
    elif last_trade_profit > 0 or first_trade_profit > 0:
        print('No need for another trade')
        pass
    else:
        print('No need for another trade')
        pass


if __name__=="__main__":
    # change_the_trade(ACCESS_TOKEN, ACCOUNT_ID)
    stream_generator = stream_rates_generator(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS)
    structured_price_data = read_stream_data_generator(stream_generator)
    # TO DO - try-except to avoid error shut-down

    while True:
        try:
            trade_state = fetch_trades_info(ACCESS_TOKEN, ACCOUNT_ID)
            trade_units_available = shows_trade_units_available(ACCESS_TOKEN, ACCOUNT_ID)
            print(datetime.now())
            if len(trade_state) == 0:
                time.sleep(2)
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
                following_trades_creator(ACCESS_TOKEN, ACCOUNT_ID, trade_state, trade_units_available, stream_generator, INSTRUMENTS)
                print('I am active. The fund is working. Relax!')
                print('*******************************************')
                time.sleep(1)
                pass
        except KeyboardInterrupt:
            print('*******************************')
            print('\n\nProgramm has been interrupted by user\n\n')
            print('*******************************')
            break
        except ConnectionResetError:
            print('CONNECTION WAS LOST - Oanda tried to break it')
            print('CONNECTION WAS LOST - Oanda tried to break it')
            print('CONNECTION WAS LOST - Oanda tried to break it')
            change_the_trade(ACCESS_TOKEN, ACCOUNT_ID)
        # except ProtocolError:
        #     print('CONNECTION WAS LOST - Protocol Error')
        #     print('CONNECTION WAS LOST - Protocol Error')
        #     print('CONNECTION WAS LOST - Protocol Error')
        #     change_the_trade(ACCESS_TOKEN, ACCOUNT_ID)
        # except ChunkedEncodingError:
        #     print('CONNECTION WAS LOST - Encoding Error')
        #     print('CONNECTION WAS LOST - Encoding Error')
        #     print('CONNECTION WAS LOST - Encoding Error')
        #     change_the_trade(ACCESS_TOKEN, ACCOUNT_ID)
        # except NameError:
        #     print('CONNECTION WAS LOST - Name Error')
        #     print('CONNECTION WAS LOST - Name Error')
        #     print('CONNECTION WAS LOST - Name Error')
        #     change_the_trade(ACCESS_TOKEN, ACCOUNT_ID)