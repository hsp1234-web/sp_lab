import pandas as pd

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    執行保守的資料清洗策略，僅確保資料的一致性。

    此函式遵循「忠實保留原始資料」的原則，執行以下操作：
    1. 確保 DataFrame 的索引是唯一的。若有重複，則保留第一個出現的項目。
    2. 確保 DataFrame 的索引是按時間順序排序的。

    所有原始欄位和 NaN 值都會被完整保留。

    Args:
        df: 包含時間序列資料的原始 Pandas DataFrame。

    Returns:
        一個索引經過排序和去重處理的新的 Pandas DataFrame。
    """
    # 複製一份資料以避免修改原始 DataFrame
    df_cleaned = df.copy()

    # 1. 移除重複的索引，保留第一個出現的
    #    首先檢查索引是否唯一，以避免不必要的計算
    if not df_cleaned.index.is_unique:
        df_cleaned = df_cleaned[~df_cleaned.index.duplicated(keep='first')]

    # 2. 排序索引
    #    首先檢查索引是否已排序，以避免不必要的計算
    if not df_cleaned.index.is_monotonic_increasing:
        df_cleaned = df_cleaned.sort_index()

    return df_cleaned
