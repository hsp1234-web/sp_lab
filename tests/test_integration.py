# tests/test_integration.py
# 端到端整合測試

import pytest
import pandas as pd
import os

from src.backtest import run_backtest
from src.stats import calculate_backtest_stats # <-- 修正導入
from src.viz import plot_equity_curve

@pytest.fixture
def setup_integration_data():
    """建立一個用於端到端測試的微型資料集。"""
    dates = pd.to_datetime([
        '2025-01-02', '2025-01-03', '2025-01-06', '2025-01-07', '2025-01-08'
    ])
    price_data = pd.DataFrame({
        'Open':  [100.0, 110.0, 120.0, 130.0, 140.0],
        'Close': [105.0, 115.0, 125.0, 135.0, 145.0]
    }, index=dates)

    signals = pd.Series(
        [1, 0, -1, 0],
        index=pd.to_datetime(['2025-01-02', '2025-01-03', '2025-01-06', '2025-01-07'])
    )

    cost_params = {"fees_per_unit": 10.0, "slippage_per_unit": 1.0}

    initial_capital = 100000.0

    return price_data, signals, cost_params, initial_capital

def test_full_pipeline(setup_integration_data, tmp_path):
    """
    測試從回測到視覺化的完整流程。
    """
    price_data, signals, cost_params, initial_capital = setup_integration_data

    # 1. 執行回測 (含成本)
    trade_log, equity_curve = run_backtest(
        price_data=price_data,
        signals=signals,
        init_cap=initial_capital,
        pos_size=1,
        cost_mode='simple',
        cost_params=cost_params
    )

    assert not trade_log.empty
    assert not equity_curve.empty

    # 2. 計算績效指標 (更新函式呼叫)
    metrics = calculate_backtest_stats(
        trade_log=trade_log,
        equity_curve=equity_curve,
        initial_capital=initial_capital
    )

    assert '總報酬率' in metrics
    assert '最大回撤 (MDD)' in metrics
    assert '夏普比率' in metrics

    # 3. 產生視覺化圖表
    output_path = tmp_path / "integration_equity_curve.jpg"
    plot_equity_curve(equity_curve, str(output_path))

    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
