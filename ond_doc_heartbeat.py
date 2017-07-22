import json
from oandapyV20 import API
from oandapyV20.exceptions import V20Error
from oandapyV20.endpoints.pricing import PricingStream
from config import ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS

def stream_rates(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS):
    api = API(access_token=ACCESS_TOKEN, environment="practice")
    stream = PricingStream(accountID=ACCOUNT_ID, params={"instruments":INSTRUMENTS})
    try:
        item = 0
        for response in api.request(stream):
            print(json.dumps(response, indent=2))
            item += 1
            # if n > 10:
            #     stream.terminate("maxrecs received: {}".format(MAXREC))

    except V20Error as e:
        print("Error: {}".format(e))

stream_rates(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS)