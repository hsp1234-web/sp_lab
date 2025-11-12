# 回測引擎參數設定檔 (BACKTEST_CONFIG)

## 用途

本文件旨在統一管理回測 (`backtest.py`) 與訊號 (`sp_signal.py`) 模組所需的核心參數，方便開發者在不同實驗情境下快速切換設定，並確保結果的可追溯性。

---

## 1. 核心參數表

| 參數鍵       | 預設值      | 資料型別 | 說明                                   |
| :----------- | :---------- | :------- | :------------------------------------- |
| `INIT_CAP`   | `100000`    | `int`    | 初始資金 (Initial Capital)             |
| `POS_SIZE`   | `1`         | `int`    | 每筆交易固定合約數量 (Position Size)   |
| `MAX_DELAY`  | `3`         | `int`    | 訊號最多延遲執行天數                   |
| `EXEC_PRICE` | `open`      | `str`    | 執行價格類型 (`open` / `close`)        |
| `COST_MODE`  | `none`      | `str`    | 成本模式 (`none`/`simple`/`detailed`)  |
| `ATR_W`      | `14`        | `int`    | ATR 計算視窗 (Window)                  |
| `ATR_MA_W`   | `30`        | `int`    | ATR 移動平均視窗                       |
| `SMA_SHORT`  | `20`        | `int`    | 短期 SMA 視窗                          |
| `SMA_LONG`   | `60`        | `int`    | 長期 SMA 視窗                          |
| `RET_H`      | `1`         | `int`    | 未來報酬計算視窗 (t+h)                 |
| `GRID_MODE`  | `off`       | `str`    | 參數掃描模式 (`off`/`coarse`/`fine`)   |
| `CACHE_ON`   | `true`      | `bool`   | 啟用快取以加速重複計算                 |
| `EARLY_STOP` | `true`      | `bool`   | 啟用早停機制以過濾無效參數組合         |

---

## 2. 快速設定檔 (Presets)

### 🔹 QuickStart (預設模式)

**用途**：最簡化的基礎設定，用於快速驗證回測流程與基本邏輯。

-   `INIT_CAP` = `100000`
-   `POS_SIZE` = `1`
-   `EXEC_PRICE` = `open`
-   `COST_MODE` = `none`
-   `ATR_W` = `14`
-   `ATR_MA_W` = `30`
-   `RET_H` = `1`
-   `GRID_MODE` = `off`
-   `CACHE_ON` = `true`

### 🔹 Conservative (保守風控模式)

**用途**：模擬較保守的交易情境，納入基本成本並使用較長期的參數。

-   `COST_MODE` = `simple`
-   `ATR_MA_W` = `60`
-   `GRID_MODE` = `coarse`
-   `EARLY_STOP` = `true`

### 🔹 Aggressive (探索最佳化模式)

**用途**：用於參數網格搜尋 (Grid Search)，以探索不同參數組合下的策略表現。

-   `COST_MODE` = `none`
-   `ATR_W` ∈ `{7, 14, 21}`
-   `ATR_MA_W` ∈ `{20, 30, 60}`
-   `RET_H` ∈ `{1, 5, 20}`
-   `GRID_MODE` = `fine`
-   `EARLY_STOP` = `true`
-   `CACHE_ON` = `true`

---

## 3. 使用方式與記錄

1.  **匯入**：由 `src/cfg.py` 模組讀取本文件中的參數。
2.  **記錄**：每次執行回測前，需在 `log.md` 中明確記錄所使用的模式 (例如：`使用 QuickStart 模式進行回測`)。
3.  **修改追蹤**：若在特定實驗中修改了非預設參數，需在 `log.md` 中詳細註明，格式如下：
    `YYYY-MM-DD | <參數名> | <舊值> -> <新值> | <修改理由>`

#### 範例記錄 (`log.md`)

```
2025-11-09 | GRID_MODE | off -> coarse | 開啟參數掃描以測試不同 SMA 組合。
2025-11-10 | ATR_MA_W | 30 -> 60 | 測試在保守模式下策略的穩定性。
2025-11-11 | COST_MODE | none -> simple | 首次納入手續費與滑價進行模擬。
```
