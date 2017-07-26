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
from datetime import datetime, timedelta
import time
import ast
import matplotlib.pyplot as plt
import numpy as np 
from sklearn.svm import SVR

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
        time.sleep(1)


def stream_rates_generator(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS):
    # Connects to the rate stream and re-generates rate in a stream
    url = 'https://stream-fxpractice.oanda.com/v3/accounts/{}/pricing/stream'.format(ACCOUNT_ID)
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
    # Interprets stream info to the operable instances
    ask_rates = deque(maxlen=150)
    bid_rates = deque(maxlen=150)

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
            
        yield instant_rates, ask_rates, bid_rates


def trades_pip_margin_indicator(trades_stream_data, structured_price_data):
    # Generates profit in PIPs for the last trade to facilitate the decision making for following trades
    while True:
        time_now = datetime.utcnow()
        print("Current time: ", time_now)

        for cur_trades in quasi_stream_trades_info_generator(ACCESS_TOKEN, ACCOUNT_ID):
            full_trades_data = cur_trades
            break

        stream_generator = stream_rates_generator(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS)
        structured_price_data = read_stream_data_generator(stream_generator)
        for rate in structured_price_data:
            ask_rate = float(rate[0]['ask'])
            bid_rate =  float(rate[0]['bid'])
            break

        tr_item = 0
        number_of_tr_items = len(full_trades_data)
        trades_profits = list()
        for trade_price in full_trades_data:
            if full_trades_data[tr_item]['currentUnits'] > 0:
                profit_in_pips = dict()
                profit_in_pips['trade_' + str(number_of_tr_items - tr_item)] = float(format((bid_rate - full_trades_data[tr_item]['initial_price']) * 10000, '.1f'))
                profit_in_pips['trade_amount'] = full_trades_data[tr_item]['currentUnits']
                trades_profits.append(profit_in_pips)
            else:
                profit_in_pips = dict()
                profit_in_pips['trade_' + str(number_of_tr_items - tr_item)] = float(format((full_trades_data[tr_item]['initial_price'] - ask_rate) * 10000, '.1f'))
                profit_in_pips['trade_amount'] = full_trades_data[tr_item]['currentUnits']
                trades_profits.append(profit_in_pips)
            if len(trades_profits) == number_of_tr_items:
                yield trades_profits
                time.sleep(1)
            else:
                pass
            tr_item += 1


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


def rate_direction_predictor(ACCESS_TOKEN, ACCOUNT_ID, trades_stream_data, trade_units_available, structured_price_data, INSTRUMENTS):
    # Chooses direction for the first deal and makes the first trade
    print('trade_units_available: ', trade_units_available)
    for tsd_item in trades_stream_data:
        if len(tsd_item) > 0:
            break
        else:
            for struct_price_data_item in structured_price_data:
                if len(struct_price_data_item[1]) < 5:
                    print("Not enough data to choose the direction :((")
                    continue
                else:
                    time.sleep(3)
                    last_price = float(struct_price_data_item[1][-1])
                    last_item = 0
                    last_five_items_sum = 0
                    for f in struct_price_data_item[1][-5:]:
                        last_five_items_sum += float(struct_price_data_item[1][-5:][last_item])
                        last_item += 1
                    last_five_avg = float(format(float(last_five_items_sum) / 5, '.5f'))
                    print('Last price', last_price)
                    print('Last five average', last_five_avg)
                    if last_price < last_five_avg:
                        direction = '-'
                        take_profit_price = format(last_price - 0.0003, '.5f')
                        break
                    else:
                        direction = ''
                        take_profit_price = format(last_price + 0.0002, '.5f')
                        break

            amount_of_units = int(int(trade_units_available) / 10)
            units_quantity = direction + str(amount_of_units)
            make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, take_profit_price)
            time.sleep(3)
            break
        break
                    
        
        # TO DO - It semms to be a good idea to initiate two parallel programms: to collect the data and to initiate trades.


def following_trades_creator(ACCESS_TOKEN, ACCOUNT_ID, trades_stream_data, compare_heartbeat, trade_units_available, structured_price_data, INSTRUMENTS):
    # Once the initial trade is open makes further trades

# !!! The function cannot capture the "positive" graph behaviour - all "positive" following trades are cancelled
# {'orderCreateTransaction': {'id': '1460', 'instrument': 'EUR_USD', 'userID': 6259640, 
# 'requestID': '42324510077575889', 'timeInForce': 'FOK', 'time': '2017-07-25T20:36:01.449758667Z', 
# 'type': 'MARKET_ORDER', 'positionFill': 'DEFAULT', 'takeProfitOnFill': {'price': '1.16455', 
# 'timeInForce': 'GTC'}, 'reason': 'CLIENT_ORDER', 'batchID': '1460', 'units': '979', 
# 'accountID': '101-004-6259640-001'}, 'orderCancelTransaction': {'id': '1461', 
# 'time': '2017-07-25T20:36:01.449758667Z', 'accountID': '101-004-6259640-001', 'userID': 6259640, 
# 'requestID': '42324510077575889', 'reason': 'LOSING_TAKE_PROFIT', 'batchID': '1460', 
# 'orderID': '1460', 'type': 'ORDER_CANCEL'}, 'lastTransactionID': '1461', 
# 'relatedTransactionIDs': ['1460', '1461']}


    for tsd_item in trades_stream_data:
        print('We currently have ', len(tsd_item), ' active transaction(s).')
        if len(tsd_item) == 0:
            break
        else:
            for trade in compare_heartbeat:
                unit = len(trade)
                trade_amount = trade[0]['trade_amount']
                trade_profit = trade[0]['trade_' + str(unit)]
                print('Last trade amount: ', trade_amount)
                print('Unrealized profit for the last trade: ', trade_profit)
                break

            for price_lists in structured_price_data:
                ask_rate = price_lists[1][-1]
                bid_rate = price_lists[2][-1]
                print('Current ASK rate: ', ask_rate)
                print('Current BID rate: ', bid_rate)
                break

            print('Trade units left: ', trade_units_available)

            if int(trade_units_available) < abs(trade_amount):
                print('********************************')
                print('!!!Not enough units to trade!!!')
                print('********************************')
                break

            else:
                if trade_profit <= -3:
                    if trade_amount > 0:
                        take_profit_price = format(ask_rate + 0.0001, '.5f')
                        units_quantity = str(trade_amount)
                        make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, take_profit_price)
                        time.sleep(3)
                        break
                    else:
                        take_profit_price = format(bid_rate - 0.0001, '.5f')
                        units_quantity = str(trade_amount)
                        make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, take_profit_price)
                        time.sleep(3)
                        break

                elif trade_profit >= 1:
                    if trade_amount > 0:
                        take_profit_price = format(ask_rate + 0.0002, '.5f')
                        units_quantity = str(trade_amount)
                        make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, take_profit_price)
                        time.sleep(3)
                        break
                    else:
                        take_profit_price = format(bid_rate - 0.0002, '.5f')
                        units_quantity = str(trade_amount)
                        make_the_trade(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS, units_quantity, take_profit_price)
                        time.sleep(3)
                        break
                else:
                    break


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


if __name__=="__main__":
    trades_stream_data = quasi_stream_trades_info_generator(ACCESS_TOKEN, ACCOUNT_ID)
    stream_generator = stream_rates_generator(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS)
    structured_price_data = read_stream_data_generator(stream_generator)
    compare_heartbeat = trades_pip_margin_indicator(trades_stream_data, structured_price_data)
    trade_units_available = shows_trade_units_available(ACCESS_TOKEN, ACCOUNT_ID)
    
    for h in trades_stream_data:
        if len(h) == 0:
            print('*******************************************')
            rate_direction_predictor(ACCESS_TOKEN, ACCOUNT_ID, trades_stream_data, trade_units_available, structured_price_data, INSTRUMENTS)
            print('The initial order has been put. Good luck!')
            print('*******************************************')
            pass
        else:
            print('*******************************************')
            following_trades_creator(ACCESS_TOKEN, ACCOUNT_ID, trades_stream_data, compare_heartbeat, trade_units_available, structured_price_data, INSTRUMENTS)
            print('I am active. The fund is working. Relax!')
            print('*******************************************')
            pass
    # TIME NOW?? datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%SZ')

# ******************************************************************
# 
# Unusual behaviour - sometimes the function doesn't set the right Take Profit value
# Moreover it overwrites the existing value with the wrong one.
# 
# ******************************************************************
# ERROR-ERROR-ERROR
#     Traceback (most recent call last):
#   File "c:\projects\Diplomum\env\lib\site-packages\urllib3\response.py", line 302, in _error_catcher
#     yield
#   File "c:\projects\Diplomum\env\lib\site-packages\urllib3\response.py", line 594, in read_chunked
#     self._update_chunk_length()
#   File "c:\projects\Diplomum\env\lib\site-packages\urllib3\response.py", line 536, in _update_chunk_length
#     line = self._fp.fp.readline()
#   File "C:\Python34\lib\socket.py", line 378, in readinto
#     return self._sock.recv_into(b)
#   File "C:\Python34\lib\ssl.py", line 748, in recv_into
#     return self.read(nbytes, buffer)
#   File "C:\Python34\lib\ssl.py", line 620, in read
#     v = self._sslobj.read(len, buffer)
# ConnectionResetError: [WinError 10054] Удаленный хост принудительно разорвал существующее подключение

# During handling of the above exception, another exception occurred:

# Traceback (most recent call last):
#   File "c:\projects\Diplomum\env\lib\site-packages\requests\models.py", line 739, in generate
#     for chunk in self.raw.stream(chunk_size, decode_content=True):
#   File "c:\projects\Diplomum\env\lib\site-packages\urllib3\response.py", line 432, in stream
#     for line in self.read_chunked(amt, decode_content=decode_content):
#   File "c:\projects\Diplomum\env\lib\site-packages\urllib3\response.py", line 622, in read_chunked
#     self._original_response.close()
#   File "C:\Python34\lib\contextlib.py", line 77, in __exit__
#     self.gen.throw(type, value, traceback)
#   File "c:\projects\Diplomum\env\lib\site-packages\urllib3\response.py", line 320, in _error_catcher
#     raise ProtocolError('Connection broken: %r' % e, e)
# urllib3.exceptions.ProtocolError: ("Connection broken: ConnectionResetError(10054, 'Удаленный хост принудительно разорвал существующее подключение', None, 10054, None)", ConnectionResetError(10054, 'Удаленный хост принудительно разорвал существующее подключение', None, 10054, None))

# During handling of the above exception, another exception occurred:

# Traceback (most recent call last):
#   File "assembly_spot.py", line 300, in <module>
#     following_trades_creator(trades_stream_data, compare_heartbeat, trade_units_available, structured_price_data, INSTRUMENTS)
#   File "assembly_spot.py", line 220, in following_trades_creator
#     for price_lists in structured_price_data:
#   File "assembly_spot.py", line 73, in read_stream_data_generator
#     for rate in stream_generator:
#   File "assembly_spot.py", line 61, in stream_rates_generator
#     for line in r.iter_lines():
#   File "c:\projects\Diplomum\env\lib\site-packages\requests\models.py", line 783, in iter_lines
#     for chunk in self.iter_content(chunk_size=chunk_size, decode_unicode=decode_unicode):
#   File "c:\projects\Diplomum\env\lib\site-packages\requests\models.py", line 742, in generate
#     raise ChunkedEncodingError(e)
# requests.exceptions.ChunkedEncodingError: ("Connection broken: ConnectionResetError(10054, 'Удаленный хост принудительно разорвал существующее подключение', None, 10054, None)", ConnectionResetError(10054, 'Удаленный хост принудительно разорвал существующее подключение', None, 10054, None))
