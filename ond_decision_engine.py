import requests
import json
from config import ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS
from datetime import datetime
from rate_request import stream_rates, stream_reader


for i in stream_rates(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS):
    print(stream_rates(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS))
    print(stream_reader(stream_data))


# TO DO: Learn how to get stable HEARTBEAT rates info
# TO DO: The rates for decision should be the actual rates from the market - see sandbox!
# TO DO: Learn how to make the first order
# TO DO: Learn how to create/modify an order with "Take Profit" condition
# This chapter in docs may help: Example for trades-endpoints
# TO DO: build a rule for the following orders once the initial order is opened

