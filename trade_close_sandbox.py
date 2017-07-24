import oandapyV20
import oandapyV20.endpoints.trades as trades
from config import ACCESS_TOKEN, ACCOUNT_ID

client = oandapyV20.API(access_token=ACCESS_TOKEN)
data = {
"units": '100'
}
r = trades.TradeClose(accountID=ACCOUNT_ID, data=data, tradeID = '360')
client.request(r)
print(r.response)