import json
import math

import requests
from fyers_api import accessToken, fyersModel
from flask import Flask, render_template, request, redirect, send_file, url_for
from flask import Flask
from flask import request
import webbrowser
import yfinance as yf
from ta.trend import ADXIndicator
import datetime
import pandas as pd
import time


app = Flask(__name__)

redirect_url = "http://127.0.0.1:8099/process_authcode_from_fyers"
response_t = "code"
state = "sample_state"




# To get client_id and client_secret from user and pass to fyers api
@app.route("/getauthcode", methods=['POST'])
def getauthcode():
    global client_id
    client_id = request.form.get('client_id')
    global client_secret
    client_secret = request.form.get('client_secret')
    session = accessToken.SessionModel(
        client_id=client_id,
        secret_key=client_secret,
        redirect_uri=redirect_url,
        response_type=response_t
    )

    response = session.generate_authcode()
    webbrowser.open(response)
    return response


# Fyres api will call back this methid with auth code. This method will use that auth code to generate access token
@app.route("/process_authcode_from_fyers")
def process_authcode_from_fyers():
    try:
        authcode = request.args.get('auth_code')
        session = accessToken.SessionModel(
            client_id=client_id,
            secret_key=client_secret,
            redirect_uri=redirect_url,
            response_type=response_t,
            grant_type="authorization_code"
        )
        session.set_token(authcode)
        response = session.generate_token()
        global access_token
        access_token = response["access_token"]
        print("access token ", access_token)
        global refresh_token
        refresh_token = response["refresh_token"]
        return render_template('authorized.html')
    except Exception as e:
        return {"status": "Failed", "data": str(e)}



# User Profile
@app.route("/get_client_details")
def get_client_details():

    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="/logs")
    response = fyers.get_profile()
    print(response)
    return response


# User funds
@app.route("/get_client_funds_available")
def get_client_funds_available():

    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="/logs")
    response = fyers.funds()
    print(response)
    return response


# User holdings
@app.route("/get_client_holdings")
def get_client_holdings():
    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="/logs")
    response = fyers.holdings()
    print(response)
    return response


#User orders in current day
@app.route("/get_client_orders")
def get_client_orders():
    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="/logs")
    response = fyers.orderbook()
    print(response)
    return response


# User positions in current day
@app.route("/get_client_positions")
def get_client_positions():
    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="/logs")
    response = fyers.positions()
    print(response)
    return response


# User trades in current day
@app.route("/get_client_trades")
def get_client_trades():
    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="/logs")
    response = fyers.tradebook()
    print(response)
    return response


# Get history data for a particular symbol
@app.route("/get_history")
def get_history():
    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="/logs")

    data = {
        "symbol": "NSE:SBIN-EQ",
        "resolution": "D",
        "date_format": "0",
        "range_from": "1622097600",
        "range_to": "1622097685",
        "cont_flag": "1"
    }

    response = fyers.history(data=data)
    print(response)
    return response


# Get adx values for 1 minute time interval
@app.route("/get_adx_value")
def get_adx_value():
    try:
        # Download Nifty index data for a 1-minute timeframe
        nifty_data = yf.download("^NSEI", interval="1m")

        # Extract the high, low, close prices
        high = nifty_data["High"]
        low = nifty_data["Low"]
        close = nifty_data["Close"]

        # Calculate the ADX
        adx_indicator = ADXIndicator(high, low, close, window=14)
        adx = adx_indicator.adx()

        # Get last value from adx series
        last_adx = adx.iloc[-1]

        # Print the ADX values
        print(last_adx)

        return last_adx
    except Exception as e:
        print (e)


def time_in_range(start, end, current):
    """Returns whether current is in the range [start, end]"""
    return start <= current <= end


def is_it_trade_time():
    start_first_time_window = datetime.time(5, 25, 0)
    end_first_time_window = datetime.time(11, 45, 0)
    current_first_time_window = datetime.datetime.now().time()
    first_time_window = time_in_range(start_first_time_window, end_first_time_window, current_first_time_window)
    if first_time_window == False:
        start_second_time_window = datetime.time(12, 45, 0)
        end_second_time_window = datetime.time(2, 30, 0)
        current_second_time_window = datetime.datetime.now().time()
        second_time_window = time_in_range(start_second_time_window, end_second_time_window, current_second_time_window)

    if first_time_window:
        print ("Time is morning trade time")
        return True
    elif second_time_window:
        print ("Time is noon trade time")
        return True
    else:
        print ("Not a trade time")
        return False


def strikeprice_dataframe_from_nse():
    # Variable initiations for getting strike price from NSE website
    url = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36 Edg/103.0.1264.37',
        'accept-encoding': 'gzip, deflate, br', 'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8'}
    session = requests.Session()
    request = session.get(url, headers=headers)
    cookies = dict(request.cookies)

    response = session.get(url, headers=headers, cookies=cookies).json()
    rawdata = pd.DataFrame(response)
    rawop = pd.DataFrame(rawdata['filtered']['data']).fillna(0)
    data = []
    for i in range(0, len(rawop)):
        calloi = callcoi = cltp = putoi = putcoi = pltp = 0
        stp = rawop['strikePrice'][i]
        if (rawop['CE'][i] == 0):
            calloi = callcoi = 0
        else:
            calloi = rawop['CE'][i]['openInterest']
            callcoi = rawop['CE'][i]['changeinOpenInterest']
            cltp = rawop['CE'][i]['lastPrice']
        if (rawop['PE'][i] == 0):
            putoi = putcoi = 0
        else:
            putoi = rawop['PE'][i]['openInterest']
            putcoi = rawop['PE'][i]['changeinOpenInterest']
            pltp = rawop['PE'][i]['lastPrice']
        opdata = {
            #             'CALL OI': calloi, 'CALL CHNG OI': callcoi, 'CALL LTP': cltp, 'STRIKE PRICE': stp,
            #             'PUT OI': putoi, 'PUT CHNG OI': putcoi, 'PUT LTP': pltp
            'CALL LTP': cltp, 'STRIKE PRICE': stp, 'PUT LTP': pltp
        }

        data.append(opdata)
    optionchain = pd.DataFrame(data)
    return optionchain


def calculate_ma(symbol, window):
    data = yf.download(symbol, interval="1m")
    smma = data['Close'].rolling(window).mean().ewm(alpha=1/window, adjust=False).mean()
    sma = data['Close'].rolling(window).mean()
    datetime =data.index
    ma_data = pd.DataFrame({'datetime': datetime, 'SMMA': smma, 'SMA': sma}, index=data.index)
    return ma_data


def calculate_crossover(ma_data):
    crossover_list = []
    for ind in ma_data.index:

        smma = ma_data['SMMA'][ind]
        sma = ma_data['SMA'][ind]
        time = ma_data['datetime'][ind]

        if not (math.isnan(smma)) & (math.isnan(sma)):
            if (int(smma) - int(sma)) == 0:
                #                 print(int(smma), int(sma))
                #                 print("crossover on " + str(time) + str(int(sma)))
                crossover_list.append(str(time))
    return crossover_list


# Initiate ADX based trade
@app.route("/initiate_adx_trade", methods=['POST'])
def initiate_adx_trade():

    # Get instrument name from the request form
    instrument = request.form.get('instrument')

    # Check if the current time is a trade time
    trade_time = is_it_trade_time()
    # print(trade_time)
    # return str(trade_time)

    # Check and get Strike value for the respective instrument using Regex
    if trade_time:
        optionchain = strikeprice_dataframe_from_nse()
        call_strikeprice_df = optionchain[optionchain["CALL LTP"].ge(120) & optionchain["CALL LTP"].lt(150)]["STRIKE PRICE"]
        put_strikeprice_df = optionchain[optionchain["PUT LTP"].ge(120) & optionchain["PUT LTP"].lt(150)]["STRIKE PRICE"]

        call_strikeprice_list = call_strikeprice_df.tolist()
        put_strikeprice_list = put_strikeprice_df.tolist()

        print(call_strikeprice_list)
        print(put_strikeprice_list)

        # Get ADX value for Call option
        if not call_strikeprice_list:
            print("No strike price available")
        else:
            adx_value = get_adx_value()
            if (adx_value > 19.7):
                # check smma sma crossover
                symbol = '^NSEI'
                window = 7
                ma_data = calculate_ma(symbol, window)
                crossover_list = calculate_crossover(ma_data)
                print(crossover_list)

        # Get ADX value for Put option
        if not put_strikeprice_list:
            print("No strike price available")
        else:
            adx_value = get_adx_value()
            if (adx_value > 19.7):
                # check smma sma crossover
                symbol = '^NSEI'
                window = 7
                ma_data = calculate_ma(symbol, window)
                crossover_list = calculate_crossover(ma_data)
                print(crossover_list)




        return "True"



















# @cross_origin("*")
@app.route('/gui')
def gui():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="8099", debug=False)