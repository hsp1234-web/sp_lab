# tests/test_viz.py
# 視覺化模組測試

import pytest
import pandas as pd
import os
from src.viz import plot_equity_curve, calculate_performance_metrics

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


def test_calculate_performance_metrics(sample_equity_curve):
    """
    測試績效指標計算是否正確。
    """
    # 預期結果
    # Total Return = (102000 - 100000) / 100000 = 0.02
    # MDD:
    #   - p1=101000, d1=99000, dd1 = (101000-99000)/101000 = 0.0198...
    #   - MDD = 0.01980198...
    # Sharpe Ratio: (假設無風險利率為0, 交易日為252天)
    #   - daily_returns = [0.0099, -0.0198, 0.0303]
    #   - mean = 0.0068, std = 0.025
    #   - sharpe = (0.0068 / 0.025) * sqrt(252) = 4.3...

    expected_metrics = {
        'total_return': 0.02,
        'max_drawdown': pytest.approx(0.01980, abs=1e-5),
        'sharpe_ratio': pytest.approx(4.304, abs=1e-3)
    }

    metrics = calculate_performance_metrics(sample_equity_curve)

    assert metrics['total_return'] == expected_metrics['total_return']
    assert metrics['max_drawdown'] == expected_metrics['max_drawdown']
    assert metrics['sharpe_ratio'] == expected_metrics['sharpe_ratio']
