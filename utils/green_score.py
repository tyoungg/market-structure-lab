def calculate_return_premium(stock_return, twin_return):
    """
    Simple difference between stock return and twin portfolio return.
    """
    return stock_return - twin_return

def calculate_green_score(
    stock_return,
    twin_return,
    valuation_change=0,
    liquidity_change=0,
    momentum_persistence=0
):
    """
    Evolved Green Score based on multiple factors.
    """
    return_premium = calculate_return_premium(stock_return, twin_return)

    # Weights from the design doc
    # 0.40 * return_premium
    # 0.25 * pe_expansion (valuation_change)
    # 0.15 * liquidity_change
    # 0.20 * momentum_persistence

    score = (
        0.40 * return_premium +
        0.25 * valuation_change +
        0.15 * liquidity_change +
        0.20 * momentum_persistence
    )

    return score
