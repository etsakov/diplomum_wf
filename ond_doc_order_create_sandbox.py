import requests
import json
import oandapyV20
import oandapyV20.endpoints.orders as orders
from config import ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS


# def stream_rates(ACCESS_TOKEN, ACCOUNT_ID, INSTRUMENTS):
url = 'https://stream-fxpractice.oanda.com/v3/accounts/' + ACCOUNT_ID + '/pricing/stream?instruments=%s' % (INSTRUMENTS)
head = {'Content-type':"application/json",
        'Accept-Datetime-Format':"RFC3339",
        'Authorization':"Bearer " + ACCESS_TOKEN}


r = requests.get(url, headers=head, stream=True)
print(r)

for line in r.iter_lines():

    if line:
        decoded_line = line.decode('utf-8')
        print(json.loads(decoded_line))


# Set the number of units you want to buy "" or sell "-"

amount_of_units = 100
direction = ''
units_quantity = direction + str(amount_of_units)

data = {
        "order": {
        "timeInForce": "FOK",
        "instrument": INSTRUMENTS,
        "units": units_quantity,  
        "type": "MARKET",
        "positionFill": "DEFAULT",
        "takeProfitOnFill": {
            "timeInForce": "GTC",
            "price": "1.16700"
        }
    }
}

client = oandapyV20.API(access_token = ACCESS_TOKEN)
r = orders.OrderCreate(accountID = ACCOUNT_ID, data = data)
client.request(r)
print(r.response)
