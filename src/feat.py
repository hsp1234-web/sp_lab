import pandas as pd
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

    Note:
        `pandas-ta` 函式庫的許多功能 (例如 `ta.atr`) 在設計上是針對
        DataFrame 進行操作的，需要同時傳入 High, Low, Close 等欄位。
        直接在單一的 Series 上使用其 `.ta` 擴充功能可能會導致非預期的錯誤。
    """
    # 複製一份資料以避免修改原始 DataFrame
    df_feat = df.copy()

    # 展平 MultiIndex 欄位，例如將 ('Close', '^GSPC') 轉為 'Close'
    if isinstance(df_feat.columns, pd.MultiIndex):
        df_feat.columns = df_feat.columns.get_level_values(0)

    # 1. 計算移動平均線 (SMA)
    df_feat['SMA_20'] = df_feat['Close'].rolling(window=20).mean()
    df_feat['SMA_60'] = df_feat['Close'].rolling(window=60).mean()

    # 2. 計算平均真實波幅 (ATR)
    # 使用 .ta 擴充語法呼叫 ATR 計算
    df_feat.ta.atr(length=14, append=True)

    # 將 pandas-ta 產生的 'ATRr_14' 欄位重命名為 'ATR_14' 以符合下游模組的預期
    if 'ATRr_14' in df_feat.columns:
        df_feat.rename(columns={'ATRr_14': 'ATR_14'}, inplace=True)

    # 3. 計算日報酬率
    # 簡單報酬率
    df_feat['RET_SIMPLE'] = df_feat['Close'].pct_change()
    # 對數報酬率
    df_feat['RET_LOG'] = np.log(df_feat['Close'] / df_feat['Close'].shift(1))

    return df_feat
