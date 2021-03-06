import requests
import json
from config import ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS
from datetime import datetime, timedelta
import time

def stream_rates(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS):
    url = 'https://stream-fxpractice.oanda.com/v3/accounts/' + ACCOUNT_ID + '/pricing/stream?instruments=%s' % (INSTRUMENTS)
    head = {'Content-type':"application/json",
            'Accept-Datetime-Format':"RFC3339",
            'Authorization':"Bearer " + ACCESS_TOKEN}

    r = requests.get(url, headers=head, stream=True)
    print(r)
    for line in r.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            yield json.loads(decoded_line)


def read_stream_data(stream_generator):

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
            if len(ask_rates) < 10:
                ask_rates.append(float(rate['asks'][0]['price']))
                bid_rates.append(float(rate['bids'][0]['price']))
            else:
                print('Value to deleted from ASK: ', ask_rates[-10])
                print('Value to deleted from BID: ', bid_rates[-10])
                del(bid_rates[-10])
                del(ask_rates[-10])
                
        else:
            print("No data available")
            pass
        yield instant_rates, ask_rates, bid_rates


if __name__=="__main__":

    stream_generator = stream_rates(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS)
    # for rate_lists in read_stream_data(stream_generator):
    #     if len(rate_lists[1]) > 5:
    #         print('Ask price list: ', rate_lists[1])
    #         print('Bid price list: ', rate_lists[2])
    #     else:
    #         pass
    for item in stream_generator:
        print(item)