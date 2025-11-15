import pandas as pd
import numpy as np

def generate_signals(
    df,
    high_vol_trend: int,
    atr_period: int = 14,
    atr_multiplier: float = 1.0,
    ma_window: int = 30
):
    """
    根據市場特徵與統計結論，產生交易訊號 (參數化版本，已修復迴歸錯誤)。

    Args:
        df: 包含特徵的 Pandas DataFrame。
        high_vol_trend: 高波動後的趨勢方向 (-1 或 1)。
        atr_period (int): 用於尋找 ATR 欄位的週期。
        atr_multiplier (float): ATR 閾值的倍數。
        ma_window (int): 用於計算 ATR 移動平均的窗口。

    Returns:
        一個附加了 'signal' 及多個輔助欄位的 DataFrame。
    """
    df_signal = df.copy()
    atr_col = f'ATR_{atr_period}'

    if atr_col not in df_signal.columns:
        raise ValueError(f"輸入的 DataFrame 中缺少 '{atr_col}' 欄位。")

    # --- 1. 定義波動狀態 ---
    df_signal['ATR_MA'] = df_signal[atr_col].rolling(window=ma_window).mean()
    df_signal['is_high_vol'] = df_signal[atr_col] > (df_signal['ATR_MA'] * atr_multiplier)

    # --- 2. 產生基礎訊號 ---
    df_signal['signal'] = np.where(df_signal['is_high_vol'], high_vol_trend, 0)

    # --- 3. 重新加入輔助欄位以修復迴歸 ---
    df_signal['signal_reason'] = np.where(
        df_signal['is_high_vol'],
        f"High Volatility {'Long' if high_vol_trend == 1 else 'Short'}",
        "No Signal"
    )
    df_signal['signal_generated_at'] = df_signal.index
    df_signal['signal_exec_when'] = df_signal.index + pd.Timedelta(days=1)

    # --- 4. 清理與格式化 ---
    df_signal = df_signal.drop(columns=['ATR_MA', 'is_high_vol'])
    df_signal['signal'] = df_signal['signal'].astype(int)

    return df_signal

def adjust_signals_for_execution(df_with_signals, max_delay_days: int = 3):
    import pandas as pd
    df_adjusted = df_with_signals.copy()
    trading_days = pd.to_datetime(df_adjusted.index)
    signal_days = df_adjusted[df_adjusted['signal'] != 0].index
    for day in signal_days:
        # 確保 'signal_exec_when' 欄位存在
        if 'signal_exec_when' in df_adjusted.columns:
            ideal_exec_date = df_adjusted.loc[day, 'signal_exec_when']
            future_trading_days = trading_days[trading_days >= ideal_exec_date]
            if not future_trading_days.empty:
                actual_exec_date = future_trading_days[0]
                delay = (actual_exec_date - ideal_exec_date).days
                if delay <= max_delay_days:
                    df_adjusted.loc[day, 'signal_exec_when'] = actual_exec_date
                    df_adjusted.loc[day, 'signal_reason'] += f" (Delayed {delay}d)"
                else:
                    df_adjusted.loc[day, 'signal'] = 0
                    df_adjusted.loc[day, 'signal_reason'] = f"Cancelled (Delay > {max_delay_days}d)"
            else:
                df_adjusted.loc[day, 'signal'] = 0
                df_adjusted.loc[day, 'signal_reason'] = "Cancelled (No Future Trading Day)"
    return df_adjusted

def generate_buy_and_hold_signals(df: pd.DataFrame) -> pd.DataFrame:
    df_signal = df.copy()
    df_signal['signal'] = 1
    df_signal['signal_reason'] = "Buy and Hold Strategy"
    # 為 adjust_signals_for_execution 函式提供必要的欄位
    df_signal['signal_generated_at'] = df_signal.index
    df_signal['signal_exec_when'] = df_signal.index + pd.Timedelta(days=1)

    if len(df_signal) > 1:
        df_signal.iloc[-2, df_signal.columns.get_loc('signal')] = 0
        df_signal.iloc[-2, df_signal.columns.get_loc('signal_reason')] = "Signal to Close Position for Backtest End"
        df_signal.iloc[-1, df_signal.columns.get_loc('signal')] = 0
        df_signal.iloc[-1, df_signal.columns.get_loc('signal_reason')] = "Position Closed"
    return df_signal

def generate_bollinger_band_signals(
    df: pd.DataFrame,
    sma_long_period: int = 200,
    bband_period: int = 20,
    bband_stddev: float = 2.0
) -> pd.DataFrame:
    """
    產生基於「順大勢、逆小勢」布林帶策略的交易訊號。

    Args:
        df (pd.DataFrame): 包含價格和指標特徵的 DataFrame。
        sma_long_period (int): 長期 SMA 的週期。
        bband_period (int): 布林帶的週期。
        bband_stddev (float): 布林帶的標準差倍數。

    Returns:
        pd.DataFrame: 包含 'signal' 欄位的 DataFrame。
    """
    df_signal = df.copy()

    # --- 1. 準備欄位名稱 ---
    sma_col = f'SMA_{sma_long_period}'
    bband_stddev_str = str(bband_stddev).replace('.', '_')
    upper_col = f'BB_upper_{bband_period}_{bband_stddev_str}'
    lower_col = f'BB_lower_{bband_period}_{bband_stddev_str}'

    # 檢查必要欄位是否存在
    required_cols = ['Close', sma_col, upper_col, lower_col]
    if not all(col in df_signal.columns for col in required_cols):
        raise ValueError(f"輸入的 DataFrame 缺少必要欄位。需要: {required_cols}")

    # --- 2. 定義進出場條件 (向量化) ---
    close = df_signal['Close']
    sma_long = df_signal[sma_col]
    bb_upper = df_signal[upper_col]
    bb_lower = df_signal[lower_col]

    # 做多條件
    long_trend = close > sma_long
    long_entry_trigger = close < bb_lower
    long_exit_profit_trigger = close > bb_upper # 獲利了結
    long_exit_stop_trigger = close < sma_long # 趨勢反轉停損

    # 做空條件
    short_trend = close < sma_long
    short_entry_trigger = close > bb_upper
    short_exit_profit_trigger = close < bb_lower # 獲利了結
    short_exit_stop_trigger = close > sma_long # 趨勢反轉停損

    # --- 3. 狀態機邏輯 (逐日模擬) ---
    signals = np.zeros(len(df_signal))
    position = 0  # -1 for short, 0 for flat, 1 for long

    for i in range(1, len(df_signal)):
        # --- 空手狀態：尋找進場點 ---
        if position == 0:
            if long_trend.iloc[i] and long_entry_trigger.iloc[i]:
                signals[i] = 1
                position = 1
            elif short_trend.iloc[i] and short_entry_trigger.iloc[i]:
                signals[i] = -1
                position = -1
            else:
                signals[i] = 0 # 保持空手
                position = 0
        # --- 持有多頭部位：尋找出場點 ---
        elif position == 1:
            if long_exit_profit_trigger.iloc[i] or long_exit_stop_trigger.iloc[i]:
                signals[i] = 0  # 產生平倉訊號
                position = 0
            else:
                signals[i] = 1  # 保持持有
                position = 1
        # --- 持有空頭部位：尋找出場點 ---
        elif position == -1:
            if short_exit_profit_trigger.iloc[i] or short_exit_stop_trigger.iloc[i]:
                signals[i] = 0  # 產生平倉訊號
                position = 0
            else:
                signals[i] = -1  # 保持持有
                position = -1

    # 我們只需輸出每日的目標倉位 (0, 1, -1)，回測引擎會處理倉位變化
    df_signal['signal'] = signals.astype(int)
    return df_signal[['signal']]
