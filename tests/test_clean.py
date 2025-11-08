import pandas as pd
import numpy as np
import pytest
from src.clean import clean_data

# 定義測試檔案路徑
DIRTY_DATA_PATH = "tests/sample_parquets/dirty_gspc.parquet"

@pytest.fixture
def dirty_dataframe() -> pd.DataFrame:
    """載入測試用的髒資料 DataFrame。"""
    return pd.read_parquet(DIRTY_DATA_PATH)

def test_clean_data_logic(dirty_dataframe):
    """
    測試 clean_data 函式是否能正確處理排序與重複索引，
    同時確保不改變原始資料的內容（欄位與 NaN 值）。
    """
    # 1. 執行目標函式
    cleaned_df = clean_data(dirty_dataframe)

    # 2. 驗證索引的正確性
    assert cleaned_df.index.is_unique, "清洗後的索引應為唯一值，無重複。"
    assert cleaned_df.index.is_monotonic_increasing, "清洗後的索引應為單調遞增。"

    # 3. 驗證欄位是否被完整保留
    assert dirty_dataframe.columns.equals(cleaned_df.columns), "所有原始欄位都應被保留。"

    # 4. 驗證 NaN 值是否被保留
    # 檢查 '2023-01-06' 的 'Open' 和 'Volume' 是否仍然是 NaN
    assert pd.isna(cleaned_df.loc['2023-01-06', 'Open']), "Open 欄位的 NaN 值應被保留。"
    assert pd.isna(cleaned_df.loc['2023-01-06', 'Volume']), "Volume 欄位的 NaN 值應被保留。"

    # 5. 驗證去重邏輯是否正確 (保留第一個)
    # 原始資料中 '2023-01-03' 的第一筆 Open 是 102.0
    expected_open_on_duplicate_date = 102.0
    actual_open_on_duplicate_date = cleaned_df.loc['2023-01-03', 'Open']
    assert actual_open_on_duplicate_date == expected_open_on_duplicate_date, \
        f"重複索引的資料應保留第一筆，預期 Open 為 {expected_open_on_duplicate_date}，但得到 {actual_open_on_duplicate_date}。"

    # 6. 驗證資料筆數是否正確
    # 原始 5 筆，去除 1 筆重複後，應為 4 筆
    assert len(cleaned_df) == 4, f"預期清洗後有 4 筆資料，但得到 {len(cleaned_df)} 筆。"
