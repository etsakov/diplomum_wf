import requests
import oandapyV20
import oandapyV20.endpoints.accounts as accounts
from datetime import datetime
from optparse import OptionParser
from config import ACCESS_TOKEN, ACCOUNT_ID

domainDict = { 'live' : 'stream-fxtrade.oanda.com',
               'demo' : 'stream-fxpractice.oanda.com' }
# Replace the following variables with your personal values 
environment = 'demo' # Replace this 'live' if you wish to connect to the live environment 
domain = domainDict[environment] 


def statement_indication(access_token, account_id):
    client = oandapyV20.API(access_token = ACCESS_TOKEN)
    account_statement = accounts.AccountDetails(ACCOUNT_ID)
    client.request(account_statement)
    return account_statement.response

unstructured_info = statement_indication(ACCESS_TOKEN, ACCOUNT_ID)

# TO DO - extract structured info from Positions Opened and from Trades Opened by each trade:
# Positions_Opened:  [{'financing': '0.0000', 'long': {'financing': '0.0000', 'pl': '0.0001', 'averagePrice': '1.14423', 'units': '3', 'tradeIDs': ['12', '22', '24'], 'unrealizedPL': '-0.0015', 'resettablePL': '0.0001'}, 'pl': '0.0001', 'commission': '0.0000', 'short': {'units': '0', 'financing': '0.0000', 'pl': '0.0000', 'unrealizedPL': '0.0000', 'resettablePL': '0.0000'}, 'instrument': 'EUR_USD', 'unrealizedPL': '-0.0015', 'resettablePL': '0.0001'}]
# Position_Value:  3.0003
# Number_Of_Trades_Open:  3
# Trades_Opened:  [{'financing': '0.0000', 'initialUnits': '1', 'id': '12', 'realizedPL': '0.0000', 'currentUnits': '1', 'unrealizedPL': '-0.0010', 'instrument': 'EUR_USD', 'openTime': '2017-07-17T07:25:01.254668809Z', 'price': '1.14477', 'state': 'OPEN'}, {'financing': '0.0000', 'initialUnits': '1', 'id': '22', 'realizedPL': '0.0000', 'currentUnits': '1', 'unrealizedPL': '-0.0004', 'instrument': 'EUR_USD', 'openTime': '2017-07-17T07:38:58.887873575Z', 'price': '1.14412', 'state': 'OPEN'}, {'financing': '0.0000', 'initialUnits': '1', 'id': '24', 'realizedPL': '0.0000', 'currentUnits': '1', 'unrealizedPL': '-0.0001', 'instrument': 'EUR_USD', 'openTime': '2017-07-17T07:42:16.561283375Z', 'price': '1.14379', 'state': 'OPEN'}]

def show_general_info(unstructured_info):
    for item in unstructured_info:
        statement_info = dict()
        statement_info["time"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        statement_info["account_id"] = unstructured_info["account"]["id"]
        statement_info["last_transaction_id"] = unstructured_info["lastTransactionID"]
        statement_info["number_of_trades_open"] = unstructured_info["account"]["openTradeCount"]
        statement_info["leverage"] = unstructured_info["account"]["marginRate"]
        statement_info["margin_closeout"] = unstructured_info["account"]["marginCloseoutPositionValue"]
        statement_info["currency"] = unstructured_info["account"]["currency"]
        statement_info["withdrawal_limit"] = unstructured_info["account"]["withdrawalLimit"]
        statement_info["financing"] = unstructured_info["account"]["financing"]
        statement_info["margin_call_%"] = unstructured_info["account"]["marginCallPercent"]
        statement_info["margin_used"] = unstructured_info["account"]["marginUsed"]
        statement_info["positions_opened"] = unstructured_info["account"]["positions"]
        statement_info["trades_opened"] = unstructured_info["account"]["trades"]
        statement_info["position_value"] = unstructured_info["account"]["positionValue"]
        statement_info["balance"] = unstructured_info["account"]["balance"]
        statement_info["orders_opened"] = unstructured_info["account"]["orders"]
        statement_info["unrealized_profit_loss"] = unstructured_info["account"]["unrealizedPL"]
        statement_info["account_type"] = unstructured_info["account"]["alias"]
        statement_info["number_positions_opened"] = unstructured_info["account"]["openPositionCount"]
        statement_info["available_margin"] = unstructured_info["account"]["marginAvailable"]
        statement_info["hedge_available"] = unstructured_info["account"]["hedgingEnabled"]
        statement_info["profit_or_loss"] = unstructured_info["account"]["pl"]
        statement_info["number_of_pending_orders"] = unstructured_info["account"]["pendingOrderCount"]
        return statement_info

def show_current_state_info(statement_info):
    print("----------------------------------")
    print("time: ".title(), statement_info["time"])
    print("account_id: ".title(), statement_info["account_id"])
    print("account_type: ".title(), statement_info["account_type"])
    print("currency: ".title(), statement_info["currency"])
    print("hedge_available: ".title(), statement_info["hedge_available"])
    print("----------------------------------")
    print("number_positions_opened: ".title(), statement_info["number_positions_opened"])
    print("leverage: ".title(), statement_info["leverage"])
    print("positions_opened: ".title(), statement_info["positions_opened"])
    print("position_value: ".title(), statement_info["position_value"])
    print("number_of_trades_open: ".title(), statement_info["number_of_trades_open"])
    print("trades_opened: ".title(), statement_info["trades_opened"])
    print("orders_opened: ".title(), statement_info["orders_opened"])
    print("unrealized_profit_loss: ".title(), statement_info["unrealized_profit_loss"])
    print("balance: ".title(), statement_info["balance"])
    print("withdrawal_limit: ".title(), statement_info["withdrawal_limit"])
    print("profit_or_loss: ".title(), statement_info["profit_or_loss"])
    print("----------------------------------")
    print("financing: ".title(), statement_info["financing"])
    print("margin_closeout: ".title(), statement_info["margin_closeout"])
    print("margin_call_%: ".title(), statement_info["margin_call_%"])
    print("margin_used: ".title(), statement_info["margin_used"])
    print("available_margin: ".title(), statement_info["available_margin"])
    print("----------------------------------")
    print("number_of_pending_orders: ".title(), statement_info["number_of_pending_orders"])
    print("last transaction id: ".title(), statement_info["last_transaction_id"])
    print("----------------------------------")

if __name__=="__main__":
    unstructured_info = statement_indication(ACCESS_TOKEN, ACCOUNT_ID)
    statement_info = show_general_info(unstructured_info)
    show_current_state_info(statement_info)
    # print(unstructured_info)
    # print(show_general_info(unstructured_info))


# {'account': {'marginRate': '0.1', 'withdrawalLimit': '0.0000', 'marginUsed': '989.9052', 
# 'marginAvailable': '0.0000', 'positions': [{'commission': '0.0000', 'unrealizedPL': '-13.6789', 
# 'long': {'financing': '-0.0008', 'resettablePL': '-0.8711', 'unrealizedPL': '0.0000', 
# 'pl': '-0.8711', 'units': '0'}, 'financing': '0.0026', 'resettablePL': '1.9997', 
# 'instrument': 'EUR_USD', 'pl': '1.9997', 'short': {'unrealizedPL': '-13.6789', 
# 'resettablePL': '2.8708', 'financing': '0.0034', 'averagePrice': '1.14701', 
# 'tradeIDs': ['90', '93', '96', '101', '106', '111', '114', '117'], 'pl': '2.8708', 
# 'units': '-9900'}}], 'trades': [
# {'takeProfitOrderID': '91', 'price': '1.14674', 
# 'unrealizedPL': '-8.0976', 'openTime': '2017-07-17T14:05:25.537551276Z', 
# 'currentUnits': '-5000', 'state': 'OPEN', 'realizedPL': '0.0000', 'financing': '0.0000', 
# 'instrument': 'EUR_USD', 'initialUnits': '-5000', 'id': '90'}, 
# {'takeProfitOrderID': '94', 'price': '1.14696', 'unrealizedPL': '-1.4280', 
# 'openTime': '2017-07-17T14:10:48.174438940Z', 'currentUnits': '-1000', 'state': 
# 'OPEN', 'realizedPL': '0.0000', 'financing': '0.0000', 'instrument': 'EUR_USD', 
# 'initialUnits': '-1000', 'id': '93'}, 
# {'takeProfitOrderID': '99', 'price': '1.14711', 'unrealizedPL': '-1.2974', 
# 'openTime': '2017-07-17T14:13:11.687776464Z', 'currentUnits': '-1000', 'state': 
# 'OPEN', 'realizedPL': '0.0000', 'financing': '0.0000', 'instrument': 'EUR_USD', 
# 'initialUnits': '-1000', 'id': '96'}, 
# {'takeProfitOrderID': '109', 'price': '1.14731', 'unrealizedPL': '-1.1232', 
# 'openTime': '2017-07-17T14:14:51.769523606Z', 'currentUnits': '-1000', 'state': 
# 'OPEN', 'realizedPL': '0.0000', 'financing': '0.0000', 'instrument': 'EUR_USD', 
# 'initialUnits': '-1000', 'id': '101'}, 
# {'takeProfitOrderID': '107', 'price': '1.14747', 'unrealizedPL': '-0.9839', 
# 'openTime': '2017-07-17T14:15:36.230620347Z', 'currentUnits': '-1000', 'state': 
# 'OPEN', 'realizedPL': '0.0000', 'financing': '0.0000', 'instrument': 'EUR_USD', 
# 'initialUnits': '-1000', 'id': '106'}, 
# {'takeProfitOrderID': '112', 'price': '1.14759', 'unrealizedPL': '-0.4397', 
# 'openTime': '2017-07-17T14:19:25.573073173Z', 'currentUnits': '-500', 'state': 
# 'OPEN', 'realizedPL': '0.0000', 'financing': '0.0000', 'instrument': 'EUR_USD', 
# 'initialUnits': '-500', 'id': '111'}, 
# {'takeProfitOrderID': '115', 'price': '1.14769', 'unrealizedPL': '-0.2377', 
# 'openTime': '2017-07-17T14:21:29.414172038Z', 'currentUnits': '-300', 'state': 
# 'OPEN', 'realizedPL': '0.0000', 'financing': '0.0000', 'instrument': 'EUR_USD', 
# 'initialUnits': '-300', 'id': '114'}, 
# {'takeProfitOrderID': '118', 'price': '1.14778', 'unrealizedPL': '-0.0714', 
# 'openTime': '2017-07-17T14:25:57.351411775Z', 'currentUnits': '-100', 'state': 
# 'OPEN', 'realizedPL': '0.0000', 'financing': '0.0000', 'instrument': 'EUR_USD', 
# 'initialUnits': '-100', 'id': '117'}], 
# 'marginCloseoutUnrealizedPL': '-13.1880', 'marginCallMarginUsed': '989.9957', 
# 'commission': '0.0000', 'marginCloseoutMarginUsed': '989.9957', 'unrealizedPL': '-13.6789', 
# 'positionValue': '9899.0519', 'marginCloseoutNAV': '988.8143', 
# 'orders': [{'price': '1.14624', 'tradeID': '90', 'createTime': '2017-07-17T14:05:25.537551276Z', 
# 'state': 'PENDING', 'type': 'TAKE_PROFIT', 'timeInForce': 'GTC', 'triggerCondition': 'DEFAULT', 
# 'id': '91'}, 
# {'price': '1.14646', 'tradeID': '93', 'createTime': '2017-07-17T14:10:57.204265911Z', 
# 'state': 'PENDING', 'type': 'TAKE_PROFIT', 'timeInForce': 'GTC', 'triggerCondition': 'DEFAULT', 
# 'id': '94'}, 
# {'price': '1.14666', 'replacesOrderID': '97', 'tradeID': '96', 
# 'createTime': '2017-07-17T14:13:37.600565877Z', 'state': 'PENDING', 'type': 'TAKE_PROFIT', 
# 'timeInForce': 'GTC', 'triggerCondition': 'DEFAULT', 'id': '99'}, 
# {'price': '1.14701', 'tradeID': '106', 'createTime': '2017-07-17T14:15:44.956815395Z', 
# 'state': 'PENDING', 'type': 'TAKE_PROFIT', 'timeInForce': 'GTC', 'triggerCondition': 'DEFAULT', 
# 'id': '107'}, 
# {'price': '1.14681', 'replacesOrderID': '104', 'tradeID': '101', 
# 'createTime': '2017-07-17T14:16:28.170064365Z', 'state': 'PENDING', 'type': 'TAKE_PROFIT', 
# 'timeInForce': 'GTC', 'triggerCondition': 'DEFAULT', 'id': '109'}, 
# {'price': '1.14669', 'tradeID': '111', 'createTime': '2017-07-17T14:19:34.308721739Z', 
# 'state': 'PENDING', 'type': 'TAKE_PROFIT', 'timeInForce': 'GTC', 'triggerCondition': 'DEFAULT', 
# 'id': '112'}, 
# {'price': '1.14680', 'tradeID': '114', 'createTime': '2017-07-17T14:21:40.937960672Z', 
# 'state': 'PENDING', 'type': 'TAKE_PROFIT', 'timeInForce': 'GTC', 'triggerCondition': 'DEFAULT', 
# 'id': '115'}, 
# {'price': '1.14693', 'tradeID': '117', 'createTime': '2017-07-17T14:26:07.239638757Z', 
# 'state': 'PENDING', 'type': 'TAKE_PROFIT', 'timeInForce': 'GTC', 'triggerCondition': 'DEFAULT', 
# 'id': '118'}], 
# 'lastTransactionID': '118', 'NAV': '988.3234', 'hedgingEnabled': False, 'alias': 'Primary', 
# 'pendingOrderCount': 8, 'openPositionCount': 1, 'createdByUserID': 6259640, 'openTradeCount': 8, 
# 'resettablePL': '1.9997', 'marginCallPercent': '1.00119', 
# 'createdTime': '2017-06-24T13:28:09.433699201Z', 'marginCloseoutPercent': '0.50060', 
# 'financing': '0.0026', 'currency': 'EUR', 'pl': '1.9997', 'balance': '1002.0023', 
# 'marginCloseoutPositionValue': '9899.9569', 'id': '101-004-6259640-001'}, 
# 'lastTransactionID': '118'}