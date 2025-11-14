# -*- coding: utf-8 -*-
"""
主執行腳本 (Orchestrator)

這個腳本是整個量化研究專案的單一進入點。它會按照正確的順序，
依序執行從數據獲取、清洗、特徵工程、統計分析、訊號生成、
回測模擬，到最終視覺化報告產出的完整流程。
"""

import os
import pandas as pd

# ----------------------------------------------------------------------------
# 核心模組導入 (更新)
# ----------------------------------------------------------------------------
from src.fetch import download_gspc
from src.clean import clean_data
from src.feat import calculate_features
from src.sp_signal import generate_signals, adjust_signals_for_execution, generate_buy_and_hold_signals
from src.backtest import run_backtest
from src.stats import calculate_backtest_stats # <-- 從 stats 導入
from src.viz import plot_equity_curve

# ----------------------------------------------------------------------------
# 全域設定與路徑管理
# ----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
RAW_DATA_PATH = os.path.join(DATA_DIR, 'raw', 'gspc_raw.parquet')
CLEAN_DATA_PATH = os.path.join(DATA_DIR, 'processed', 'gspc_clean.parquet')
FEATURES_PATH = os.path.join(DATA_DIR, 'processed', 'features.parquet')
SIGNALS_PATH = os.path.join(DATA_DIR, 'processed', 'sp_signals.parquet')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
EQUITY_CURVE_PATH = os.path.join(OUTPUT_DIR, 'sp_equity_curve.jpg')
TRADE_LOG_PATH = os.path.join(OUTPUT_DIR, 'sp_trade_log.csv')

STRATEGY = 'buy_and_hold'
INIT_CAPITAL = 100000.0
POS_SIZE = 100
COST_PARAMS = {
    'fee_per_trade': 1.5,
    'slippage_pct': 0.0001
}

def ensure_directories_exist():
    os.makedirs(os.path.dirname(RAW_DATA_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(CLEAN_DATA_PATH), exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("✅ 資料夾結構已確認。")

# ----------------------------------------------------------------------------
# 主流程執行函式
# ----------------------------------------------------------------------------
def main():
    """
    執行完整的端到端 (End-to-End) 量化研究與回測流程。
    """
    print("--- [ 步驟 0/7 ] 正在準備執行環境 ---")
    ensure_directories_exist()
    print("-" * 40)

    print("--- [ 步驟 1/7 ] 正在下載原始市場數據 ---")
    download_gspc(RAW_DATA_PATH)
    print("✅ 原始數據下載完成。")
    print("-" * 40)

    print("--- [ 步驟 2/7 ] 正在進行數據清洗 ---")
    raw_df = pd.read_parquet(RAW_DATA_PATH)
    clean_df = clean_data(raw_df)
    clean_df.to_parquet(CLEAN_DATA_PATH)
    print(f"✅ 數據清洗完成，已儲存至 {CLEAN_DATA_PATH}")
    print("-" * 40)

    print("--- [ 步驟 3/7 ] 正在計算技術指標特徵 ---")
    features_df = calculate_features(pd.read_parquet(CLEAN_DATA_PATH))
    features_df.to_parquet(FEATURES_PATH)
    print(f"✅ 特徵計算完成，已儲存至 {FEATURES_PATH}")
    print("-" * 40)

    print("--- [ 步驟 4/7 ] 正在生成交易訊號 ---")
    features_df_for_signal = pd.read_parquet(FEATURES_PATH)
    if STRATEGY == 'volatility':
        ideal_signals_df = generate_signals(features_df_for_signal, high_vol_trend=-1, use_sma_filter=False)
        executable_signals_df = adjust_signals_for_execution(ideal_signals_df)
    elif STRATEGY == 'buy_and_hold':
        executable_signals_df = generate_buy_and_hold_signals(features_df_for_signal)
    else:
        raise ValueError(f"未知的策略選項：'{STRATEGY}'")
    executable_signals_df.to_parquet(SIGNALS_PATH)
    print(f"✅ 交易訊號生成完成，已儲存至 {SIGNALS_PATH}")
    print("-" * 40)

    print("--- [ 步驟 5/7 ] 正在執行回測模擬 (包含交易成本) ---")
    trade_log, equity_curve = run_backtest(
        price_data=features_df_for_signal,
        signals=executable_signals_df['signal'],
        init_cap=INIT_CAPITAL,
        pos_size=POS_SIZE,
        cost_mode='simple',
        cost_params=COST_PARAMS
    )
    trade_log.to_csv(TRADE_LOG_PATH)
    print(f"✅ 回測執行完畢，交易日誌已儲存至 {TRADE_LOG_PATH}")
    print("-" * 40)

    print("--- [ 步驟 6/7 ] 正在計算績效指標並產生視覺化圖表 ---")
    # 更新函式呼叫
    performance_metrics = calculate_backtest_stats(
        trade_log=trade_log,
        equity_curve=equity_curve,
        initial_capital=INIT_CAPITAL
    )
    plot_equity_curve(equity_curve, EQUITY_CURVE_PATH, performance_metrics)
    print(f"✅ 權益曲線圖已儲存至 {EQUITY_CURVE_PATH}")
    print("-" * 40)

    print("--- [ 步驟 7/7 ] 正在顯示最終績效報告 ---")
    print("\n========= 最終績效報告 =========\n")
    for metric, value in performance_metrics.items():
        # 格式化輸出
        if isinstance(value, float):
            print(f"{metric:<20}: {value:.4f}")
        else:
            print(f"{metric:<20}: {value}")
    print("\n==================================\n")

    print("\n流程執行完畢。")

if __name__ == "__main__":
    main()
