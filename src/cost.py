# src/cost.py
# 交易成本與滑價模擬模組

def calculate_simple_cost(quantity: int, cost_params: dict) -> float:
    """
    計算基於 'simple' 模型的交易成本。

    Args:
        quantity (int): 交易的合約數量。
        cost_params (dict): 包含成本參數的字典。
            - "fees_per_unit" (float): 每單位合約的固定手續費。
            - "slippage_per_unit" (float): 每單位合約的固定滑價點數。

    Returns:
        float: 該筆交易的總成本。
    """
    fees = cost_params.get("fees_per_unit", 0.0)
    slippage = cost_params.get("slippage_per_unit", 0.0)

    total_cost = (fees + slippage) * quantity

    return total_cost
