# tests/test_cost.py
# 交易成本模組測試

import pytest
from src.cost import calculate_simple_cost

def test_calculate_simple_cost():
    """
    測試 simple 成本模型的計算是否正確。
    """
    trade_price = 10000.0
    quantity = 2

    # 假設手續費 (fees) 為 50 元/單位，滑價 (slippage) 為 0.2 點/單位
    cost_params = {
        "fees_per_unit": 50.0,
        "slippage_per_unit": 0.2
    }

    # 預期成本 = (手續費 + 滑價) * 數量
    # 這裡的滑價是點數，不是金額，所以總滑價成本是 slippage * quantity
    # 總成本 = (fees_per_unit * quantity) + (slippage_per_unit * quantity)
    # 讓我們假設滑價是固定的金額以簡化
    # 預期成本 = (手續費 + 滑價) * 數量
    # (50 + 0.2) * 2 = 100.4

    # 重新定義：滑價是價格的百分比
    # cost_params = {"fees": 50, "slippage": 0.0001} # 0.01%
    # total_cost = (fees * quantity) + (trade_price * slippage * quantity)
    # (50*2) + (10000 * 0.0001 * 2) = 100 + 2 = 102

    # 根據設計文件，我們採用固定點數
    # 假設每單位合約的手續費是 50 元，滑價是 0.2 點
    # 總成本 = (固定手續費 + 固定滑價點數) * 合約數量
    expected_cost = (50.0 + 0.2) * 2

    total_cost = calculate_simple_cost(
        quantity=quantity,
        cost_params=cost_params
    )

    assert total_cost == expected_cost
