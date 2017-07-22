import requests
import json
import oandapyV20
import oandapyV20.endpoints.orders as orders

access_token="d612e5b6e0f902b605207883dded35bc-8928c64998a13c444885331fd77cf935"
accountID = "101-004-6259640-001"
order_id = 154

# Put the right order ID first!!!

client = oandapyV20.API(access_token=access_token)
r = orders.OrderCancel(accountID= accountID, orderID = order_id)
client.request(r)
print(r.response)
