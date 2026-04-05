import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest, proportion_confint
from statsmodels.stats.power import NormalIndPower

def calculate_sample_boundaries(baseline_conv, mde, alpha=0.05, power=0.8):
    """Pre-experiment planning to avoid underpowered bias."""

    analysis = NormalIndPower()

    # We use the effect size for proportions
    # For a professional safety margin, we look at the required N for the target MDE
    # and a 'Max' boundary for a more conservative (smaller) lift detection.
    n_min = analysis.solve_power(effect_size=mde, alpha=alpha, power=power, ratio=1.0)

    # Max boundary: Suppose the lift is even smaller (half of MDE), how many would we need?
    n_max = analysis.solve_power(effect_size=mde/2, alpha=alpha, power=power, ratio=1.0)

    return int(np.ceil(n_min)), int(np.ceil(n_max))


def run_statistical_engine(df,alpha=0.05, mde=0.02):

    # Group data for conversion
    groups = df.groupby('group')['converted'].agg(['sum','count'])
    
    try:
        n_test = groups.loc['Test', 'count']
        s_test = groups.loc['Test', 'sum']
        n_con = groups.loc['Control', 'count']
        s_con = groups.loc['Control', 'sum']
    except KeyError as e:
        return {"status": f"🛑 Error: Missing group in data: {e}"}
    
    # 1. Statistical Power Analysis (Was our sample size sufficient for MDE?)
    analysis = NormalIndPower()
    # Effect size is usually calculated as (p2 - p1) / pooled_std
    actual_power = analysis.solve_power(effect_size=mde, nobs1=n_test, alpha=alpha, ratio=1.0)
 
    # 2. Statistical Significance (2-Sample Z-Test)
    z_stat, p_val = proportions_ztest([s_test,s_con], [n_test,n_con])

    # 3. Confidence Intervals (Proportion CI for both groups)
    ci_test = proportion_confint(s_test, n_test, alpha=alpha, method='normal')
    ci_con = proportion_confint(s_con, n_con, alpha=alpha, method='normal')

    # 4. Relative Lift Calculation
    p_test, p_con = s_test/n_test, s_con/n_con
    rel_lift = (p_test - p_con) / p_con if p_con > 0 else 0

    # 5. Financial Audit (Average Revenue Per User)
    arpu_test = df[df['group'] == 'Test']['revenue'].mean()
    arpu_con = df[df['group'] == 'Control']['revenue'].mean()
    rev_lift = (arpu_test - arpu_con) / arpu_con if arpu_con > 0 else 0

    # 6. Automated Professional Decision Logic (Z-Test + MDE + ARPU)
    # A result is "Practically Significant" if the relative lift > mde
    if p_val < alpha and rel_lift > mde and rev_lift > 0:
        status = "🚀 DEPLOY: Statistically significant & Profitable"
    elif p_val < alpha and rev_lift <= 0:
        status = "⚠️ CAUTION: High Conversion but Revenue Dilution"
    elif p_val < alpha and rel_lift <= mde:
        status = "⚖️ NEUTRAL: Significant but below Practical Threshold (MDE)"
    else:
        status = "🛑 HOLD: Insufficient Data or No Impact"

    return {
        "p_val": p_val,
        "rel_lift": rel_lift,
        "rev_lift": rev_lift,
        "power": actual_power,
        "status": status,
        "ci_test": ci_test,
        "ci_con": ci_con,
        "mde_threshold": mde,
        "n_total": n_test + n_con
    }