import json
import requests
import oandapyV20
import oandapyV20.endpoints.trades as trades
# import oandapyV20.endpoints.orders as orders
from config import ACCESS_TOKEN, ACCOUNT_ID
import time

trade_id = '4704'

client = oandapyV20.API(access_token=ACCESS_TOKEN)
r = trades.TradeDetails(accountID=ACCOUNT_ID, tradeID=trade_id)
client.request(r)
print(r.response)

# x = 0
# while x != 1:
#     client = oandapyV20.API(access_token=ACCESS_TOKEN)
#     r = orders.OrdersPending(ACCOUNT_ID)
#     client.request(r)
#     print(r.response)
#     time.sleep(1)