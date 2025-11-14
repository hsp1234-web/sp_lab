import pandas as pd
from typing import Generator, Tuple

def create_walk_forward_splits(
    data: pd.DataFrame,
    train_period_len: int,
    test_period_len: int,
    step: int = None
) -> Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]:
    """
    生成滾動前向優化 (Walk-Forward Optimization) 的數據分割。

    Args:
        data (pd.DataFrame): 完整的時間序列數據，索引必須是時間類型。
        train_period_len (int): 每個訓練週期的長度（天數）。
        test_period_len (int): 每個測試週期的長度（天數）。
        step (int, optional): 每個滾動窗口向前移動的步長。
                               如果為 None，則預設為 test_period_len。

    Yields:
        Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]:
        一個生成器，每次回傳一個 (訓練集, 測試集) 的元組。
    """
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("數據的索引必須是 pandas 的 DatetimeIndex。")

    if step is None:
        step = test_period_len

    total_len = len(data)
    start_idx = 0

    while start_idx + train_period_len + test_period_len <= total_len:
        train_end_idx = start_idx + train_period_len
        test_end_idx = train_end_idx + test_period_len

        train_set = data.iloc[start_idx:train_end_idx]
        test_set = data.iloc[train_end_idx:test_end_idx]

        yield train_set, test_set

        start_idx += step
