import numpy as np 
import random
import scipy.optimize as opt
from statsmodels.tsa.seasonal import seasonal_decompose

def summary_stats(returns):

    avg = np.mean(returns)
    var = np.var(returns)
    std = np.std(returns)
    
    return avg, var, std

def ma_short(prices):

    ma_5 = np.mean(prices[:5])
    ma_10 = np.mean(prices[:10])
    ma_20 = np.mean(prices[:20])

    return ma_5, ma_10, ma_20

def ma_long(prices):
    
    ma_50 = 0
    ma_100 = 0
    ma_200 = 0

    if len(prices) >= 50:
         ma_50 = np.mean(prices[:50])
    if len(prices) >= 100:
        ma_100 = np.mean(prices[:100])
    if len(prices) >= 200:
        ma_200 = np.mean(prices[:200])

    return ma_50, ma_100, ma_200

def general_garch(prices):
    prices = prices[::-1]
    log_returns = np.log(prices) - np.log(prices.shift(1))
    returns = 100*log_returns.dropna().reset_index(drop=True)
    num_days = 5
    initial_params = [0.0001, 0.1, 0.8] # Initial omega, alpha, beta

    def garch_likelihood(parameters, ret):
        omega_par, alpha_par, beta_par = parameters
        T = len(ret)
        sigma_squared = np.zeros(T)

        sigma_squared[0] = max(omega_par / (1 - alpha_par - beta_par), 1e-10)
        for t in range(1, T):
            sigma_squared[t] = omega_par + alpha_par * ret[t-1]**2 + beta_par * sigma_squared[t-1]

        log_likelihood = -0.5 * np.sum(np.log(sigma_squared) + (ret**2 / sigma_squared))
        return -log_likelihood 
    
    def simulate_future_returns(ret, sigma_sq, omega, alpha, beta, num_days):
        future_returns = np.zeros(num_days)
        future_volatility = np.zeros(num_days)
    
        random.seed(42)
    
        for t in range(num_days):
            if t == 0:
                future_volatility[t] = omega + alpha * ret**2 + beta * sigma_sq
                future_returns[t] = np.sqrt(sigma_sq) * np.random.normal()
            else:
                future_volatility[t] = np.sqrt(omega + alpha * future_returns[t-1]**2 + beta * future_volatility[t-1])
                future_returns[t] = np.sqrt(future_volatility[t-1]) * np.random.normal()

        return future_returns, future_volatility

    result = opt.minimize(garch_likelihood, initial_params, bounds=[[0, None], [0, 1], [0, 1]], args=(returns, ))
 
    #Parameters
    omega, alpha, beta = result.x

    #Filtered Variance Process
    T = len(returns)
    sigma_sq = np.zeros(T)
    sigma_sq[0] = omega / (1 - alpha - beta)
    for t in range(1, T):
        sigma_sq[t] = omega + alpha * returns[t-1]**2 + beta * sigma_sq[t-1]

    #Simulate future returns for 5 days
    random.seed(42)
    future_returns = np.zeros((len(returns), num_days)) 
    future_volatility = np.zeros((len(returns), num_days))
    for i in range(len(returns)):
        future_returns[i], future_volatility[i] = simulate_future_returns(returns[i], sigma_sq[i], omega, alpha, beta, num_days)

    return omega, alpha, beta, sigma_sq[-1], future_returns[-1][0], future_volatility[-1][0]

def plot_season(prices):
    season_dec = seasonal_decompose(prices, model='additive', period=10)
    return season_dec