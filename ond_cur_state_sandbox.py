import requests
import oandapyV20
import oandapyV20.endpoints.accounts as accounts
from datetime import datetime
from config import ACCESS_TOKEN, ACCOUNT_ID
import time

def statement_indication(ACCESS_TOKEN, ACCOUNT_ID):
    e = 0
    while e != 1:
        client = oandapyV20.API(access_token = ACCESS_TOKEN)
        account_statement = accounts.AccountDetails(ACCOUNT_ID)
        client.request(account_statement)
        units_available = format(float(account_statement.response["account"]["marginAvailable"]) / float(account_statement.response["account"]["marginRate"]), '.0f')
        yield units_available
        time.sleep(1)

for i in statement_indication(ACCESS_TOKEN, ACCOUNT_ID):
    print(i)