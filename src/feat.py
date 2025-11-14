import pandas as pd
import numpy as np
import talib

def calculate_features(df: pd.DataFrame, atr_period: int = 14, sma_short_period: int = 20, sma_long_period: int = 60) -> pd.DataFrame:
    """
    根據輸入的日線資料 DataFrame，計算多項可參數化的技術指標特徵。

    Args:
        df: 包含 'Open', 'High', 'Low', 'Close' 的 DataFrame。
        atr_period (int): ATR 的計算週期。
        sma_short_period (int): 短期 SMA 的計算週期。
        sma_long_period (int): 長期 SMA 的計算週期。

    Returns:
        一個包含原始資料以及新增特徵欄位的新的 Pandas DataFrame。
    """
    df_feat = df.copy()

    if isinstance(df_feat.columns, pd.MultiIndex):
        df_feat.columns = df_feat.columns.get_level_values(0)

    # 1. 計算移動平均線 (SMA)
    df_feat[f'SMA_{sma_short_period}'] = df_feat['Close'].rolling(window=sma_short_period).mean()
    df_feat[f'SMA_{sma_long_period}'] = df_feat['Close'].rolling(window=sma_long_period).mean()

    # 2. 計算平均真實波幅 (ATR)
    high_prices = df_feat['High'].to_numpy(dtype=np.double)
    low_prices = df_feat['Low'].to_numpy(dtype=np.double)
    close_prices = df_feat['Close'].to_numpy(dtype=np.double)

    df_feat[f'ATR_{atr_period}'] = talib.ATR(high_prices, low_prices, close_prices, timeperiod=atr_period)

    # 3. 計算日報酬率
    df_feat['RET_SIMPLE'] = df_feat['Close'].pct_change()
    df_feat['RET_LOG'] = np.log(df_feat['Close'] / df_feat['Close'].shift(1))

    return df_feat
