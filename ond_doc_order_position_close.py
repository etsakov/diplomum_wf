import requests
import json
import oandapyV20
import oandapyV20.endpoints.positions as positions

access_token="d612e5b6e0f902b605207883dded35bc-8928c64998a13c444885331fd77cf935"
accountID = "101-004-6259640-001"
instrument = "EUR_USD"

data = {
        "longUnits": "ALL"
}

# TO DO - find out how to close not ALL positions but a particular trade!!!

client = oandapyV20.API(access_token = access_token)
r = positions.PositionClose(accountID= accountID, instrument = instrument, data = data)
client.request(r)
print(r.response)
