# src/cost.py
# 交易成本與滑價模擬模組

def calculate_simple_cost(quantity: int, cost_params: dict) -> float:
    """
    計算基於 'simple' 模型的交易成本。

    Args:
        quantity (int): 交易的合約數量。
        cost_params (dict): 包含成本參數的字典。
            - "commission_per_trade" (float): 每筆交易的固定手續費。
            - "slippage_per_trade" (float): 每筆交易的固定滑價點數。

    Returns:
        float: 該筆交易的總成本。
    """
    commission = cost_params.get("commission_per_trade", 0.0)
    slippage = cost_params.get("slippage_per_trade", 0.0)

    # 假設成本是基於每筆交易，而不是每單位數量
    # 如果是基於數量，這裡應該是 (commission + slippage) * quantity
    total_cost = commission + slippage

    return total_cost
