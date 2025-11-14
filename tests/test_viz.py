# tests/test_viz.py
# 視覺化模組測試

import pytest
import pandas as pd
import os
from src.viz import plot_equity_curve # <-- 移除多餘的導入

@pytest.fixture
def sample_equity_curve():
    """提供一個用於測試的樣本權益曲線 DataFrame。"""
    dates = pd.to_datetime(['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04'])
    equity = [100000, 101000, 99000, 102000]
    return pd.DataFrame({'equity': equity}, index=dates)

def test_plot_equity_curve_creates_file(sample_equity_curve, tmp_path):
    """
    測試 plot_equity_curve 是否能成功建立一個圖表檔案。
    """
    # tmp_path 是 pytest 提供的一個 fixture，用於建立臨時檔案目錄
    output_path = tmp_path / "equity_curve.jpg"

    # 呼叫函式
    plot_equity_curve(
        equity_curve=sample_equity_curve,
        output_path=str(output_path)
    )

    # 斷言檔案是否存在
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0 # 確保檔案不是空的
