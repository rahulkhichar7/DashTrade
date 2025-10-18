import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class Portfolio:
    def __init__(self, data, signal, initial_cash, commission=0.0005, slippage=0.001,
                 intraday=False, trade_quantity_on_signal=2):
        self.data = data.copy()
        self.data['signal'] = signal['signal'] if isinstance(signal, pd.DataFrame) else signal
        self.initial_cash = float(initial_cash)
        self.commission = float(commission)
        self.slippage = float(slippage)
        self.intraday = intraday
        self.trade_quantity_on_signal = int(trade_quantity_on_signal)

        self.equity_data = pd.DataFrame(
            index=self.data.index,
            columns=['cash', 'position_value', 'total_equity']
        )

    def apply_slippage(self, price, direction):
        if direction == 'buy':
            return price * (1 + self.slippage)
        elif direction == 'sell':
            return price * (1 - self.slippage)
        return price

    def simulate(self):
        cash = float(self.initial_cash)
        position_size = 0      # +ve = long shares, -ve = short shares

        if len(self.data) == 0:
            return

        first_close = self.data['close'].iloc[0]
        self.equity_data.iloc[0] = {
            'cash': cash,
            'position_value': position_size * first_close,
            'total_equity': cash + position_size * first_close
        }

        for i in range(1, len(self.data)):
            prev_close = self.data['close'].iloc[i-1]
            open_price = self.data['open'].iloc[i]
            signal = self.data['signal'].iloc[i-1]

            # Update start-of-day equity based on previous close
            self.equity_data.iloc[i-1] = {
                'cash': cash,
                'position_value': position_size * prev_close,
                'total_equity': cash + position_size * prev_close
            }

            # ---- BUY SIGNAL ----
            if signal == 1:
                # Step 1: If currently short, buy back everything first
                if self.intraday and position_size < 0:
                    exec_price = self.apply_slippage(open_price, 'buy')
                    shares_to_buy_back = abs(position_size)
                    cost = shares_to_buy_back * exec_price
                    commission_amt = cost * self.commission
                    cash -= (cost + commission_amt)
                    position_size = 0 

                # Step 2: Buy fresh long position if possible
                exec_price = self.apply_slippage(open_price, 'buy')

                effective_cash = cash * (1 - self.commission)
                max_shares = int(effective_cash / exec_price)
                shares_to_buy = min(max_shares, self.trade_quantity_on_signal)

                if shares_to_buy > 0:
                    cost = shares_to_buy * exec_price
                    commission_amt = cost * self.commission
                    if cash >= cost + commission_amt:
                        cash -= (cost + commission_amt)
                        position_size += shares_to_buy  

            # ---- SELL SIGNAL ----
            elif signal == -1:
                # Step 1: If currently long, sell all holdings first
                if position_size > 0:
                    exec_price = self.apply_slippage(open_price, 'sell')
                    revenue = position_size * exec_price
                    commission_amt = revenue * self.commission
                    cash += (revenue - commission_amt)
                    position_size = 0  # longs fully closed

                # Step 2: If intraday, open new short position
                if self.intraday:
                    exec_price = self.apply_slippage(open_price, 'sell')
                    effective_cash = cash * (1 - self.commission)
                    max_shares = int(effective_cash / exec_price)
                    shares_to_short = min(max_shares, self.trade_quantity_on_signal)

                    if shares_to_short > 0:
                        revenue = shares_to_short * exec_price
                        commission_amt = revenue * self.commission
                        cash += (revenue - commission_amt)
                        position_size -= shares_to_short  

        # Record final day's equity using last close
        last_close = self.data['close'].iloc[-1]
        self.equity_data.iloc[-1] = {
            'cash': cash,
            'position_value': position_size * last_close,
            'total_equity': cash + position_size * last_close
        }

        # Save final state
        self.final_cash = cash
        self.final_position = position_size
        self.final_equity = cash + position_size * last_close
    
    def metrics(self, risk_free_rate =0, periods_per_year = 252):
        eq = self.equity_data['total_equity'].astype(float).dropna()
        if eq.empty:
            raise RuntimeError("Run simulate() before metrics()")

        returns = eq.pct_change().dropna()

        # --- Total Return ---
        total_return = eq.iloc[-1] / eq.iloc[0] - 1

        # --- CAGR ---
        days = (eq.index[-1] - eq.index[0]).days
        years = days / 365.25 if days > 0 else 1
        CAGR = (eq.iloc[-1] / eq.iloc[0])**(1/years) - 1 if years > 0 else np.nan

        # --- Volatility (annualized) ---
        volatility = returns.std() * np.sqrt(periods_per_year)

        # --- Sharpe Ratio ---
        excess_ret = returns - risk_free_rate/periods_per_year
        sharpe = (excess_ret.mean() / returns.std()) * np.sqrt(periods_per_year) if returns.std() != 0 else np.nan

        # --- Max Drawdown ---
        rolling_max = eq.cummax()
        drawdown = (eq - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        # --- Win Rate & Profit Factor ---
        win_rate = (returns > 0).mean()
        gross_profit = returns[returns > 0].sum()
        gross_loss = -returns[returns < 0].sum()
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else np.nan

        return {
            "Total Return (%)": round(total_return*100, 2),
            "CAGR (%)": round(CAGR*100, 2),
            "Volatility": round(volatility, 2),
            "Sharpe Ratio": round(sharpe, 2),
            "Max Drawdown (%)": round(max_drawdown*100, 2),
            "Win Rate (%)": round(win_rate*100, 2),
            "Profit Factor": round(profit_factor, 2)
        }

    def plot_equity(self):
        if self.equity_data['total_equity'].isnull().all():
            raise RuntimeError("Run simulate() first.")
        plt.figure(figsize=(10, 4))
        self.equity_data['total_equity'].astype(float).plot(title='Equity Curve')
        plt.xlabel('Date')
        plt.ylabel('Total Equity')
        plt.grid(True)
        plt.show()

    def analyse(self, risk_free_rate=0, periods_per_year=252):
        if self.equity_data['total_equity'].isnull().all():
            raise RuntimeError("Run simulate() first.")

        results = { 
            "Total Return": [],
            "CAGR": [],
            "Volatility": [],
            "Sharpe Ratio": [],
            "Max Drawdown": [],
            "Win Rate": [],
            "Profit Factor": []
        }

        eq = self.equity_data['total_equity'].astype(float).dropna()

        for end_idx in range(1, len(eq)):
            sub_eq = eq.iloc[:end_idx+1]
            sub_returns = sub_eq.pct_change().dropna()

            # --- Total Return ---
            total_return = sub_eq.iloc[-1] / sub_eq.iloc[0] - 1

            # --- CAGR ---
            days = (sub_eq.index[-1] - sub_eq.index[0]).days
            years = days / 365.25 if days > 0 else 1
            CAGR = (sub_eq.iloc[-1] / sub_eq.iloc[0])**(1/years) - 1 if years > 0 else np.nan

            # --- Volatility ---
            volatility = sub_returns.std() * np.sqrt(periods_per_year) if not sub_returns.empty else np.nan

            # --- Sharpe Ratio ---
            if not sub_returns.empty and sub_returns.std() != 0:
                excess_ret = sub_returns - risk_free_rate/periods_per_year
                sharpe = (excess_ret.mean() / sub_returns.std()) * np.sqrt(periods_per_year)
            else:
                sharpe = np.nan

            # --- Max Drawdown ---
            rolling_max = sub_eq.cummax()
            drawdown = (sub_eq - rolling_max) / rolling_max
            max_drawdown = drawdown.min()

            # --- Win Rate & Profit Factor ---
            win_rate = (sub_returns > 0).mean() if not sub_returns.empty else np.nan
            gross_profit = sub_returns[sub_returns > 0].sum()
            gross_loss = -sub_returns[sub_returns < 0].sum()
            profit_factor = gross_profit / gross_loss if gross_loss != 0 else np.nan

            results["Total Return"].append(total_return)
            results["CAGR"].append(CAGR)
            results["Volatility"].append(volatility)
            results["Sharpe Ratio"].append(sharpe)
            results["Max Drawdown"].append(max_drawdown)
            results["Win Rate"].append(win_rate)
            results["Profit Factor"].append(profit_factor)

        return pd.DataFrame(results, index=eq.index[1:])
