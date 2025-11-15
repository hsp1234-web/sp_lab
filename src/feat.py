import pandas as pd
import numpy as np
import talib

def calculate_features(
    df: pd.DataFrame,
    sma_long_period: int = 200,
    bband_period: int = 20,
    bband_stddev: float = 2.0,
    atr_period: int = 14
) -> pd.DataFrame:
    """
    根據輸入的日線資料 DataFrame，計算多項可參數化的技術指標特徵。
    此版本專為「順大勢、逆小勢」布林帶策略設計，並保留舊指標以供相容。

    Args:
        df: 包含 'Open', 'High', 'Low', 'Close' 的 DataFrame。
        sma_long_period (int): 長期 SMA 的計算週期，用於定義大趨勢。
        bband_period (int): 布林帶的計算週期。
        bband_stddev (float): 布林帶的標準差倍數。
        atr_period (int): ATR 的計算週期 (為舊策略或未來擴充保留)。

    Returns:
        一個包含原始資料以及新增特徵欄位的新的 Pandas DataFrame。
    """
    df_feat = df.copy()

    if isinstance(df_feat.columns, pd.MultiIndex):
        df_feat.columns = df_feat.columns.get_level_values(0)

    # --- 準備 TA-Lib 所需的 NumPy 陣列 ---
    high_prices = df_feat['High'].to_numpy(dtype=np.double)
    low_prices = df_feat['Low'].to_numpy(dtype=np.double)
    close_prices = df_feat['Close'].to_numpy(dtype=np.double)

    # --- 新策略所需指標 ---
    # 1. 計算長期移動平均線 (SMA_long)
    df_feat[f'SMA_{sma_long_period}'] = talib.SMA(close_prices, timeperiod=sma_long_period)

    # 2. 計算布林帶 (Bollinger Bands)
    upper, middle, lower = talib.BBANDS(
        close_prices,
        timeperiod=bband_period,
        nbdevup=bband_stddev,
        nbdevdn=bband_stddev,
        matype=0  # SMA
    )
    # 使用 format 確保小數點能正確顯示在欄位名稱中
    bband_stddev_str = str(bband_stddev).replace('.', '_')
    df_feat[f'BB_upper_{bband_period}_{bband_stddev_str}'] = upper
    df_feat[f'BB_middle_{bband_period}_{bband_stddev_str}'] = middle
    df_feat[f'BB_lower_{bband_period}_{bband_stddev_str}'] = lower


    # --- 其他指標 (為舊策略或未來擴充保留) ---
    # 3. 計算平均真實波幅 (ATR)
    df_feat[f'ATR_{atr_period}'] = talib.ATR(high_prices, low_prices, close_prices, timeperiod=atr_period)

    # 4. 計算日報酬率
    df_feat['RET_SIMPLE'] = df_feat['Close'].pct_change()
    df_feat['RET_LOG'] = np.log(df_feat['Close'] / df_feat['Close'].shift(1))

    return df_feat
