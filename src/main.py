# -*- coding: utf-8 -*-
"""
VOL-FUTURE-LAB 專案主執行腳本

此腳本為整個量化研究流程的單一入口點，整合了從數據獲取到最終視覺化報告的
所有步驟。旨在提供一個可被外部環境 (如 Google Colab) 直接呼叫的標準化執行流程。

執行順序:
1. 獲取原始數據 (fetch)
2. 數據清洗 (clean)
3. 特徵工程 (feat)
4. 統計分析 (stats)
5. 訊號生成 (signal)
6. 執行回測 (backtest)
7. 產生視覺化報告 (viz)
"""
import os
import subprocess
import pandas as pd
import matplotlib

# --- [核心設定] ---
# 為了確保在無 GUI 的伺服器環境 (如 Colab) 中能順利產圖，必須在使用 pyplot 前設定好後端。
matplotlib.use('Agg')

# --- [延遲導入] ---
# 由於我們會更改工作目錄，將模組導入放在 main 函式內，確保路徑正確。

# --- [回測參數設定] ---
INIT_CAPITAL = 100000.0
POS_SIZE = 100

def main():
    """主執行函式"""
    # 將工作目錄切換至此腳本所在的 src 資料夾，以確保所有相對路徑參照 (../data) 正確
    main_script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(main_script_dir)

    # 現在工作目錄已變更，可以安全地導入同目錄下的模組
    from backtest import run_backtest
    from viz import plot_equity_curve, calculate_performance_metrics

    # --- [1-5] 執行數據準備階段的腳本 ---
    scripts_to_run = [
        "fetch.py", "clean.py", "feat.py", "stats.py", "signal.py"
    ]
    total_steps = len(scripts_to_run) + 2  # 數據準備 + 回測 + 視覺化

    for i, script in enumerate(scripts_to_run, 1):
        print(f"\n--- [{i}/{total_steps}] 正在執行 {script} ---")
        # 使用 check=True，若腳本執行失敗，將會拋出例外
        subprocess.run(['python', script], check=True)

    # --- [6] 執行回測 (backtest.py) ---
    print(f"\n--- [{total_steps - 1}/{total_steps}] 正在執行回測 ---")
    print("📈 正在讀取數據與訊號...")
    # 相對路徑是基於目前的 'src' 工作目錄
    signals_df = pd.read_parquet('../data/processed/signals.parquet')
    features_df = pd.read_parquet('../data/processed/features.parquet')

    print("🚀 執行回測中...")
    trade_log, equity_curve = run_backtest(
        price_data=features_df,
        signals=signals_df['signal'],
        init_cap=INIT_CAPITAL,
        pos_size=POS_SIZE
    )

    # --- [7] 產生視覺化報告 (viz.py) ---
    print(f"\n--- [{total_steps}/{total_steps}] 正在產生視覺化報告 ---")
    # 輸出目錄將建立在 'src' 資料夾內
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    equity_curve_path = os.path.join(output_dir, 'equity_curve.jpg')
    plot_equity_curve(equity_curve, equity_curve_path)

    print("\n--- 績效指標 ---")
    performance = calculate_performance_metrics(equity_curve)
    for key, value in performance.items():
        print(f"{key}: {value:.4f}")

    print(f"\n✅ 所有流程執行完畢！權益曲線圖已儲存至: {os.path.join(main_script_dir, equity_curve_path)}")

if __name__ == "__main__":
    main()
