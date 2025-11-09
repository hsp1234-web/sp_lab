import pandas as pd
import numpy as np

def generate_signals(
    df: pd.DataFrame,
    high_vol_trend: int,
    use_sma_filter: bool = False,
    atr_window: int = 14,
    ma_window: int = 30,
    sma_window: int = 20
) -> pd.DataFrame:
    """
    根據市場特徵與統計結論，產生交易訊號。

    此函式專注於在每日收盤後，根據當天的市場數據決定是否產生一個
    理想化的進場訊號。訊號執行的具體邏輯 (如延遲、已有倉位處理)
    將由回測引擎 (`backtest.py`) 負責。

    Args:
        df: 包含 'ATR_14', 'SMA_20' 等特徵的 Pandas DataFrame。
        high_vol_trend: 代表統計結論的整數。例如 -1 代表高波動後應做空。
        use_sma_filter: 是否啟用 SMA 趨勢過濾器，預設為 False。
        atr_window: ATR 的計算天期 (預設為 14)。
        ma_window: 用於定義波動狀態的移動平均天期 (預設為 30)。
        sma_window: 用於趨勢過濾的 SMA 天期 (預設為 20)。

    Returns:
        一個附加了 'signal' (整數) 和 'signal_reason' (文字) 欄位的
        新的 Pandas DataFrame。
    """
    df_signal = df.copy()

    # --- 1. 定義波動狀態 ---
    atr_col = f'ATR_{atr_window}'
    df_signal['ATR_MA'] = df_signal[atr_col].rolling(window=ma_window).mean()
    df_signal['is_high_vol'] = df_signal[atr_col] > df_signal['ATR_MA']

    # --- 2. 產生基礎訊號 ---
    # 根據高波動日的趨勢結論產生訊號，低波動日則無訊號 (0)
    df_signal['signal'] = np.where(df_signal['is_high_vol'], high_vol_trend, 0)

    # 預設 reason
    df_signal['signal_reason'] = np.where(
        df_signal['is_high_vol'],
        f"High Volatility {'Long' if high_vol_trend == 1 else 'Short'}",
        "No Signal"
    )

    # --- 3. 新增輔助欄位 ---
    # 訊號在當日收盤時產生
    df_signal['signal_generated_at'] = df_signal.index
    # 理想的執行時間是隔天 (t+1)
    df_signal['signal_exec_when'] = df_signal.index + pd.Timedelta(days=1)


    # --- 4. 應用 SMA 趨勢過濾器 (可選) ---
    if use_sma_filter:
        sma_col = f'SMA_{sma_window}'
        df_signal['sma_trend'] = df_signal[sma_col].diff()

        # 定義趨勢條件
        is_up_trend = df_signal['sma_trend'] > 0
        is_down_trend = df_signal['sma_trend'] < 0

        # 定義訊號與趨勢是否一致
        signal_is_long = df_signal['signal'] == 1
        signal_is_short = df_signal['signal'] == -1

        # 條件不符時，重設訊號為 0
        # 做多訊號但趨勢不向上 -> 過濾
        filter_long = signal_is_long & ~is_up_trend
        # 做空訊號但趨勢不向下 -> 過濾
        filter_short = signal_is_short & ~is_down_trend

        # 更新被過濾的訊號
        df_signal.loc[filter_long | filter_short, 'signal'] = 0
        df_signal.loc[filter_long | filter_short, 'signal_reason'] = "Filtered by SMA"

    # --- 4. 清理輔助欄位 ---
    df_signal = df_signal.drop(columns=['ATR_MA', 'is_high_vol'])
    if 'sma_trend' in df_signal.columns:
        df_signal = df_signal.drop(columns=['sma_trend'])

    # 確保 signal 欄位是整數型態
    df_signal['signal'] = df_signal['signal'].astype(int)

    return df_signal


def adjust_signals_for_execution(df_with_signals: pd.DataFrame, max_delay_days: int = 3) -> pd.DataFrame:
    """
    根據交易日曆調整訊號的實際執行時間，處理延遲與取消。

    Args:
        df_with_signals: 包含理想化訊號的 DataFrame (generate_signals 的輸出)。
        max_delay_days: 訊號執行的最大延遲天數。

    Returns:
        一個調整了 signal 和 signal_exec_when 欄位的 DataFrame。
    """
    df_adjusted = df_with_signals.copy()

    # 假設 df_adjusted.index 包含了所有有效的交易日
    trading_days = pd.to_datetime(df_adjusted.index)

    # 找出所有產生了實際訊號的日子 (非 0)
    signal_days = df_adjusted[df_adjusted['signal'] != 0].index

    for day in signal_days:
        ideal_exec_date = df_adjusted.loc[day, 'signal_exec_when']

        # 尋找下一個實際的交易日
        future_trading_days = trading_days[trading_days >= ideal_exec_date]

        if not future_trading_days.empty:
            actual_exec_date = future_trading_days[0]
            delay = (actual_exec_date - ideal_exec_date).days

            if delay <= max_delay_days:
                # 更新執行日期
                df_adjusted.loc[day, 'signal_exec_when'] = actual_exec_date
                df_adjusted.loc[day, 'signal_reason'] += f" (Delayed {delay}d)"
            else:
                # 超過最大延遲，取消訊號
                df_adjusted.loc[day, 'signal'] = 0
                df_adjusted.loc[day, 'signal_reason'] = f"Cancelled (Delay > {max_delay_days}d)"
        else:
            # 找不到未來的交易日，取消訊號
            df_adjusted.loc[day, 'signal'] = 0
            df_adjusted.loc[day, 'signal_reason'] = "Cancelled (No Future Trading Day)"

    return df_adjusted
