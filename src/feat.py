import pandas as pd
import pandas_ta as ta
import numpy as np

def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    根據輸入的日線資料 DataFrame，計算多項技術指標特徵。

    此函式遵循「忠實保留原始資料」的原則，計算出的新特徵欄位將會
    附加到原始 DataFrame 的後方，原始的 OHLCV 欄位不會被修改。
    計算過程中產生的 NaN 值會被直接保留。

    計算的指標包括：
    - SMA_20: 20日簡單移動平均線 (基於收盤價)
    - SMA_60: 60日簡單移動平均線 (基於收盤價)
    - ATR_14: 14日平均真實波幅
    - RET_SIMPLE: 簡單日報酬率 (基於收盤價)
    - RET_LOG: 對數日報酬率 (基於收盤價)

    Args:
        df: 包含 'Open', 'High', 'Low', 'Close', 'Volume' 欄位的
            乾淨 Pandas DataFrame。

    Returns:
        一個包含原始資料以及新增特徵欄位的新的 Pandas DataFrame。
    """
    # 複製一份資料以避免修改原始 DataFrame
    df_feat = df.copy()

    # 1. 計算移動平均線 (SMA)
    df_feat['SMA_20'] = df_feat['Close'].rolling(window=20).mean()
    df_feat['SMA_60'] = df_feat['Close'].rolling(window=60).mean()

    # 2. 計算平均真實波幅 (ATR)
    # pandas-ta 會自動尋找 High, Low, Close 欄位
    df_feat['ATR_14'] = ta.atr(high=df_feat['High'], low=df_feat['Low'], close=df_feat['Close'], length=14)

    # 3. 計算日報酬率
    # 簡單報酬率
    df_feat['RET_SIMPLE'] = df_feat['Close'].pct_change()
    # 對數報酬率
    df_feat['RET_LOG'] = np.log(df_feat['Close'] / df_feat['Close'].shift(1))

    return df_feat
