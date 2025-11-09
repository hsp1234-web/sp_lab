# src/main.py
"""
主執行流程腳本。
"""
import os
from datetime import datetime
import json

# 確保在任何 matplotlib 匯入之前設定後端
import matplotlib
matplotlib.use('Agg')

from fetch import fetch_data
from clean import clean_data
from feat import create_features
from stats import run_statistical_tests
from signal import generate_signals, adjust_signals_for_execution
from backtest import run_backtest
from viz import plot_equity_curve, calculate_performance_metrics

def main():
    """主執行函數"""
    print("📈 開始執行 VOL-FUTURE-LAB 回測流程...")

    # --- 參數設定 ---
    TICKER = "^GSPC"
    START_DATE = "2010-01-01"
    END_DATE = datetime.now().strftime('%Y-%m-%d')
    ATR_PERIOD = 20
    FAST_MA = 50
    SLOW_MA = 200
    SIGNIFICANCE_LEVEL = 0.05
    INITIAL_CAPITAL = 100000.0
    POSITION_SIZE = 100
    COST_PARAMS = {'commission_per_trade': 1.0, 'slippage_per_trade': 0.0002}

    # --- 建立輸出資料夾 ---
    output_dir = "output"
    data_dir = os.path.join(output_dir, "data")
    results_dir = os.path.join(output_dir, "results")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    # --- 檔案路徑定義 ---
    # ... (檔案路徑定義與之前相同)
    raw_data_path = os.path.join(data_dir, "raw_data.parquet")
    cleaned_data_path = os.path.join(data_dir, "cleaned_data.parquet")
    features_path = os.path.join(data_dir, "features.parquet")
    stats_summary_path = os.path.join(results_dir, "stats_summary.txt")
    signals_path = os.path.join(data_dir, "signals.parquet")
    trade_log_path = os.path.join(results_dir, "trade_log.csv")
    equity_curve_path = os.path.join(results_dir, "equity_curve.jpg")
    performance_metrics_path = os.path.join(results_dir, "performance_metrics.json")

    # --- 流程 ---

    # 1. Fetch
    print("\n[1/7] 正在下載數據...")
    raw_data = fetch_data(TICKER, START_DATE, END_DATE)
    raw_data.to_parquet(raw_data_path)

    # 2. Clean
    print("\n[2/7] 正在清洗數據...")
    cleaned_data = clean_data(raw_data)
    cleaned_data.to_parquet(cleaned_data_path)

    # 3. Feat
    print("\n[3/7] 正在建立特徵...")
    features_df = create_features(cleaned_data, atr_period=ATR_PERIOD, fast_ma=FAST_MA, slow_ma=SLOW_MA)
    features_df.to_parquet(features_path)

    # 4. Stats (可選步驟，主要用於研究)
    print("\n[4/7] 正在執行統計分析...")
    stats_summary = run_statistical_tests(features_df, significance_level=SIGNIFICANCE_LEVEL, atr_period=ATR_PERIOD)
    with open(stats_summary_path, 'w') as f:
        json.dump(stats_summary, f, indent=4)
    print("✅ 統計摘要已儲存。")

    # 5. Signal
    print("\n[5/7] 正在生成交易訊號...")
    ideal_signals = generate_signals(features_df, fast_ma=FAST_MA, slow_ma=SLOW_MA)
    final_signals = adjust_signals_for_execution(ideal_signals, features_df)
    final_signals.to_parquet(signals_path)
    print("✅ 交易訊號已生成。")

    # 6. Backtest (已內建成本計算)
    print("\n[6/7] 正在執行回測 (包含成本計算)...")
    trade_log, equity_curve = run_backtest(
        price_data=features_df,
        signals=final_signals,
        init_cap=INITIAL_CAPITAL,
        pos_size=POSITION_SIZE,
        cost_mode='simple',
        cost_params=COST_PARAMS
    )
    trade_log.to_csv(trade_log_path, index=False)
    print(f"✅ 回測完成，交易日誌已儲存至 {trade_log_path}")

    # 7. Viz
    print("\n[7/7] 正在生成視覺化報告...")
    # 重新命名 equity_curve DataFrame 的欄位以符合 plot_equity_curve 的預期
    equity_curve_renamed = equity_curve.rename(columns={'equity': 'Equity'})
    plot_equity_curve(equity_curve_renamed, equity_curve_path)
    print(f"✅ 權益曲線圖已儲存至 {equity_curve_path}")

    performance_metrics = calculate_performance_metrics(equity_curve_renamed)
    with open(performance_metrics_path, 'w') as f:
        json.dump(performance_metrics, f, indent=4)
    print(f"✅ 績效指標已儲存至 {performance_metrics_path}")

    print("\n--- 績效指標 ---")
    for key, value in performance_metrics.items():
        print(f"{key}: {value:.4f}" if isinstance(value, float) else f"{key}: {value}")
    print("--------------------")

    print(f"\n🎉 回測流程全部執行完畢！結果已儲存於 '{output_dir}' 資料夾。")
    print(f"最終權益曲線圖: {equity_curve_path}")

if __name__ == "__main__":
    main()
