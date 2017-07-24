import json
import requests
from config import ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS
from datetime import datetime, timedelta
import time

def stream_rates(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS):
    # Connects to the rate stream
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

def price_lists_creator(structured_price_data):
    # Generates the lists for the future dynamics prediction
    for price_list in structured_price_data:
        ask_price_list = price_list[1]
        bid_price_list = price_list[2]
        yield ask_price_list, bid_price_list



if __name__=="__main__":

    stream_generator = stream_rates(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS)
    structured_price_data = read_stream_data(stream_generator)
    for rate_lists in price_lists_creator(structured_price_data):
        print('Ask price list: ', rate_lists[0])
        print('Bid price list: ', rate_lists[1])
    # data = list()

    
    # for y in structured_price_data:

    #     print('New ASK price: ',  y['ask'])
    #     data.append(y[1])
    #     print(y)
    #     price_lists_creator(structured_price_data)

    # ask_price_list = price_lists_creator(structured_price_data)[0]
    # bid_price_list = price_lists_creator(structured_price_data)[1]

    # print('Here are the ASK prices: ', ask_price_list)
    # z = 0
    # while z < 10:
    #     time.sleep(60)
    #     print('Here are the ASK prices: ', ask_price_list)



# time.sleep(10)

# if len(data) < 5:
#     pass
# else:
#     print('TO DELETE:', data[-5])
#     del(data[-5])
# print('len(data)', len(data))