# -*- coding: utf-8 -*-
"""
主執行腳本 (Orchestrator)

這個腳本是整個量化研究專案的單一進入點。它會按照正確的順序，
依序執行從數據獲取、清洗、特徵工程、統計分析、訊號生成、
回測模擬，到最終視覺化報告產出的完整流程。

設計這個主腳本的目的，是為了讓整個複雜的流程可以被一鍵觸發，
特別是在像 Google Colab 這樣的遠端環境中，能確保流程的
一致性與可重現性。
"""

import os
import pandas as pd

# ----------------------------------------------------------------------------
# 核心模組導入 (使用絕對導入)
# ----------------------------------------------------------------------------
# 這裡我們直接導入位於 src 目錄下的模組。
# 為了讓這個腳本在 Colab 環境中能被 `%run` 指令正確執行，
# 呼叫它的 Notebook 必須先把 `src` 目錄的路徑加入到 `sys.path` 中。

from src.fetch import download_gspc
from src.clean import clean_data
from src.feat import calculate_features
from src.sp_signal import generate_signals, adjust_signals_for_execution
from src.backtest import run_backtest
from src.cost import calculate_simple_cost
from src.viz import plot_equity_curve, calculate_performance_metrics

# ----------------------------------------------------------------------------
# 全域設定與路徑管理
# ----------------------------------------------------------------------------
# 我們將所有會用到的檔案路徑和重要的回測參數，統一在這裡進行管理。
# 這樣做的好處是，未來如果需要調整檔案儲存位置或修改回測設定，
# 只需在這個區塊進行修改即可，無需改動下方的執行流程。

# --- 路徑設定 ---
# 建立一個相對於目前腳本位置的 `data` 和 `output` 資料夾路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data') # 退回到專案根目錄，再進入 data
RAW_DATA_PATH = os.path.join(DATA_DIR, 'raw', 'gspc_raw.parquet')
CLEAN_DATA_PATH = os.path.join(DATA_DIR, 'processed', 'gspc_clean.parquet')
FEATURES_PATH = os.path.join(DATA_DIR, 'processed', 'features.parquet')
SIGNALS_PATH = os.path.join(DATA_DIR, 'processed', 'sp_signals.parquet')

OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
EQUITY_CURVE_PATH = os.path.join(OUTPUT_DIR, 'sp_equity_curve.jpg')
TRADE_LOG_PATH = os.path.join(OUTPUT_DIR, 'sp_trade_log.csv')

# --- 回測參數 ---
INIT_CAPITAL = 100000.0  # 初始資金
POS_SIZE = 100          # 每次交易的部位大小
COST_PARAMS = {         # 交易成本參數
    'fee_per_trade': 1.5, # 每筆交易固定手續費
    'slippage_pct': 0.0001 # 滑價成本 (百分比)
}

def ensure_directories_exist():
    """
    確保所有需要的數據和輸出資料夾都存在，如果不存在則自動建立。
    """
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
    # --- 步驟 0: 環境準備 ---
    print("--- [ 步驟 0/7 ] 正在準備執行環境 ---")
    ensure_directories_exist()
    print("-" * 40)

    # --- 步驟 1: 數據獲取 ---
    print("--- [ 步驟 1/7 ] 正在下載原始市場數據 ---")
    download_gspc(RAW_DATA_PATH)
    print("✅ 原始數據下載完成。")
    print("-" * 40)

    # --- 步驟 2: 數據清洗 ---
    print("--- [ 步驟 2/7 ] 正在進行數據清洗 ---")
    raw_df = pd.read_parquet(RAW_DATA_PATH)
    clean_df = clean_data(raw_df)
    clean_df.to_parquet(CLEAN_DATA_PATH)
    print(f"✅ 數據清洗完成，已儲存至 {CLEAN_DATA_PATH}")
    print("-" * 40)

    # --- 步驟 3: 特徵工程 ---
    print("--- [ 步驟 3/7 ] 正在計算技術指標特徵 ---")
    # 重新讀取 clean_df 以確保索引正確
    clean_df_for_feat = pd.read_parquet(CLEAN_DATA_PATH)
    features_df = calculate_features(clean_df_for_feat)
    features_df.to_parquet(FEATURES_PATH)
    print(f"✅ 特徵計算完成，已儲存至 {FEATURES_PATH}")
    print("-" * 40)

    # --- 步驟 4: 訊號生成 ---
    # 註：此處直接生成訊號。`stats` 模組的統計研究結論 (例如，高波動後應做空)
    # 已經被整合到 `signal` 模組的邏輯中。
    # `stats.py` 是一個供研究員手動執行的獨立分析腳本。
    print("--- [ 步驟 4/7 ] 正在生成交易訊號 ---")

    # 重新讀取 features_df 以確保索引正確
    features_df_for_signal = pd.read_parquet(FEATURES_PATH)

    # 根據研究結論，我們假設高波動後應做空 (trend = -1)
    # 且不使用 SMA 趨勢過濾器
    ideal_signals_df = generate_signals(features_df_for_signal, high_vol_trend=-1, use_sma_filter=False)

    # 考量到非交易日，對理想訊號進行延遲與取消的調整
    executable_signals_df = adjust_signals_for_execution(ideal_signals_df)

    # 儲存包含所有詳細資訊的訊號 DataFrame
    executable_signals_df.to_parquet(SIGNALS_PATH)
    print(f"✅ 交易訊號生成完成（包含詳細原因），已儲存至 {SIGNALS_PATH}")
    print("-" * 40)

    # --- 步驟 5: 執行回測 ---
    print("--- [ 步驟 5/7 ] 正在執行回測模擬 (包含交易成本) ---")
    trade_log, equity_curve = run_backtest(
        price_data=features_df_for_signal,
        signals=executable_signals_df['signal'],
        init_cap=INIT_CAPITAL,
        pos_size=POS_SIZE,
        cost_mode='simple', # 指定使用 'simple' 成本模型
        cost_params=COST_PARAMS
    )
    trade_log.to_csv(TRADE_LOG_PATH)
    print(f"✅ 回測執行完畢，交易日誌已儲存至 {TRADE_LOG_PATH}")
    print("-" * 40)

    # --- 步驟 6: 績效計算與視覺化 ---
    print("--- [ 步驟 6/7 ] 正在計算績效指標並產生視覺化圖表 ---")
    performance_metrics = calculate_performance_metrics(equity_curve)
    plot_equity_curve(equity_curve, EQUITY_CURVE_PATH, performance_metrics)
    print(f"✅ 權益曲線圖已儲存至 {EQUITY_CURVE_PATH}")
    print("-" * 40)

    # --- 步驟 7: 顯示最終結果 ---
    print("--- [ 步驟 7/7 ] 正在顯示最終績效報告 ---")
    print("\n========= 最終績效報告 =========\n")
    for metric, value in performance_metrics.items():
        print(f"{metric:<20}: {value:.4f}")
    print("\n==================================\n")

    # main.py 的職責在此結束。
    # 圖片的「顯示」工作，將由呼叫此腳本的前端環境 (如 Colab 筆記本) 負責。
    print("\n流程執行完畢。最終產出的權益曲線圖檔案位於：")
    print(EQUITY_CURVE_PATH)

# ----------------------------------------------------------------------------
# 程式進入點
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    # 這行是 Python 的一個標準寫法。
    # 它確保了 `main()` 這個函式只有在 `python main.py` 被直接執行時才會被呼叫。
    # 如果這個檔案被其他 .py 檔案作為模組導入 (import) 時，`main()` 則不會執行。
    main()
