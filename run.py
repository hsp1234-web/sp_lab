# -*- coding: utf-8 -*-
"""
專案執行進入點 (Entry Point)

這個腳本是為了提供一個穩定且唯一的命令列執行介面，特別是用於解決在不同
環境下 (例如本地 vs. Google Colab) 可能出現的 Python 模組路徑問題。

核心功能 (組合方案)：
1.  **動態設定執行路徑**：它會將 `src` 目錄的絕對路徑添加到 Python 的
    系統搜尋路徑 (`sys.path`) 的最前端。這一步是為了解決 `main.py`
    內部無法找到 `fetch`, `clean` 等同級模組的問題。
2.  **強制載入本地模組**：接著，它使用 `importlib` 函式庫，從明確的
    檔案路徑直接載入 `src/main.py` 模組。這一步是為了解決 `sp_signal`
    模組與系統內建函式庫的命名衝突問題。
3.  **啟動主流程**：成功載入模組後，它會執行 `main.py` 中的 `main`
    函式，啟動整個自動化回測流程。
"""

import sys
import os
import importlib.util

def main():
    """
    設定環境路徑並執行主回測流程。
    """
    try:
        # --- 步驟 1: 定義 `src` 和 `main.py` 的絕對路徑 ---
        project_root = os.path.dirname(os.path.abspath(__file__))
        src_path = os.path.join(project_root, 'src')
        main_py_path = os.path.join(src_path, 'main.py')

        if not os.path.exists(main_py_path):
            print(f"❌ 錯誤：找不到主執行檔 {main_py_path}")
            return

        # --- 步驟 2: 將專案根目錄加入 sys.path (確保 `from src.module` 可行) ---
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            print(f"✅ 已將專案根目錄 '{project_root}' 加入 Python 執行環境的最前端。")

        # --- 步驟 3: 使用 importlib 從檔案路徑強制載入模組 (解決 sp_signal 衝突) ---
        spec = importlib.util.spec_from_file_location("main", main_py_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"無法從 {main_py_path} 建立模組規範。")

        main_module = importlib.util.module_from_spec(spec)
        sys.modules["main"] = main_module

        spec.loader.exec_module(main_module)

        print(f"✅ 已從指定路徑 '{main_py_path}' 強制載入主模組。")

        # --- 步驟 4: 呼叫載入的模組中的 main 函式 ---
        # print("\n🚀 即將啟動全自動化回測流程...") # main.py 內部已有此訊息，避免重複
        main_module.main()
        # print("\n✅ 主流程執行完畢！") # main.py 內部已有此訊息，避免重複

    except ImportError as e:
        print(f"❌ 匯入錯誤：請確認 `src/main.py` 及其內部匯入的模組是否都存在。")
        print(f"   錯誤詳情：{e}")
    except Exception as e:
        print(f"❌ 執行過程中發生未預期的錯誤。")
        print(f"   錯誤詳情：{e}")

if __name__ == "__main__":
    main()
