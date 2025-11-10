# -*- coding: utf-8 -*-
"""
專案執行進入點 (Entry Point)

這個腳本是為了提供一個穩定且唯一的命令列執行介面，特別是用於解決在不同
環境下 (例如本地 vs. Google Colab) 可能出現的 Python 模組路徑問題。

核心功能：
1.  **強制載入本地模組**：它使用 `importlib` 函式庫，從明確的檔案路徑
    直接載入 `src/main.py` 模組。
2.  **根除命名衝突**：這個方法繞過了標準的 Python `sys.path` 搜尋機制，
    從而避免 Colab 環境優先載入系統內建 `signal` 函式庫的問題，確保
    我們自己的 `src/signal.py` 被正確使用。
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
        #    os.path.abspath(__file__) 獲取目前腳本的絕對路徑
        #    os.path.dirname(...) 獲取該腳本所在的目錄 (專案根目錄)
        project_root = os.path.dirname(os.path.abspath(__file__))
        src_path = os.path.join(project_root, 'src')
        main_py_path = os.path.join(src_path, 'main.py')

        if not os.path.exists(main_py_path):
            print(f"❌ 錯誤：找不到主執行檔 {main_py_path}")
            return

        # --- 步驟 2: 使用 importlib 從檔案路徑強制載入模組 ---
        #    這是解決 Colab 環境命名衝突的關鍵步驟。

        # a. 建立一個模組規範 (spec)，告訴 Python 如何載入這個檔案
        #    我們將模組命名為 "main"，這樣它內部的相對匯入才能正常運作
        spec = importlib.util.spec_from_file_location("main", main_py_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"無法從 {main_py_path} 建立模組規範。")

        # b. 根據規範，建立一個新的模組物件
        main_module = importlib.util.module_from_spec(spec)

        # c. 將這個模組物件加入到系統的模組快取中
        #    這一步很重要，可以讓 `main.py` 內部的 `from feat import ...` 找到彼此
        sys.modules["main"] = main_module

        # d. 最後，實際執行模組內的程式碼
        spec.loader.exec_module(main_module)

        print(f"✅ 已從指定路徑 '{main_py_path}' 強制載入主模組。")

        # --- 步驟 3: 呼叫載入的模組中的 main 函式 ---
        print("\n🚀 即將啟動全自動化回測流程...")
        main_module.main()
        print("\n✅ 主流程執行完畢！")

    except ImportError as e:
        print(f"❌ 匯入錯誤：請確認 `src/main.py` 及其內部匯入的模組是否都存在。")
        print(f"   錯誤詳情：{e}")
    except Exception as e:
        print(f"❌ 執行過程中發生未預期的錯誤。")
        print(f"   錯誤詳情：{e}")

if __name__ == "__main__":
    main()
