from fyers_apiv3 import fyersModel
import pandas as pd

from config import CLIENT_ID, SECRET_KEY, REDIRECT_URI, AUTH_CODE, get_logger

printf = get_logger("data")

class FyersData:
    def __init__(self):
        # Create session model
        appSession = fyersModel.SessionModel(
            client_id=CLIENT_ID, secret_key=SECRET_KEY, redirect_uri=REDIRECT_URI,
            response_type="code", grant_type="authorization_code"
        )

        appSession.set_token(AUTH_CODE)
        response = "NOT DEFINED"
        try:
            response = appSession.generate_token()
            ACCESS_TOKEN = response["access_token"]
        except Exception as e:
            printf(f"{str(e)}: {response}")
            exit()
        self.fyers = fyersModel.FyersModel(token=ACCESS_TOKEN, is_async=False, client_id=CLIENT_ID, log_path="log")

    def get_data(self, symbol, resolution, date_format, range_from, range_to, cont_flag, oi_flag):
        headers = {
             'symbol': symbol, 'resolution': resolution, 'date_format': date_format,
             'range_from': range_from, 'range_to': range_to, 'cont_flag': cont_flag,
             'oi_flag': oi_flag
        }
        try:
            printf(f"Downloading data for {symbol}")
            response = self.fyers.history(headers)
            if response.get('code') != 200 or 'candles' not in response:
                printf(f"Error downloading data: {response}")
                return None
            else:
                printf("Formatting data into pandas DataFrame")
                return self.format_data(response['candles'])
        except Exception as e:
            printf(f"An exception occurred: {e}")
            return None

    def format_data(self, candles):
 # API candle data -> pandas DataFrame
       df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
       df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
       df.set_index('timestamp', inplace=True)
       return df