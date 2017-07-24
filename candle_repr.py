import requests
from datetime import datetime
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
from config import ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS
import matplotlib.pyplot as plt
import numpy as np 
from sklearn.svm import SVR

# >>>from time import sleep
# >>>sleep(1)

prediction_length = 150
granularity = 'S5'

def connect_to_api():
    client = oandapyV20.API(access_token= ACCESS_TOKEN)
    params = {'accountId' : ACCOUNT_ID, 'instruments' : INSTRUMENTS, 'granularity': granularity}
    data_request = instruments.InstrumentsCandles(instrument = INSTRUMENTS, params = params)
    client.request(data_request)
    response = data_request.response
    return response

def candle_responce_reader(response_data):
    granularity = response_data['granularity']
    instrument = response_data['instrument']
    candles = response_data['candles']

    instance_num = 0
    candles_structured = list()
    for candle in candles:
        single_candle = dict()
        single_candle['instance_num'] = instance_num
        single_candle['complete'] = candles[instance_num]['complete']
        single_candle['volume'] = candles[instance_num]['volume']
        single_candle['time'] = datetime.strftime(datetime.strptime(candles[instance_num]['time'].split('.')[0], '%Y-%m-%dT%H:%M:%S'), '%d.%m.%Y %H:%M:%S')
        # single_candle['time'] = int(candles[instance_num]['time'].split('.')[0].split("T")[1].replace(':',''))
        single_candle['open_price'] = candles[instance_num]['mid']['o']
        single_candle['highest_price'] = candles[instance_num]['mid']['h']
        single_candle['lowest_price'] = candles[instance_num]['mid']['l']
        single_candle['close_price'] = candles[instance_num]['mid']['c']

        candles_structured.append(single_candle)
        instance_num += 1

    return candles_structured

# TO DO - check with the data
def prepare_the_data(candles_structured_data):

    dates = list()
    prices = list()
    instances = list()
    last_five_prices_sum = 0

    instance = 0
    for row in candles_structured_data:

        dates.append(candles_structured_data[instance]['time'])
        instances.append(candles_structured_data[instance]['instance_num'])
        prices.append(candles_structured_data[instance]['close_price'])
        if instance >= 495:
            last_five_prices_sum += float(candles_structured_data[instance]['close_price'])
        else:
            pass
        instance += 1

    prices = prices[:prediction_length]
    dates = np.reshape(dates,(len(dates), 1))[:prediction_length]
    instances = np.reshape(instances,(len(instances), 1))[:prediction_length]

    last_five_avg = format((float(last_five_prices_sum) / 5), '.5f')

    return dates, prices, instances, last_five_avg

def predict_prices(prices, instances, x):
    
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
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.title('Support Vector Regression')
    plt.legend()
    plt.show()

    return format(svr_rbf.predict(x)[0], '.5f'), format(svr_lin.predict(x)[0], '.5f'), format(svr_poly.predict(x)[0], '.5f')
    

if __name__=="__main__":
    response = connect_to_api()
    candles_structured = candle_responce_reader(response)
    prices = prepare_the_data(candles_structured)[1]
    # dates = prepare_the_data(candles_structured)[0]
    instances = prepare_the_data(candles_structured)[2]
    last_five_avg = prepare_the_data(candles_structured)[3]
    predicted_price = predict_prices(prices, instances, 29)
    print('RBF model prediction: ', predicted_price[0])
    print('Linear model prediction: ', predicted_price[1])
    print('Polynomial model prediction: ', predicted_price[2])
    print('Last Five Average prediction: ', last_five_avg)
    print('Last price', prices[-1])

    # Below is the logics how to choose the direction

    if predicted_price[0] < last_five_avg:
        if last_five_avg > prices[-1]:
            suggestion = 'Go Short'
        else:
            suggestion = 'Go Long'
    else:
        suggestion = 'Go Long'

    print(suggestion)

