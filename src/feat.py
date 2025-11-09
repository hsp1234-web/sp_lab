import pandas as pd
import pandas_ta as ta
import numpy as np

def create_features(df: pd.DataFrame, atr_period: int = 14, fast_ma: int = 20, slow_ma: int = 60) -> pd.DataFrame:
    """
    根據輸入的日線資料 DataFrame，計算多項技術指標特徵。

    此函式遵循「忠實保留原始資料」的原則，計算出的新特徵欄位將會
    附加到原始 DataFrame 的後方，原始的 OHLCV 欄位不會被修改。
    計算過程中產生的 NaN 值會被直接保留。

    Args:
        df: 包含 'Open', 'High', 'Low', 'Close', 'Volume' 欄位的
            乾淨 Pandas DataFrame。
        atr_period (int): 計算 ATR 的週期。
        fast_ma (int): 計算快速移動平均線的週期。
        slow_ma (int): 計算慢速移動平均線的週期。

    Returns:
        一個包含原始資料以及新增特徵欄位的新的 Pandas DataFrame。
    """
    # 複製一份資料以避免修改原始 DataFrame
    df_feat = df.copy()

    # 1. 計算移動平均線 (SMA)
    df_feat[f'SMA_{fast_ma}'] = df_feat['Close'].rolling(window=fast_ma).mean()
    df_feat[f'SMA_{slow_ma}'] = df_feat['Close'].rolling(window=slow_ma).mean()

    # 2. 計算平均真實波幅 (ATR)
    # pandas-ta 會自動尋找 High, Low, Close 欄位
    df_feat[f'ATR_{atr_period}'] = ta.atr(high=df_feat['High'], low=df_feat['Low'], close=df_feat['Close'], length=atr_period)

    # 3. 計算日報酬率
    # 簡單報酬率
    df_feat['RET_SIMPLE'] = df_feat['Close'].pct_change()
    # 對數報酬率
    df_feat['RET_LOG'] = np.log(df_feat['Close'] / df_feat['Close'].shift(1))

    return df_feat
