import json
import requests
from config import ACCESS_TOKEN, ACCOUNT_ID
from oandapyV20 import API
import oandapyV20.endpoints.trades as trades
from datetime import datetime, timedelta
import time
import ast

def get_quasi_stream_trades_info(ACCESS_TOKEN, ACCOUNT_ID):
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


if __name__=="__main__":

    for cur_trades in get_quasi_stream_trades_info(ACCESS_TOKEN, ACCOUNT_ID):
        print(cur_trades)
        time_now = datetime.utcnow()
        print(time_now)
    # TIME NOW?? datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%SZ')
