import requests
import json
import oandapyV20
from oandapyV20 import API
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
import oandapyV20.endpoints.orders as orders
from config import ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS
from datetime import datetime, timedelta
import time

client = API(access_token = ACCESS_TOKEN)
instrument = INSTRUMENTS
granularity = "S5"
td = timedelta(hours=1.4)
correction_td = timedelta(minutes=19)

# def get_raw_data(td, granularity):
#     Function gets the historical data for td-period till now
time_now = datetime.utcnow()
from_time = time_now - td
to_time = time_now - correction_td
_from = from_time.strftime("%Y-%m-%dT%H:%M:%SZ")
_to = to_time.strftime("%Y-%m-%dT%H:%M:%SZ")

params = {
    "from": _from,
    "to": _to,
    "granularity": granularity,
}

for r in InstrumentsCandlesFactory(instrument=instrument, params=params):
    client.request(r)
    timeframe_price_data = r.response.get('candles')
    item = 0
    for time in timeframe_price_data:
        print(timeframe_price_data[item]['time'])
        item += 1
    # print(datetime.utcnow())
        # return timeframe_price_data


# time_now = datetime.utcnow()
# td = timedelta(minutes=2)
# future_time = time_now + td

# td_two = timedelta(minutes=1)

# td_three = timedelta(seconds=30)

# close_time = time_now + td_two

# open_time = close_time + td_three

# print(open_time - close_time)

# print(time_now)
# print(future_time)
# z = 0
# while z < 10:
#     if datetime.utcnow() < future_time:
#         print(datetime.utcnow())
#         print('Hey-Hey!!!')
#         time.sleep(5)
#         if datetime.utcnow() > close_time:
#             if datetime.utcnow() < open_time:
#                 print('We are now closed!')
#                 time.sleep(30)
#                 pass
#             else:
#                 print('We are now opened!')
#                 pass

#     else:
#         break

# print('Time ran out')