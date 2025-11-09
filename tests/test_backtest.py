# tests/test_backtest.py
# 回測引擎測試模組

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

# 預期從 src.backtest 模組匯入回測主函式
from src.backtest import run_backtest

def setup_basic_test_data():
    """建立一個包含基本交易訊號的測試資料集"""
    dates = pd.to_datetime([
        '2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04',
        '2025-01-05', '2025-01-06', '2025-01-07', '2025-01-08'
    ])

    price_data = pd.DataFrame({
        'Open':  [100.0, 110.0, 120.0, 125.0, 130.0, 140.0, 135.0, 130.0],
        'Close': [105.0, 115.0, 125.0, 130.0, 135.0, 145.0, 140.0, 125.0]
    }, index=dates)

    # 訊號在收盤後產生，隔日開盤執行
    # 2025-01-01 (訊號 1) -> 01-02 進場 @ 110
    # 2025-01-03 (訊號 0) -> 01-04 平倉 @ 125
    # 2025-01-05 (訊號 -1) -> 01-06 進場 @ 140
    # 2025-01-07 (訊號 0) -> 01-08 平倉 @ 130
    signals = pd.Series([0] * len(dates), index=dates, name="signal")
    signals.loc['2025-01-01'] = 1
    signals.loc['2025-01-03'] = 0
    signals.loc['2025-01-05'] = -1
    signals.loc['2025-01-07'] = 0

    return price_data, signals

def test_basic_long_short_cycle():
    """
    測試案例 1：基本的多頭與空頭交易循環

    驗證：
    1. 一筆多頭交易 (Long) 的進出場與損益是否正確。
    2. 一筆空頭交易 (Short) 的進出場與損益是否正確。
    3. 最終產出的 trade_log 格式與內容是否符合規格。
    """
    price_data, signals = setup_basic_test_data()

        # 根據 T-1 訊號, 在 T 開盤執行的邏輯，重新計算預期結果
        # Long:  Entry @ 110 (01-02), Exit @ 120 (01-03), PnL = 10
        # Short: Entry @ 140 (01-06), Exit @ 135 (01-07), PnL = 5
    expected_log_data = [
        {
            "trade_id": 1,
            "entry_date": pd.to_datetime("2025-01-02"),
                "exit_date": pd.to_datetime("2025-01-03"),
            "direction": "Long",
            "entry_price": 110.0,
                "exit_price": 120.0,
            "quantity": 1,
                "pnl": 10.0,
                "realized_pnl": 10.0, # 第一次平倉
            "fees": 0,
            "notes": ""
        },
        {
            "trade_id": 2,
            "entry_date": pd.to_datetime("2025-01-06"),
                "exit_date": pd.to_datetime("2025-01-07"),
            "direction": "Short",
                "entry_price": 140.0,
                "exit_price": 135.0,
            "quantity": 1,
                "pnl": 5.0,
                "realized_pnl": 15.0, # 10 + 5
            "fees": 0,
            "notes": ""
        }
    ]

    expected_trade_log = pd.DataFrame(expected_log_data)

    # 執行回測 (預期此函式尚未實作)
    trade_log, equity_curve = run_backtest(
        price_data=price_data,
        signals=signals,
        init_cap=100000,
        pos_size=1
    )

    # 比較實際產出的交易日誌與預期結果
    # 比較實際產出的交易日誌與預期結果
    assert_frame_equal(trade_log, expected_trade_log)


def test_stop_and_reverse():
    """
    測試案例 2：停損並反向 (Stop-and-Reverse)

    驗證：
    1. 當訊號由 1 (Long) 直接轉為 -1 (Short) 時，能夠正確地「先平倉、再反向開倉」。
    2. 多頭部位的出場時間與空頭部位的進場時間應為同一日。
    3. 交易價格應為同一日的開盤價。
    """
    dates = pd.to_datetime(['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04'])
    price_data = pd.DataFrame({
        'Open':  [100.0, 110.0, 120.0, 130.0],
        'Close': [105.0, 115.0, 125.0, 135.0]
    }, index=dates)

    # 訊號：進場 -> 反向 -> 平倉
    # 01-01 (訊號 1)  -> 01-02 Long  @ 110
    # 01-02 (訊號 -1) -> 01-03 Close Long @ 120, Open Short @ 120
    # 01-03 (訊號 0)  -> 01-04 Close Short @ 130
    signals = pd.Series([1, -1, 0, 0], index=dates, name="signal")

    expected_log_data = [
        {
            "trade_id": 1,
            "entry_date": pd.to_datetime("2025-01-02"),
            "exit_date": pd.to_datetime("2025-01-03"),
            "direction": "Long",
            "entry_price": 110.0,
            "exit_price": 120.0,
            "quantity": 1,
            "pnl": 10.0,
                "realized_pnl": 10.0,
            "fees": 0,
            "notes": ""
        },
        {
            "trade_id": 2,
            "entry_date": pd.to_datetime("2025-01-03"),
            "exit_date": pd.to_datetime("2025-01-04"),
            "direction": "Short",
            "entry_price": 120.0,
            "exit_price": 130.0,
            "quantity": 1,
                "pnl": -10.0,
                "realized_pnl": 0.0, # 10 + (-10)
            "fees": 0,
            "notes": ""
        }
    ]
    expected_trade_log = pd.DataFrame(expected_log_data)

    trade_log, _ = run_backtest(
        price_data=price_data,
        signals=signals,
        init_cap=100000,
        pos_size=1
    )

    assert_frame_equal(trade_log, expected_trade_log)


def test_equity_tracking():
    """
    測試案例 4：權益曲線與未實現損益追蹤

    驗證：
    1. 每日權益的計算是否正確，包含已實現與未實現損益。
    2. 空手時，權益應等於初始資金 + 已實現損益。
    3. 持倉時，權益應額外計入按當日收盤價計算的未實現損益。
    """
    price_data, signals = setup_basic_test_data()
    init_cap = 100000

    # 手動計算預期權益曲線
    # 2025-01-01: 空手 -> 100000
    # 2025-01-02: 開盤 @ 110 進場 Long, 收盤 @ 115. 未實現損益 = (115-110)*1 = 5. 權益 = 100005
    # 2025-01-03: 開盤 @ 120 平倉. 已實現損益 = (120-110)*1 = 10. 權益 = 100010
    # 2025-01-04: 空手. 權益 = 100010
    # 2025-01-05: 空手. 權益 = 100010
    # 2025-01-06: 開盤 @ 140 進場 Short, 收盤 @ 145. 未實現損益 = (140-145)*1 = -5. 權益 = 100010 - 5 = 100005
    # 2025-01-07: 開盤 @ 135 平倉. 已實現損益 = (140-135)*1 = 5. 總已實現損益 = 10+5=15. 權益 = 100015
    # 2025-01-08: 空手. 權益 = 100015

    expected_equity_values = [
        100000.0, 100005.0, 100010.0, 100010.0, 100010.0, 100005.0, 100015.0, 100015.0
    ]
    expected_equity_curve = pd.Series(
        expected_equity_values,
        index=price_data.index,
        name="equity"
    )

    _, equity_curve = run_backtest(
        price_data=price_data,
        signals=signals,
        init_cap=init_cap,
        pos_size=1
    )

    assert_series_equal(equity_curve['equity'], expected_equity_curve, check_names=False)


def test_trade_cancellation():
    """
    測試案例 5：交易因延遲過久而取消

    驗證：
    1. 當訊號的執行延遲天數超過 max_delay 上限時，該交易應被取消。
    2. trade_log 中應只包含未被取消的交易。
    """
    # 01-02 的訊號應在 01-03 正常執行。
    # 01-03 的訊號應因延遲超過 2 天，而在 01-08 被取消。
    dates = pd.to_datetime(['2025-01-02', '2025-01-03', '2025-01-08'])
    price_data = pd.DataFrame({
        'Open':  [100.0, 110.0, 120.0],
        'Close': [105.0, 115.0, 125.0]
    }, index=dates)

    signals = pd.Series(
        [1, -1],
        index=[pd.to_datetime('2025-01-02'), pd.to_datetime('2025-01-03')]
    )

    trade_log, _ = run_backtest(
        price_data=price_data,
        signals=signals,
        init_cap=100000,
        pos_size=1,
        max_delay=2
    )

    assert len(trade_log) == 1, "應只有一筆交易被執行"
    assert trade_log.iloc[0]['direction'] == 'Long', "被執行的應為第一筆 Long 交易"


def test_execution_delay():
    """
    測試案例 3：交易執行延遲

    驗證：
    1. 當訊號產生後的隔天為非交易日（例如週末）時，交易應順延至下一個可交易日。
    2. entry_date 應為實際成交的日期。
    """
    # 建立一個包含週末的日期序列 (01-03 是週五, 01-04/05 是週末)
    dates = pd.to_datetime(['2025-01-03', '2025-01-06', '2025-01-07'])
    price_data = pd.DataFrame({
        'Open':  [100.0, 110.0, 120.0],
        'Close': [105.0, 115.0, 125.0]
    }, index=dates)

    # 訊號在週五收盤後產生，應在下週一開盤執行
    signals = pd.Series([1, 0, 0], index=dates, name="signal")

    expected_log_data = [
        {
            "trade_id": 1,
                "entry_date": pd.to_datetime("2025-01-06"),
            "exit_date": pd.to_datetime("2025-01-07"),
            "direction": "Long",
                "entry_price": 110.0,
            "exit_price": 120.0,
            "quantity": 1,
            "pnl": 10.0,
                "realized_pnl": 10.0,
            "fees": 0,
                "notes": "" # 根據新的延遲計算邏輯，這裡應該是 0 天延遲
        }
    ]
    expected_trade_log = pd.DataFrame(expected_log_data)

    trade_log, _ = run_backtest(
        price_data=price_data,
        signals=signals,
        init_cap=100000,
        pos_size=1,
        max_delay=3 # 設定延遲上限
    )

    assert_frame_equal(trade_log, expected_trade_log)
