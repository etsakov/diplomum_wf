import json
import oandapyV20
import oandapyV20.endpoints.trades as trades

accountID = "101-004-6259640-001"
access_token = "d612e5b6e0f902b605207883dded35bc-8928c64998a13c444885331fd77cf935"
amount_of_units = '100'
trade_id = '...'

client = oandapyV20.API(access_token = access_token)
r = accounts.TradeDetails(accountID = accountID, tradeID = trade_id)
client.request(r)
print(r.response)
