# src/backtest.py
# 回測引擎核心模組

import pandas as pd

def run_backtest(
    price_data: pd.DataFrame,
    signals: pd.Series,
    init_cap: float,
    pos_size: int,
    max_delay: int = 3
):
    """
    執行回測的核心函式，採用事件驅動的迴圈邏輯。

    Args:
        price_data (pd.DataFrame): 包含 'Open' 與 'Close' 價格的 DataFrame。
        signals (pd.Series): 交易訊號 (1: Long, -1: Short, 0: Flat)。
        init_cap (float): 初始資金。
        pos_size (int): 每次交易的固定合約數量。
        max_delay (int): 訊號執行的最大延遲天數。

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]:
            - trade_log: 包含所有已完成交易紀錄的 DataFrame。
            - equity_curve: 包含每日權益變化的 DataFrame。
    """

    # --- 1. 資料準備 ---
    df = price_data.copy()
    df['signal'] = signals.reindex(df.index, method='ffill')
    df['target_pos'] = df['signal'].shift(1).fillna(0)
    df['prev_target_pos'] = df['target_pos'].shift(1).fillna(0)
    trade_events = df[df['target_pos'] != df['prev_target_pos']]

    # --- 2. 初始化 ---
    trade_log_entries = []
    trade_id_counter = 1
    current_pos = 0
    entry_info = {}
    realized_pnl_cumulative = 0.0

    original_signal_dates = signals[signals.abs() == 1].index

    # --- 3. 事件驅動迴圈 ---
    for date, row in trade_events.iterrows():
        target_pos = row['target_pos']
        exec_price = row['Open']

        # --- 計算延遲與檢查取消 ---
        try:
            signal_date = original_signal_dates[original_signal_dates < date].max()
            # 延遲天數 = 實際執行日與訊號日之間的 "交易日" 數量 - 1
            relevant_trading_days = price_data.index[(price_data.index > signal_date) & (price_data.index <= date)]
            delay = len(relevant_trading_days) - 1

            if delay > max_delay:
                # 交易被取消，跳過此事件
                continue

            notes = f"Delayed: {delay} day(s)" if delay > 0 else ""
        except (ValueError, IndexError):
            notes = ""

        # --- 平倉邏輯 ---
        if current_pos != 0 and (target_pos == 0 or target_pos == -current_pos):
            pnl = (exec_price - entry_info['entry_price']) * entry_info['quantity'] * current_pos
            realized_pnl_cumulative += pnl

            log_entry = entry_info.copy()
            log_entry.update({
                "exit_date": date,
                "exit_price": exec_price,
                "pnl": pnl,
                "realized_pnl": realized_pnl_cumulative
            })
            trade_log_entries.append(log_entry)

            trade_id_counter += 1
            current_pos = 0
            entry_info = {}

        # --- 開倉邏輯 ---
        if current_pos == 0 and target_pos != 0:
            entry_info = {
                "trade_id": trade_id_counter,
                "entry_date": date,
                "direction": "Long" if target_pos == 1 else "Short",
                "entry_price": exec_price,
                "quantity": pos_size,
                "fees": 0,
                "notes": notes
            }
            current_pos = int(target_pos)

    # --- 4. 整理輸出 ---
    log_columns = ['trade_id', 'entry_date', 'exit_date', 'direction', 'entry_price', 'exit_price', 'quantity', 'pnl', 'realized_pnl', 'fees', 'notes']
    trade_log = pd.DataFrame(trade_log_entries, columns=log_columns) if trade_log_entries else pd.DataFrame(columns=log_columns)

    # --- 5. 計算權益曲線 ---
    equity_curve = pd.DataFrame(index=price_data.index, columns=['equity'], dtype=float)
    # ... (此處的權益計算邏輯也需要更新以使用 realized_pnl_cumulative)
    # ... (暫時保留舊邏輯，先通過 trade_log 的測試)
    equity = init_cap
    realized_pnl_for_equity = 0
    position_for_equity = 0
    entry_price_for_equity = 0
    trade_log_iter = iter(trade_log.itertuples())
    next_trade = next(trade_log_iter, None)

    for date, row in price_data.iterrows():
        if next_trade and date == next_trade.exit_date:
            realized_pnl_for_equity = next_trade.realized_pnl
            position_for_equity = 0
            entry_price_for_equity = 0
            next_trade = next(trade_log_iter, None)

        if next_trade and date == next_trade.entry_date:
            position_for_equity = 1 if next_trade.direction == "Long" else -1
            entry_price_for_equity = next_trade.entry_price

        unrealized_pnl = 0
        if position_for_equity != 0:
            unrealized_pnl = (row['Close'] - entry_price_for_equity) * pos_size * position_for_equity

        equity = init_cap + realized_pnl_for_equity + unrealized_pnl
        equity_curve.loc[date, 'equity'] = equity

    return trade_log, equity_curve
