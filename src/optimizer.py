import random
import numpy as np
import pandas as pd

from deap import base, creator, tools, algorithms

# 核心模組導入 (已重構)
from src.feat import calculate_features
from src.sp_signal import generate_signals
from src.backtest import run_backtest
from src.stats import calculate_backtest_stats

# --- 全域設定 ---
INITIAL_CAPITAL = 100000.0
POSITION_SIZE = 1

# --- 基因演算法設定 ---
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)
toolbox = base.Toolbox()

# --- 策略參數空間定義 ---
ATR_PERIOD_RANGE = (5, 50)
ATR_MULTIPLIER_RANGE = (1.0, 5.0)
HIGH_VOL_TREND_CHOICES = [-1, 1]

toolbox.register("attr_atr_period", random.randint, ATR_PERIOD_RANGE[0], ATR_PERIOD_RANGE[1])
toolbox.register("attr_atr_multiplier", random.uniform, ATR_MULTIPLIER_RANGE[0], ATR_MULTIPLIER_RANGE[1])
toolbox.register("attr_high_vol_trend", random.choice, HIGH_VOL_TREND_CHOICES)
toolbox.register("individual", tools.initCycle, creator.Individual,
                 (toolbox.attr_atr_period, toolbox.attr_atr_multiplier, toolbox.attr_high_vol_trend), n=1)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

# --- 適應度評估函式 (最終版本) ---
def evaluate_strategy(individual: list, training_data: pd.DataFrame) -> tuple:
    atr_period, atr_multiplier, high_vol_trend = individual[0], individual[1], individual[2]
    try:
        # 1. 動態計算特徵
        features_df = calculate_features(training_data, atr_period=int(atr_period))

        # 2. 動態生成訊號
        signals_df = generate_signals(
            features_df,
            high_vol_trend=high_vol_trend,
            atr_period=int(atr_period),
            atr_multiplier=atr_multiplier
        )

        # 3. 執行回測
        trade_log, equity_curve = run_backtest(
            price_data=training_data,
            signals=signals_df['signal'],
            init_cap=INITIAL_CAPITAL,
            pos_size=POSITION_SIZE
        )

        # 4. 計算績效
        stats = calculate_backtest_stats(
            trade_log=trade_log,
            equity_curve=equity_curve,
            initial_capital=INITIAL_CAPITAL
        )
        sharpe_ratio = stats.get("夏普比率", -100.0)

        return (sharpe_ratio,) if np.isfinite(sharpe_ratio) else (-100.0,)
    except Exception:
        return (-100.0,)

# --- 註冊遺傳演算法運算子 ---
toolbox.register("evaluate", evaluate_strategy)
toolbox.register("mate", tools.cxTwoPoint)

def custom_mutate(individual, indpb):
    if random.random() < indpb:
        individual[0] = random.randint(ATR_PERIOD_RANGE[0], ATR_PERIOD_RANGE[1])
    if random.random() < indpb:
        individual[1] += random.gauss(0, 0.5)
        individual[1] = np.clip(individual[1], ATR_MULTIPLIER_RANGE[0], ATR_MULTIPLIER_RANGE[1])
    if random.random() < indpb:
        individual[2] = random.choice(HIGH_VOL_TREND_CHOICES)
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

    # 將 training_data 作為固定參數傳遞給評估函式
    toolbox.register("map", lambda func, pop: map(lambda ind: func(ind, training_data=training_data), pop))

    # 執行演算法
    algorithms.eaSimple(pop, toolbox, cxpb=cxpb, mutpb=mutpb, ngen=ngen,
                        stats=stats, halloffame=hof, verbose=True)

    return hof[0]
