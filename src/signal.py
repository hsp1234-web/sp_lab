import pandas as pd
import numpy as np

def generate_signals(df: pd.DataFrame, fast_ma: int, slow_ma: int) -> pd.Series:
    """
    根據移動平均線交叉策略生成交易訊號。

    Args:
        df (pd.DataFrame): 包含特徵的 DataFrame。
        fast_ma (int): 快速移動平均線的週期。
        slow_ma (int): 慢速移動平均線的週期。

    Returns:
        pd.Series: 包含交易訊號 (1, -1, 0) 的 Series。
    """
    fast_ma_col = f'SMA_{fast_ma}'
    slow_ma_col = f'SMA_{slow_ma}'

    if fast_ma_col not in df.columns or slow_ma_col not in df.columns:
        raise ValueError("錯誤: 找不到指定的 SMA 欄位。")

    # 產生訊號
    signals = pd.Series(0, index=df.index)
    signals[df[fast_ma_col] > df[slow_ma_col]] = 1
    signals[df[fast_ma_col] < df[slow_ma_col]] = -1
    return signals

def adjust_signals_for_execution(signals: pd.Series, data: pd.DataFrame) -> pd.Series:
    """
    調整訊號以符合 T+1 執行。
    T+1 意味著在 T-1 收盤時產生的訊號，在 T 開盤時執行。
    在我們的向量化回測中，這相當於將訊號向前移動一個時間單位。
    """
    # 將訊號向前移動一個週期，以模擬 T+1 執行
    # fill_value=0 表示移動後產生的 NaN 用 0 填充
    return signals.shift(1).fillna(0).astype(int)
