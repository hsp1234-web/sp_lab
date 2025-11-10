# -*- coding: utf-8 -*-
"""
專案執行進入點 (Entry Point)

這個腳本是為了提供一個穩定且唯一的命令列執行介面，特別是用於解決在不同
環境下 (例如本地 vs. Google Colab) 可能出現的 Python 模組路徑問題。

核心功能：
1.  **動態設定執行路徑**：它會將 `src` 目錄的絕對路徑添加到 Python 的
    系統搜尋路徑 (`sys.path`) 的最前端。
2.  **確保本地模組優先**：這一步確保了當我們執行 `import signal` 時，
    Python 會優先載入我們專案中的 `src/signal.py`，而不是系統內建的
    同名標準函式庫，從而根除 `ImportError`。
3.  **啟動主流程**：設定完路徑後，它會匯入 `src/main.py` 中的 `main`
    函式，並執行整個自動化回測流程。
"""

import sys
import os

def main():
    """
    設定環境路徑並執行主回測流程。
    """
    try:
        # 1. 將 'src' 目錄的絕對路徑添加到 sys.path 的最前面
        #    os.path.abspath(__file__) 獲取目前腳本的絕對路徑
        #    os.path.dirname(...) 獲取該腳本所在的目錄 (專案根目錄)
        #    os.path.join(...) 將根目錄與 'src' 拼接成完整路徑
        src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')

        if src_path not in sys.path:
            # 使用 insert(0, ...) 確保我們的 src 路徑擁有最高優先級
            sys.path.insert(0, src_path)
            print(f"✅ 已將原始碼路徑 '{src_path}' 加入 Python 執行環境的最前端。")

        # 2. 從 src 目錄中匯入並執行主流程
        #    這個 import 必須在 sys.path 設定完成後才能進行
        from main import main as run_pipeline

        print("\n🚀 即將啟動全自動化回測流程...")
        run_pipeline()
        print("\n✅ 主流程執行完畢！")

    except ImportError as e:
        print(f"❌ 匯入錯誤：無法找到 'src' 目錄或其中的 'main' 模組。請確認腳本結構是否正確。")
        print(f"   錯誤詳情：{e}")
    except Exception as e:
        print(f"❌ 執行過程中發生未預期的錯誤。")
        print(f"   錯誤詳情：{e}")

if __name__ == "__main__":
    # 只有當這個腳本被直接執行時 (例如 `python run.py`)，main() 函式才會被呼叫。
    main()
