# 專案依賴項特別注意事項

本文件旨在記錄專案中特定依賴套件的重要注意事項，以幫助未來開發者快速理解關鍵的設計決策與潛在陷阱。

---

## 1. `numpy` 版本鎖定

-   **鎖定版本**: `numpy==2.2.6`
-   **原因**:
    此版本是為了維持與 `pandas-ta` 及其核心子依賴 `numba` 的兼容性而特別選定的。
    -   `numba==0.61.2` 要求 `numpy` 版本需 `< 2.3`。
    -   `pandas-ta` 要求 `numpy` 版本需 `>= 2.2.6`。
    綜合以上條件，`2.2.6` 是一個能夠滿足所有依賴需求的穩定版本。未來若需升級，務必同步測試 `pandas-ta` 的兼容性。

---

## 2. `pandas-ta` 使用須知

-   **核心設計**: `pandas-ta` 的 `.ta` 擴充功能在設計上是為 **Pandas DataFrame** 物件註冊的，而非 Series。
-   **問題背景**:
    在開發初期，曾發生 `.ta` 擴充功能無法使用的問題。經過深入分析，發現根本原因並非傳統的版本依賴衝突，而是「使用者預期」與「函式庫設計」的落差。開發者很自然地會預期 `.ta` 能夠同時作用於 Series (單一資產價格序列) 和 DataFrame (多欄位資產數據表)，但 `pandas-ta` 的設計選擇了僅支援後者。
-   **正確使用方式**:
    在呼叫 `.ta` 擴充功能或其相關函式 (如 `ta.atr`) 之前，**務必確保您的操作對象是一個 DataFrame**。如果您的原始資料是一個 Series，請先將其轉換為 DataFrame。

    ```python
    # 錯誤範例 (假設 price 是一個 Series)
    # price.ta.sma(20, append=True) # 可能會引發 AttributeError

    # 正確作法
    import pandas as pd
    price_df = pd.DataFrame(price) # 或 price.to_frame()
    price_df.ta.sma(20, append=True) # 在 DataFrame 上操作
    ```
-   **結論**:
    這是一個典型的「深入理解函式庫設計」的重要案例。遇到類似問題時，除了檢查版本兼容性，也應回頭檢視函式庫的 API 設計與預期的輸入格式。
