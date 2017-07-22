import json
import oandapyV20
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.accounts as accounts
from config import ACCESS_TOKEN, ACCOUNT_ID


def statement_unstructured_info(access_token, account_id):
    # Returns complete account info as dict
    client = oandapyV20.API(access_token = ACCESS_TOKEN)
    account_statement = accounts.AccountDetails(ACCOUNT_ID)
    client.request(account_statement)
    info_unstructured = account_statement.response
    return info_unstructured


def read_statement_unstructured_info(info_unstructured):
    # Gets only info attributed to active trades
    all_trades = info_unstructured['account']['trades']
    all_trades_info = dict()
    item = 0
    for trade in all_trades:
        all_trades_info['trade_' + str(item)] = all_trades[item]
        item += 1
    return all_trades_info


def transaction_close(ACCESS_TOKEN, ACCOUNT_ID, units_quantity, trade_id):
    # Close a trade according to its id and quantity of units
    client = oandapyV20.API(access_token = ACCESS_TOKEN)
    data = {
        "units" : units_quantity
    }

    r = trades.TradeClose(accountID = ACCOUNT_ID, data = data, tradeID = trade_id)
    client.request(r)
    print(r.response)


if __name__=="__main__":
    info_unstructured = statement_unstructured_info(ACCESS_TOKEN, ACCOUNT_ID)
    all_trades_info = read_statement_unstructured_info(info_unstructured)

    # This Loop closes all trades
    unit = 0
    for item in all_trades_info:

        units_quantity = all_trades_info['trade_' + str(unit)]['currentUnits'].replace('-', '')
        trade_id = all_trades_info['trade_' + str(unit)]['id']
        transaction_close(ACCESS_TOKEN, ACCOUNT_ID, units_quantity, trade_id)

        unit += 1

