import requests
import json
import oandapyV20
from oandapyV20 import API
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
import oandapyV20.endpoints.orders as orders
from config import ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np 
from sklearn.svm import SVR


client = API(access_token = ACCESS_TOKEN)
instrument = INSTRUMENTS
granularity = "S5"
td = timedelta(hours=1)

def get_raw_data(td, granularity):
    # Function gets the historical data for td-period till now
    time_now = datetime.utcnow()
    starting_time = time_now - td
    _from = starting_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    _to = time_now.strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
        "from": _from,
        "to": _to,
        "granularity": granularity,
    }

    for r in InstrumentsCandlesFactory(instrument=instrument, params=params):
        client.request(r)
        timeframe_price_data = r.response.get('candles')
        return timeframe_price_data


def prepare_the_data(timeframe_price_data):
    # Makes several lists of instances for future usage
    dates = list()
    prices = list()
    instances = list()
    last_five_prices_sum = 0

    item = 0
    instance = 1
    for row in timeframe_price_data:

        dates.append(datetime.strftime(datetime.strptime(timeframe_price_data[item]['time'].split('.')[0], '%Y-%m-%dT%H:%M:%S'), '%Y-%m-%dT%H:%M:%SZ'))
        prices.append(timeframe_price_data[item]['mid']['c'])
        instances.append(instance)
        if item >= (len(timeframe_price_data) - 5):
            last_five_prices_sum += float(timeframe_price_data[item]['mid']['c'])
        else:
            pass
        instance +=1
        item += 1

    last_five_average = format((last_five_prices_sum/5), '.5f')

    return instances, prices, last_five_average


def predict_prices(instances, prices, x):
    # Funtion calculates rate prediction with three methods
    min_price = float(min(prices)) - 0.0005
    max_price = float(max(prices)) + 0.0005

    svr_lin = SVR(kernel = 'linear', C = 1e3)
    svr_poly = SVR(kernel = 'poly', C = 1e3, degree = 2)
    svr_rbf = SVR(kernel = 'rbf', C = 1e3, gamma = 0.1)
    svr_lin.fit(instances, prices)
    svr_poly.fit(instances, prices)
    svr_rbf.fit(instances, prices)
# TO DO - Find out the problem with prediction models
    plt.scatter(instances, prices, color = '#191970', label = 'Time')
    plt.plot(instances, svr_rbf.predict(instances), color = 'red', label = 'RBF model')
    plt.plot(instances, svr_lin.predict(instances), color = 'green', label = 'Linear model')
    plt.plot(instances, svr_poly.predict(instances), color = 'blue', label = 'Polynomial model')
    plt.ylim([min_price, max_price])
    # plt.xticks(x, dates, rotation = 'vertical')
    plt.xlabel('Dates')
    plt.ylabel('Prices')
    plt.title('Support Vector Regression')
    plt.legend()
    plt.show()

    return format(svr_rbf.predict(x)[0], '.5f'), format(svr_lin.predict(x)[0], '.5f'), format(svr_poly.predict(x)[0], '.5f')


def get_last_price():
    url = 'https://stream-fxpractice.oanda.com/v3/accounts/' + ACCOUNT_ID + '/pricing/stream?instruments=%s' % (INSTRUMENTS)
    head = {'Content-type':"application/json",
            'Accept-Datetime-Format':"RFC3339",
            'Authorization':"Bearer " + ACCESS_TOKEN}

    r = requests.get(url, headers=head, stream=True)
    print(r)

    for line in r.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if json.loads(decoded_line)['type'] == 'PRICE':
                ask_price = json.loads(decoded_line)['asks'][0]['price']
                bid_price = json.loads(decoded_line)['bids'][0]['price']
                return ask_price, bid_price
            else:
                print(json.loads(decoded_line))
                print('Heartbeat')
        else:
            print('Something went wrong...')

    # Below is the logics how to choose the direction

def choose_direction(ask_price, predicted_price, last_five_average):

    print('RBF model prediction: ', predicted_price[0])
    print('Linear model prediction: ', predicted_price[1])
    print('Polynomial model prediction: ', predicted_price[2])
    print('Last Five Average prediction: ', last_five_average)
    print('Last price', prices[-1])

    if predicted_price[0] < ask_price:
        if last_five_average < ask_price:
            suggestion = 'Go Short'
        else:
            suggestion = 'Go Long'
    else:
        if last_five_average > ask_price:
            suggestion = 'Go Long'
        else:
            suggestion = 'Go Short'
    print(suggestion)
    return suggestion


def make_a_deal(suggestion, trade_amount, ask_price, bid_price):

    amount_of_units = trade_amount
    if suggestion == "Go Long":
        direction = ''
        take_profit_price = float(ask_price) + 0.0001
    else:
        direction = '-'
        take_profit_price = float(bid_price) - 0.0001
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
            "price": str(take_profit_price)
            }
        }
    }

    client = oandapyV20.API(access_token = ACCESS_TOKEN)
    r = orders.OrderCreate(accountID = ACCOUNT_ID, data = data)
    client.request(r)
    print(r.response)


if __name__=="__main__":
    timeframe_price_data = get_raw_data(td, granularity)
    instances = prepare_the_data(timeframe_price_data)[0]
    instances = np.reshape(instances,(len(instances), 1))
    prices = prepare_the_data(timeframe_price_data)[1]
    last_five_average = prepare_the_data(timeframe_price_data)[2]
    predicted_price = predict_prices(instances, prices, 50)
    ask_price = get_last_price()[0]
    bid_price = get_last_price()[1]
    choose_direction(ask_price, predicted_price, last_five_average)
    # trade_amount = 1000
    # make_a_deal(suggestion, trade_amount, ask_price, bid_price)
