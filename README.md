# VOL-FUTURE-LAB：指數期貨波動率量化研究

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/hsp1234-web/sp_lab/blob/6.2/sp_lab.ipynb)

本專案是一個以 Python 進行的指數期貨波動率量化研究平台。旨在建立一個以終端環境可獨立運作、具備高速數據分析與回測能力的完整流程，用於驗證「波動率」與「價格變動」之間的統計關係，並將其轉化為可回測的交易策略。

## ✨ 核心特色

-   **跨平台支援**：完全相容 **Windows** 與 **Linux** 環境，實現「寫一次，到處執行」。
-   **一鍵 Colab 執行**：透過 `sp_lab.ipynb` 提供一鍵執行的 Colab 環境，無需本地設定。
-   **現代化工具鏈**：使用 `uv` 進行高速的 Python 環境與依賴管理。
-   **受控的執行入口**：透過根目錄的 `main.py` 與 `run.py` 腳本，解決模組匯入衝突，確保執行的穩定性。
-   **測試驅動開發 (TDD)**：所有核心模組均有對應的單元測試，確保程式碼的穩健性與可維護性。
-   **模組化管線**：從數據獲取、清洗、特徵工程、統計分析、訊號生成到回測與視覺化，皆為獨立且可串連的模組。
-   **貼近真實的回測**：內建成本與滑價模擬，讓策略評估更具參考價值。
-   **自動化報告**：可自動產出權益曲線圖與關鍵績效指標 (KPIs)，如最大回撤、夏普比率等。

## 🚀 快速開始

### 1. 環境設定

本專案使用 `uv` 管理 Python 虛擬環境與依賴。

```bash
# 1. 建立虛擬環境 (只需執行一次)
uv venv

# 2. 啟用虛擬環境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. 安裝所有必要的依賴
uv pip install -r requirements.txt
```

### 2. 執行完整流程

#### 數據獲取與清洗 (Data Pipeline)

使用 `main.py` 作為統一入口：

```bash
# 獲取數據 (請確保路徑不含中文字元以避免編碼問題)
python main.py fetch --start 2023-01-01 --end 2023-12-31

# 清洗數據
python main.py clean
```

#### 策略回測 (Backtest Pipeline)

透過專案根目錄的 `run.py` 腳本，即可一鍵執行完整的端到端回測流程。

```bash
# 🚀 執行回測！
python run.py
```

### 3. 執行測試

本專案遵循嚴格的 TDD 流程。你可以隨時運行測試來驗證所有模組的正確性。

```bash
# 執行所有測試
uv run pytest

# 執行特定檔案的測試
uv run pytest tests/test_backtest.py
```

## 📂 專案結構

```
.
├── AGENTS.md
├── data
│   ├── raw              # 原始數據
│   └── processed        # 清洗後的數據
├── docs                 # 專案文件
├── index_futures_volatility_quant_project.md
├── log.md               # 開發日誌
├── requirements.txt
├── main.py              # 數據管線入口
├── run.py               # 回測管線入口
├── src                  # 核心程式碼
│   ├── __init__.py
│   ├── backtest.py      # 回測引擎
│   ├── clean.py         # 數據清洗
│   ├── cost.py          # 成本模型
│   ├── feat.py          # 特徵工程
│   ├── fetch.py         # 數據獲取
│   ├── sp_signal.py     # 訊號生成
│   ├── stats.py         # 統計分析
│   └── viz.py           # 視覺化
└── tests                # 單元測試
```

## 📚 核心模組簡介

-   **`src/fetch.py`**: 負責從網路 API (如 Twstock, FinMind) 下載原始市場數據。
-   **`src/clean.py`**: 對原始數據進行清洗、處理缺值、對齊交易日等。
-   **`src/feat.py`**: 計算技術指標（如 RSI、移動平均線）作為策略的基礎特徵。
-   **`src/stats.py`**: 執行統計分析與假說檢定，驗證策略的有效性。
-   **`src/sp_signal.py`**: 根據統計結果，生成具體的買賣訊號 (`1`, `-1`, `0`)。
-   **`src/backtest.py`**: 核心回測引擎，根據訊號模擬交易過程，並產出交易日誌與權益曲線。
-   **`src/cost.py`**: 交易成本模型，用於模擬手續費與滑價。
-   **`src/viz.py`**: 視覺化工具，將回測結果繪製成圖表，並計算績效指標。
