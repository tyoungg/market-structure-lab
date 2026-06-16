import matplotlib.pyplot as plt
import streamlit as st

def plot_event_study(df, ticker, benchmark="SPY"):
    """
    Plots the stock return vs benchmark return around an event.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df.index, df["stock_return"], label=f"{ticker} Return")
    ax.plot(df.index, df["benchmark_return"], label=f"{benchmark} Return", linestyle="--")
    ax.set_title(f"Event Study: {ticker} vs {benchmark}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Normalized Return")
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

def plot_stock_vs_twins(comparison_df, ticker):
    """
    Plots the stock return vs its twin portfolio.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(comparison_df.index, comparison_df["stock_return"], label=f"{ticker} Return")
    ax.plot(comparison_df.index, comparison_df["twin_return"], label="Twin Portfolio", linestyle="--")
    ax.set_title(f"Counterfactual Analysis: {ticker} vs Twins")
    ax.set_xlabel("Date")
    ax.set_ylabel("Normalized Return")
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

def plot_green_score_distribution(results_df):
    """
    Plots a histogram of Green Scores.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(results_df["green_score"], bins=20, color="skyblue", edgecolor="black")
    ax.set_title("Distribution of Green Scores")
    ax.set_xlabel("Green Score")
    ax.set_ylabel("Frequency")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
