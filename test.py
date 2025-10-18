import numpy as np
import pandas as pd
from fyers_apiv3 import fyersModel
from config import CLIENT_ID, AUTH_CODE, REDIRECT_URI, RESPONSE_TYPE, STATE, SECRET_KEY, GRANT_TYPE, get_logger

# --- Exchange auth_code for access_token ---
session = fyersModel.SessionModel(
    client_id=CLIENT_ID,
    secret_key=SECRET_KEY,
    redirect_uri=REDIRECT_URI,
    response_type=RESPONSE_TYPE,
    state=STATE,
    grant_type=GRANT_TYPE
)

session.set_token(AUTH_CODE)
response = session.generate_token()

access_token = response.get("access_token")
if not access_token:
    raise SystemExit("Exiting: Could not retrieve access_token")

# --- Initialize Fyers client ---
fyers = fyersModel.FyersModel(
    token=access_token,
    is_async=False,
    client_id=CLIENT_ID
)

# --- Example: Historical data for backtesting ---
data = {
    "symbol": "NSE:RELIANCE-EQ",
    "resolution": "D",       
    "date_format": "1",       # YYYY-MM-DD
    "range_from": "2024-01-01",
    "range_to": "2024-12-31",
    "cont_flag": "1"
}

history = fyers.history(data=data)

# --- Convert to DataFrame ---
if history.get("s") == "ok":
    candles = history["candles"]
    df = pd.DataFrame(candles, columns=["date", "open", "high", "low", "close", "volume"])

    # Convert timestamp to datetime (Fyers gives epoch seconds)
    df["date"] = pd.to_datetime(df["date"], unit="s")
    df.set_index("date", inplace=True)

    # Reorder to OCLHV
    df = df[["open", "close", "low", "high", "volume"]]
print(df.head(1))
