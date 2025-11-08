import pandas as pd
import numpy as np
import pytest
from src.feat import calculate_features # 預期從 src/feat.py 導入函式

# 定義測試檔案路徑
CLEAN_DATA_PATH = "tests/sample_parquets/clean_gspc_for_feat.parquet"

@pytest.fixture(scope="module")
def sample_dataframe() -> pd.DataFrame:
    """載入特徵工程用的乾淨樣本 DataFrame。"""
    return pd.read_parquet(CLEAN_DATA_PATH)

@pytest.fixture(scope="module")
def features_dataframe(sample_dataframe) -> pd.DataFrame:
    """執行特徵計算並回傳結果 DataFrame。"""
    return calculate_features(sample_dataframe)

def test_sma_values(features_dataframe, sample_dataframe):
    """驗證 SMA_20 和 SMA_60 的數值是否正確。"""
    # SMA_20: 第 20 筆資料 (index 19) 的 SMA 應為前 20 筆 Close 的平均
    expected_sma_20 = sample_dataframe['Close'].iloc[:20].mean()
    actual_sma_20 = features_dataframe['SMA_20'].iloc[19]
    assert np.isclose(actual_sma_20, expected_sma_20), "SMA_20 計算不正確。"

    # 由於我們的資料只有 40 筆，SMA_60 應該全部都是 NaN
    assert features_dataframe['SMA_60'].isna().all(), "SMA_60 應全部為 NaN。"

def test_atr_values(features_dataframe, sample_dataframe):
    """驗證 ATR_14 的數值是否正確。"""
    # 由於 ATR 的遞歸計算特性，直接驗證一個手動計算的值比較困難。
    # 我們這裡採用一個簡化的驗證：ATR 值應該是正數。
    # 更精確的驗證可以在需要時，針對一個極小的 DataFrame 進行。
    assert (features_dataframe['ATR_14'].dropna() > 0).all(), "ATR 應為正數。"

    # 驗證第 14 筆資料 (index 13) 的 ATR 不為 NaN
    assert not pd.isna(features_dataframe['ATR_14'].iloc[13]), "ATR_14 在第 14 天應有值。"

def test_returns(features_dataframe, sample_dataframe):
    """驗證 RET_SIMPLE 和 RET_LOG 的數值是否正確。"""
    # 驗證第二筆資料 (index 1) 的報酬率
    prev_close = sample_dataframe['Close'].iloc[0]
    current_close = sample_dataframe['Close'].iloc[1]

    expected_ret_simple = (current_close / prev_close) - 1
    actual_ret_simple = features_dataframe['RET_SIMPLE'].iloc[1]
    assert np.isclose(actual_ret_simple, expected_ret_simple), "RET_SIMPLE 計算不正確。"

    expected_ret_log = np.log(current_close / prev_close)
    actual_ret_log = features_dataframe['RET_LOG'].iloc[1]
    assert np.isclose(actual_ret_log, expected_ret_log), "RET_LOG 計算不正確。"

def test_nan_preserved(features_dataframe):
    """驗證起始期的 NaN 在輸出中仍存在。"""
    # SMA_20 的前 19 筆應為 NaN
    assert features_dataframe['SMA_20'].iloc[:19].isna().all(), "SMA_20 的前 19 筆應為 NaN。"
    assert not pd.isna(features_dataframe['SMA_20'].iloc[19]), "SMA_20 的第 20 筆不應為 NaN。"

    # ATR_14 的前 13 筆應為 NaN (Talib 的 ATR 實作在第 14 天會有第一個值)
    assert features_dataframe['ATR_14'].iloc[:13].isna().all(), "ATR_14 的前 13 筆應為 NaN。"
    assert not pd.isna(features_dataframe['ATR_14'].iloc[13]), "ATR_14 的第 14 筆不應為 NaN。"

    # RET_* 的第一筆應為 NaN
    assert pd.isna(features_dataframe['RET_SIMPLE'].iloc[0]), "RET_SIMPLE 的第一筆應為 NaN。"
    assert pd.isna(features_dataframe['RET_LOG'].iloc[0]), "RET_LOG 的第一筆應為 NaN。"

def test_original_data_unchanged(features_dataframe, sample_dataframe):
    """驗證原始欄位在新增特徵後保持不變。"""
    original_columns = sample_dataframe.columns
    pd.testing.assert_frame_equal(
        features_dataframe[original_columns],
        sample_dataframe
    ), "原始 OHLCV 欄位不應被修改。"
