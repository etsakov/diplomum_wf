import requests
import json
from config import ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS
from datetime import datetime

# TO DO - hide string 5-7 to a separate file

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
            return json.loads(decoded_line)

# Prints only 10 instances???!!!

def stream_reader(stream_data):
    for rates in stream_data:
        rates = dict()
        rates['time'] = datetime.strftime(datetime.strptime(stream_data['time'].split('.')[0], '%Y-%m-%dT%H:%M:%S'), '%d.%m.%Y %H:%M:%S')
        rates['status'] = stream_data['status']
        rates['ask'] = stream_data['asks'][0]['price']
        rates['bid'] = stream_data['bids'][0]['price']
        return rates

if __name__=="__main__":

    stream_data = stream_rates(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS)
    print(stream_reader(stream_data))

    # HOW TO MAKE IT HEARTBEAT???