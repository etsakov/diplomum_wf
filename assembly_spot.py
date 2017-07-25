import json
import requests
import oandapyV20
from oandapyV20 import API
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.accounts as accounts
from config import ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS
from datetime import datetime, timedelta
import time
import ast
import matplotlib.pyplot as plt
import numpy as np 
from sklearn.svm import SVR

def quasi_stream_trades_info_generator(ACCESS_TOKEN, ACCOUNT_ID):
    # Generates a stream of current transactions info and converts it into the operable lists
    x = 0
    while x != 1:
        api = API(access_token = ACCESS_TOKEN)
        r = trades.TradesList(ACCOUNT_ID)
        rv = api.request(r)
        trades_full_info = format(json.dumps(rv, indent=2))
        trades_full_info = ast.literal_eval(trades_full_info)
        # ast.literal_eval - converts a string to a dictionary
        trade_item = 0
        number_of_trades = len(trades_full_info['trades'])
        trade_list = list()
        
        for trade_item_info in trades_full_info['trades']:
            if trade_item <= number_of_trades:
                trade_item_info = dict()
                trade_item_info['tradeID'] = trades_full_info['trades'][trade_item]['takeProfitOrder']['tradeID']
                trade_item_info['state'] = trades_full_info['trades'][trade_item]['state']
                trade_item_info['instrument'] = trades_full_info['trades'][trade_item]['instrument']
                trade_item_info['open_time'] = datetime.strftime(datetime.strptime(trades_full_info['trades'][trade_item]['openTime'].split('.')[0], '%Y-%m-%dT%H:%M:%S'), '%Y-%m-%dT%H:%M:%SZ')
                trade_item_info['currentUnits'] = int(trades_full_info['trades'][trade_item]['currentUnits'])
                trade_item_info['initial_price'] = float(trades_full_info['trades'][trade_item]['price'])
                trade_item_info['take_profit_price'] = float(trades_full_info['trades'][trade_item]['takeProfitOrder']['price'])
                trade_item_info['take_profit_pips'] = format((float(trades_full_info['trades'][trade_item]['takeProfitOrder']['price']) - float(trades_full_info['trades'][trade_item]['price'])) * 10000, '.1f')
                trade_item_info['unrealized_PL'] = float(trades_full_info['trades'][trade_item]['unrealizedPL'])
                trade_item_info['financing'] = float(trades_full_info['trades'][trade_item]['financing'])
                trade_list.append(trade_item_info)
                trade_item += 1
            else:
                pass

        yield trade_list
        time.sleep(1)


def stream_rates_generator(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS):
    # Connects to the rate stream and re-generates rate in a stream
    url = 'https://stream-fxpractice.oanda.com/v3/accounts/' + ACCOUNT_ID + '/pricing/stream?instruments=%s' % (INSTRUMENTS)
    head = {'Content-type':"application/json",
            'Accept-Datetime-Format':"RFC3339",
            'Authorization':"Bearer " + ACCESS_TOKEN}

    r = requests.get(url, headers=head, stream=True)
    # print(r)
    for line in r.iter_lines():

        if line:
            decoded_line = line.decode('utf-8')
            yield json.loads(decoded_line)


def read_stream_data_generator(stream_generator):
    # Interprets stream info to the operable instances
    ask_rates = list()
    bid_rates = list()

    for rate in stream_generator:
        if rate['type'] == 'PRICE':
            instant_rates = dict()
            instant_rates['time'] = datetime.strftime(datetime.strptime(rate['time'].split('.')[0], '%Y-%m-%dT%H:%M:%S'), '%d.%m.%Y %H:%M:%S')
            instant_rates['status'] = rate['status']
            instant_rates['ask'] = float(rate['asks'][0]['price'])
            instant_rates['bid'] = float(rate['bids'][0]['price'])
            instant_rates['spread'] = float('%.5f' % (float(rate['asks'][0]['price']) - float(rate['bids'][0]['price'])))
            if len(ask_rates) < 150:
                ask_rates.append(float(rate['asks'][0]['price']))
                bid_rates.append(float(rate['bids'][0]['price']))
            else:
                print('Value to delete from ASK: ', ask_rates[-150])
                del(ask_rates[-150])
                print('Value to delete from BID: ', bid_rates[-150])
                del(bid_rates[-150])

        else:
            print("No data available")
            pass
        yield instant_rates, ask_rates, bid_rates


def trades_pip_margin_indicator(trades_stream_data, structured_price_data):
    # Generates profit in PIPs to facilitate the decision making for following trades
    a = 0
    while a != 1:
        time_now = datetime.utcnow()
        print(time_now)

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
                # print('trades_profits', trades_profits)
                yield trades_profits
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


def rate_direction_predictor(trades_stream_data, trade_units_available, structured_price_data, INSTRUMENTS):
    # Chooses direction for the first deal

    d = 0
    while d != 1:
        print('trade_units_available: ', trade_units_available)
        for tsd_item in trades_stream_data:
            print(len(tsd_item))
            if len(tsd_item) > 0:
                pass
            else:
                for struct_price_data_item in structured_price_data:
                    if len(struct_price_data_item[1]) < 5:
                        pass
                    else:
                        last_price = float(struct_price_data_item[1][-1])
                        last_five_item = 0
                        last_five_items_sum = 0
                        for f in struct_price_data_item[1][-5:]:
                            last_five_items_sum += float(struct_price_data_item[1][-5:][last_five_item])
                            last_five_item += 1
                        last_five_avg = float(format(float(last_five_items_sum) / 5, '.5f'))
                        print('Last price', last_price)
                        print('Last five average', last_five_avg)
                        if last_price < last_five_avg:
                            direction = '-'
                            take_profit_price = format(last_price - 0.0003, '.5f')
                        else:
                            direction = ''
                            take_profit_price = format(last_price + 0.0003, '.5f')

                        amount_of_units = int(int(trade_units_available) / 10)
                        units_quantity = direction + str(amount_of_units)
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
                        client.request(r)
                        print(r.response)
                        
            break
            # TO DO - It semms to be correct to initiate two parallel programms: to collect the data and to initiate trades.


def following_trades_creator(trades_stream_data, compare_heartbeat, trade_units_available, structured_price_data, INSTRUMENTS):
    # Once the initial trade is open makes further trades
    c = 0
    while c != 1:
        for tsd_item in trades_stream_data:
            print(len(tsd_item))
            if len(tsd_item) == 0:
                pass
            else:
                for trade in compare_heartbeat:
                    unit = len(trade)
                    trade_amount = trade[0]['trade_amount']
                    trade_profit = trade[0]['trade_' + str(unit)]
                    print('trade_amount ', trade_amount, ' ', type(trade_amount))
                    print('trade_profit ', trade_profit, ' ', type(trade_profit))
                    break

                for price_lists in structured_price_data:
                    ask_rate = price_lists[1][-1]
                    bid_rate = price_lists[2][-1]
                    print('ask_rate ', ask_rate, ' ', type(ask_rate))
                    print('bid_rate ', bid_rate, ' ', type(bid_rate))
                    break

                print('Trade units left: ', trade_units_available)

                if int(trade_units_available) < abs(trade_amount):
                    print('!!!Not enough units to trade!!!')

                else:
                    if trade_profit < -5:
                        if trade_amount > 0:
                            take_profit_price = format(ask_rate + 0.0002, '.5f')
                        else:
                            take_profit_price = format(bid_rate - 0.0002, '.5f')
                    elif trade_profit > 1:
                        if trade_amount > 0:
                            take_profit_price = format(ask_rate + 0.0001, '.5f')
                        else:
                            take_profit_price = format(bid_rate - 0.0001, '.5f')

                    else:
                        pass

                    data = {
                            "order": {
                            "timeInForce": "FOK",
                            "instrument": INSTRUMENTS,
                            "units": str(trade_amount),  
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
                    client.request(r)
                    print(r.response)
            break

        time.sleep(1)



if __name__=="__main__":
    trades_stream_data = quasi_stream_trades_info_generator(ACCESS_TOKEN, ACCOUNT_ID)
    stream_generator = stream_rates_generator(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS)
    structured_price_data = read_stream_data_generator(stream_generator)
    compare_heartbeat = trades_pip_margin_indicator(trades_stream_data, structured_price_data)
    trade_units_available = shows_trade_units_available(ACCESS_TOKEN, ACCOUNT_ID)
    # price_lists_generator = price_lists_generator(structured_price_data)
    rate_direction_predictor(trades_stream_data, trade_units_available, structured_price_data, INSTRUMENTS)
    following_trades_creator(trades_stream_data, compare_heartbeat, trade_units_available, structured_price_data, INSTRUMENTS)

    # b = 0
    # while b != 1:
    #     for test_beat in rate_direction_predictor(trades_stream_data, trade_units_available, structured_price_data):
    #         print(test_beat)
    #         print(shows_trade_units_available(ACCESS_TOKEN, ACCOUNT_ID))
    #         time.sleep(1)
    

    # l = 0
    # while l != 1:
    #     for cur_trades in quasi_stream_trades_info_generator(ACCESS_TOKEN, ACCOUNT_ID):
    #         print(cur_trades)
    #         time_now = datetime.utcnow()
    #         print(time_now)
    #         break

    #     stream_generator = stream_rates_generator(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS)
    #     structured_price_data = read_stream_data_generator(stream_generator)
    #     for rate_lists in price_lists_generator(structured_price_data):
    #         print('Ask price list: ', rate_lists[0])
    #         print('Bid price list: ', rate_lists[1])
    #         break

    # TIME NOW?? datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%SZ')