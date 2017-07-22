import requests
import json
from oandapyV20 import API
import oandapyV20.endpoints.trades as trades
from config import ACCESS_TOKEN, ACCOUNT_ID

def all_trades_info_request(ACCESS_TOKEN, ACCOUNT_ID):
    api = API(access_token = ACCESS_TOKEN)

    r = trades.TradesList(ACCOUNT_ID)
    print("REQUEST:{}".format(r))
    rv = api.request(r)
    return "RESPONSE:\n{}".format(json.dumps(rv, indent=2))

print(all_trades_info_request(ACCESS_TOKEN, ACCOUNT_ID))