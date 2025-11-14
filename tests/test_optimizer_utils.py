import pandas as pd
import pytest
from src.optimizer_utils import create_walk_forward_splits

@pytest.fixture
def sample_time_series_data():
    """建立一個用於測試的、長度為 100 天的時間序列 DataFrame。"""
    dates = pd.to_datetime(pd.date_range(start="2024-01-01", periods=100, freq='D'))
    data = pd.DataFrame({'price': range(100)}, index=dates)
    return data

def test_walk_forward_splits_correct_number_of_splits(sample_time_series_data):
    """測試是否生成了正確數量的數據分割。"""
    splits = list(create_walk_forward_splits(
        data=sample_time_series_data,
        train_period_len=30,
        test_period_len=10,
        step=10
    ))
    # 預期分割數：(100 - 30 - 10) // 10 + 1 = 60 // 10 + 1 = 7
    assert len(splits) == 7

def test_walk_forward_splits_correct_set_lengths(sample_time_series_data):
    """測試每個分割中的訓練集和測試集是否具有正確的長度。"""
    splits = list(create_walk_forward_splits(
        data=sample_time_series_data,
        train_period_len=30,
        test_period_len=10
    ))
    for train_set, test_set in splits:
        assert len(train_set) == 30
        assert len(test_set) == 10

def test_walk_forward_splits_no_overlap_between_test_sets(sample_time_series_data):
    """測試不同分割的測試集之間是否沒有重疊。"""
    splits = list(create_walk_forward_splits(
        data=sample_time_series_data,
        train_period_len=30,
        test_period_len=10,
        step=10 # 步長等於測試集長度，確保無重疊
    ))

    test_indices = [s[1].index for s in splits]

    for i in range(len(test_indices) - 1):
        intersection = test_indices[i].intersection(test_indices[i+1])
        assert len(intersection) == 0

def test_walk_forward_splits_data_is_sequential(sample_time_series_data):
    """測試每個分割中，測試集是否緊跟在訓練集之後。"""
    splits = list(create_walk_forward_splits(
        data=sample_time_series_data,
        train_period_len=30,
        test_period_len=10
    ))
    for train_set, test_set in splits:
        assert train_set.index[-1] + pd.Timedelta(days=1) == test_set.index[0]

def test_walk_forward_splits_handles_non_datetime_index():
    """測試當索引不是 DatetimeIndex 時是否會引發 ValueError。"""
    data = pd.DataFrame({'price': range(10)})
    with pytest.raises(ValueError, match="數據的索引必須是 pandas 的 DatetimeIndex。"):
        list(create_walk_forward_splits(data, 5, 2))

def test_walk_forward_splits_step_parameter(sample_time_series_data):
    """測試 `step` 參數是否能正確控制窗口的移動。"""
    # 預設 step = test_period_len (10)
    splits_default_step = list(create_walk_forward_splits(
        sample_time_series_data, 30, 10
    ))

    # 手動設定 step = 5
    splits_custom_step = list(create_walk_forward_splits(
        sample_time_series_data, 30, 10, step=5
    ))

    # 第二個分割的起始點應該不同
    assert splits_default_step[1][0].index[0] == pd.to_datetime("2024-01-11")
    assert splits_custom_step[1][0].index[0] == pd.to_datetime("2024-01-06")
