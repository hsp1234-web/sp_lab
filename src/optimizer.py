import random
import numpy as np
import pandas as pd

from deap import base, creator, tools, algorithms

# --- 核心模組導入 ---
from src.feat import calculate_features
# 導入新的布林帶訊號生成器，並保留舊的以備不時之需
from src.sp_signal import generate_bollinger_band_signals, generate_signals
from src.backtest import run_backtest
from src.stats import calculate_backtest_stats

# --- 全域設定 ---
INITIAL_CAPITAL = 100000.0
POSITION_SIZE = 1

# --- 基因演算法設定 ---
# 確保在重新執行時不會出錯
try:
    del creator.FitnessMax
    del creator.Individual
except AttributeError:
    pass

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)
toolbox = base.Toolbox()

# --- 新策略的參數空間定義 (布林帶) ---
SMA_LONG_PERIOD_RANGE = (50, 250)
BBAND_PERIOD_RANGE = (10, 60)
BBAND_STDDEV_RANGE = (1.5, 3.5)

toolbox.register("attr_sma_long_period", random.randint, SMA_LONG_PERIOD_RANGE[0], SMA_LONG_PERIOD_RANGE[1])
toolbox.register("attr_bband_period", random.randint, BBAND_PERIOD_RANGE[0], BBAND_PERIOD_RANGE[1])
toolbox.register("attr_bband_stddev", random.uniform, BBAND_STDDEV_RANGE[0], BBAND_STDDEV_RANGE[1])

toolbox.register("individual", tools.initCycle, creator.Individual,
                 (toolbox.attr_sma_long_period, toolbox.attr_bband_period, toolbox.attr_bband_stddev), n=1)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

# --- 適應度評估函式 (已更新為布林帶策略) ---
def evaluate_strategy(individual: list, training_data: pd.DataFrame) -> tuple:
    """
    評估一個「個體」(一組策略參數) 的適應度 (夏普比率)。
    """
    # 解包參數
    sma_long_period, bband_period, bband_stddev = individual[0], individual[1], individual[2]

    try:
        # 1. 動態計算特徵
        features_df = calculate_features(
            training_data,
            sma_long_period=int(sma_long_period),
            bband_period=int(bband_period),
            bband_stddev=bband_stddev
        )

        # 2. 動態生成訊號 (使用新的函式)
        signals_df = generate_bollinger_band_signals(
            features_df,
            sma_long_period=int(sma_long_period),
            bband_period=int(bband_period),
            bband_stddev=bband_stddev
        )

        # 3. 執行回測
        trade_log, equity_curve = run_backtest(
            price_data=training_data,
            signals=signals_df['signal'],
            init_cap=INITIAL_CAPITAL,
            pos_size=POSITION_SIZE
        )

        # 4. 計算績效
        if trade_log.empty:
            return (-100.0,) # 如果沒有交易，給予極低的懲罰分數

        stats = calculate_backtest_stats(
            trade_log=trade_log,
            equity_curve=equity_curve,
            initial_capital=INITIAL_CAPITAL
        )
        sharpe_ratio = stats.get("夏普比率", -100.0)

        return (sharpe_ratio,) if np.isfinite(sharpe_ratio) else (-100.0,)
    except Exception as e:
        # 在優化過程中，某些參數組合可能導致錯誤 (例如週期過長)，給予懲罰分數
        # print(f"Error evaluating individual {individual}: {e}") # 可選的除錯輸出
        return (-100.0,)

# --- 註冊遺傳演算法運算子 ---
toolbox.register("evaluate", evaluate_strategy)
toolbox.register("mate", tools.cxTwoPoint)

def custom_mutate(individual, indpb):
    """針對新參數集的自訂突變函式。"""
    # SMA Period
    if random.random() < indpb:
        individual[0] = random.randint(SMA_LONG_PERIOD_RANGE[0], SMA_LONG_PERIOD_RANGE[1])
    # BBand Period
    if random.random() < indpb:
        individual[1] = random.randint(BBAND_PERIOD_RANGE[0], BBAND_PERIOD_RANGE[1])
    # BBand Stddev
    if random.random() < indpb:
        individual[2] += random.gauss(0, 0.2) # 較小的標準差以進行微調
        individual[2] = np.clip(individual[2], BBAND_STDDEV_RANGE[0], BBAND_STDDEV_RANGE[1])
    return individual,

toolbox.register("mutate", custom_mutate, indpb=0.2)
toolbox.register("select", tools.selTournament, tournsize=3)

# --- 優化執行器 ---
def run_ga_optimization(training_data: pd.DataFrame, pop_size: int, ngen: int, cxpb: float, mutpb: float):
    """
    執行完整的基因演算法優化流程，並返回找到的最佳個體。
    """
    pop = toolbox.population(n=pop_size)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)

    # --- 動態註冊評估函式 ---
    # 為了將 training_data 傳遞給評估函式，我們在執行前動態註冊它
    # 這確保了 eaSimple 可以找到一個名為 "evaluate" 的標準函式
    toolbox.register("evaluate", evaluate_strategy, training_data=training_data)

    # 執行演算法
    algorithms.eaSimple(pop, toolbox, cxpb=cxpb, mutpb=mutpb, ngen=ngen,
                        stats=stats, halloffame=hof, verbose=True)

    # 清理動態註冊的函式，以避免潛在的副作用
    toolbox.unregister("evaluate")

    return hof[0]
