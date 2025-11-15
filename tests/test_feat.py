import pandas as pd
import numpy as np
import pytest
from src.feat import calculate_features

# 定義測試檔案路徑
CLEAN_DATA_PATH = "tests/sample_parquets/clean_gspc_for_feat.parquet"

# --- Fixtures ---

@pytest.fixture(scope="module")
def sample_dataframe() -> pd.DataFrame:
    """載入特徵工程用的乾淨樣本 DataFrame。"""
    return pd.read_parquet(CLEAN_DATA_PATH)

@pytest.fixture(scope="module")
def default_features_df(sample_dataframe: pd.DataFrame) -> pd.DataFrame:
    """使用預設參數執行特徵計算。"""
    return calculate_features(sample_dataframe)

@pytest.fixture(scope="module")
def custom_features_df(sample_dataframe: pd.DataFrame) -> pd.DataFrame:
    """使用自訂參數執行特徵計算，以進行更具體的測試。"""
    return calculate_features(
        sample_dataframe,
        sma_long_period=30,
        bband_period=10,
        bband_stddev=1.5
    )

# --- 測試函式 ---

def test_sma_long_values(custom_features_df: pd.DataFrame, sample_dataframe: pd.DataFrame):
    """驗證長期 SMA 的數值是否正確 (使用自訂參數)。"""
    period = 30
    col_name = f'SMA_{period}'

    # 第 30 筆資料 (index 29) 的 SMA 應為前 30 筆 Close 的平均
    expected_sma = sample_dataframe['Close'].iloc[:period].mean()
    actual_sma = custom_features_df[col_name].iloc[period - 1]
    assert np.isclose(actual_sma, expected_sma), f"{col_name} 計算不正確。"

def test_default_sma_is_nan(default_features_df: pd.DataFrame):
    """驗證在小樣本數據上，預設的 SMA_200 應全部為 NaN。"""
    # 由於我們的樣本資料只有 40 筆，預設的 SMA_200 應該全部都是 NaN
    assert default_features_df['SMA_200'].isna().all(), "預設 SMA_200 應全部為 NaN。"

def test_bollinger_bands_values(custom_features_df: pd.DataFrame):
    """驗證布林帶的數值是否合理 (使用自訂參數)。"""
    period = 10
    stddev = 1.5
    stddev_str = "1_5"
    upper_col = f'BB_upper_{period}_{stddev_str}'
    middle_col = f'BB_middle_{period}_{stddev_str}'
    lower_col = f'BB_lower_{period}_{stddev_str}'

    # 驗證欄位是否存在
    assert upper_col in custom_features_df.columns
    assert middle_col in custom_features_df.columns
    assert lower_col in custom_features_df.columns

    # 驗證關係：Upper >= Middle >= Lower
    assert (custom_features_df[upper_col].dropna() >= custom_features_df[middle_col].dropna()).all()
    assert (custom_features_df[middle_col].dropna() >= custom_features_df[lower_col].dropna()).all()

    # 驗證第一個非 NaN 值的位置 (TA-Lib 需要 period-1 的暖機期)
    assert not pd.isna(custom_features_df[upper_col].iloc[period - 1])
    assert pd.isna(custom_features_df[upper_col].iloc[period - 2])

def test_atr_values(default_features_df: pd.DataFrame):
    """驗證預設 ATR_14 的數值是否正確。"""
    atr_col = 'ATR_14'
    # TA-Lib 的 ATR 實作需要 14 個週期來 '暖機'，因此第一個非 NaN 值出現在第 15 天 (索引 14)
    assert not pd.isna(default_features_df[atr_col].iloc[14]), f"{atr_col} 在第 15 天應有值。"
    assert (default_features_df[atr_col].dropna() > 0).all(), f"{atr_col} 應為正數。"

def test_returns_values(default_features_df: pd.DataFrame, sample_dataframe: pd.DataFrame):
    """驗證日報酬率的數值是否正確。"""
    # 驗證第二筆資料 (index 1) 的報酬率
    prev_close = sample_dataframe['Close'].iloc[0]
    current_close = sample_dataframe['Close'].iloc[1]

    expected_ret_simple = (current_close / prev_close) - 1
    actual_ret_simple = default_features_df['RET_SIMPLE'].iloc[1]
    assert np.isclose(actual_ret_simple, expected_ret_simple), "RET_SIMPLE 計算不正確。"

def test_nan_preservation(custom_features_df: pd.DataFrame):
    """驗證不同指標的起始期 NaN 是否被正確保留 (使用自訂參數)。"""
    # SMA_30 的前 29 筆應為 NaN
    assert custom_features_df['SMA_30'].iloc[:29].isna().all()
    assert not pd.isna(custom_features_df['SMA_30'].iloc[29])

    # BBands_10 的前 9 筆應為 NaN
    assert custom_features_df['BB_upper_10_1_5'].iloc[:9].isna().all()
    assert not pd.isna(custom_features_df['BB_upper_10_1_5'].iloc[9])

def test_original_data_unchanged(default_features_df: pd.DataFrame, sample_dataframe: pd.DataFrame):
    """驗證原始欄位在新增特徵後保持不變。"""
    original_columns = sample_dataframe.columns
    pd.testing.assert_frame_equal(
        default_features_df[original_columns],
        sample_dataframe
    ), "原始 OHLCV 欄位不應被修改。"
