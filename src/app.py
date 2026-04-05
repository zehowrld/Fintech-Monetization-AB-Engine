import os
import streamlit as st
import plotly.express as px
from ingestion import ingest_monetization_data
from engine import run_statistical_engine, calculate_sample_boundaries

st.set_page_config(page_title="Fintech Revenue Lab", layout="wide", page_icon="💰")

# API key status check
api_status = "Connected ✅" if os.getenv('ALPHA_VANTAGE_KEY') else "API key missing using Fallback ⚠️"

# Pre-Experiment Setup (Professional Planning) ---
MDE = 0.02
ALPHA = 0.05
n_min, n_max = calculate_sample_boundaries(baseline_conv=0.10, mde=MDE, alpha= ALPHA)

# --- Header Section ---
st.title("💸 Fintech User Monetization Engine")
st.sidebar.header("📊 Experiment Planning (Unbiased)")
st.sidebar.write(f"**Market API:** {api_status}")
st.sidebar.info(f"**Statistically Required N:**\n\nMin: {n_min:,}\n\nMax Boundary: {n_max:,}")

# --- Execution ---
df = ingest_monetization_data(n_required=n_min * 2) # Total users for 2 groups
# We define our Alpha and MDE (Delta) here
results = run_statistical_engine(df, alpha=ALPHA, mde=MDE)

# --- Top-Level Metrics ---
col1, col2, col3, col4, col5= st.columns(5)
col1.metric("Conversion Lift", f"{results['rel_lift']:.2%}")
col2.metric("Revenue Lift", f"{results['rev_lift']:.2%}")
col3.metric("P-Value", f"{results['p_val']:.4f}")
col4.metric("Statistical Power", f"{results['power']:.2%}")
col5.metric("Total Samples", f"{results['n_total']:,}")

# Big Status Banner
st.subheader(f"Executive Decision: {results['status']}")

if results['n_total'] < n_min:
    st.warning(f"🚨 BIAS ALERT: Your sample size ({results['n_total']}) is lower than the required {n_min}. Results may be unreliable.")
else:
    st.success(f"✅ POWER VALIDATED: Sample size meets the {n_min} requirement for an unbiased test.")

# --- Visualizations ---
st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Revenue Distribution")
    fig_box = px.box(df[df["converted"] == 1], x="group", y="revenue", color="group",
                     points="all", title="Spending Patterns (Paying Users)")
    st.plotly_chart(fig_box, use_container_width=True)

with right:
    st.subheader("Confidence Intervals (95%)")
    # Show the range of conversion for each group
    st.write(f"**Control Group Range:** {results['ci_con'][0]:.2%} to {results['ci_con'][1]:.2%}")
    st.write(f"**Test Group Range:** {results['ci_test'][0]:.2%} to {results['ci_test'][1]:.2%}")
    st.info(f"Target Delta (MDE): **{results['mde_threshold']:.1%}**")

st.divider()
with st.expander("🔍 Live Data Audit"):
    st.dataframe(df.head(50), use_container_width=True)