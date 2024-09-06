from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64
import yfinance as yf
import functions_package
import mysql.connector

username = 'doadmin'
password = 'AVNS_MtZBitzAUUXU-z8-BNt' 
host = 'usi-student-4m-do-user-17534849-0.d.db.ondigitalocean.com'
port = 25060
database = 'defaultdb'

connection = mysql.connector.connect(
        user=username,
        password=password,
        host=host,
        port=port,
        database=database,
    )


app = FastAPI()

templates = Jinja2Templates(directory="templates")

def create_db():
    cursor = connection.cursor()

    connection.commit()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ticker_list
                    (
                        id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    ticker_name VARCHAR(20) UNIQUE
                    )
    ''')
    connection.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
                    ticker_id BIGINT UNSIGNED,
                    mean VARCHAR(255),
                    variance VARCHAR(255),
                    standard_deviation VARCHAR(255),
                    PRIMARY KEY (ticker_id),
                    FOREIGN KEY (ticker_id) REFERENCES ticker_list(id)
        )
    ''')
    connection.commit()

    cursor.execute('''
       CREATE TABLE IF NOT EXISTS garch (
                    ticker_id BIGINT UNSIGNED,
                    omega VARCHAR(255),
                    alpha VARCHAR(255),
                    beta VARCHAR(255),
                    sigma_sq VARCHAR(255),
                    future_return VARCHAR(255),
                    future_volatility VARCHAR(255),
                    PRIMARY KEY (ticker_id),
                    FOREIGN KEY (ticker_id) REFERENCES ticker_list(id)
        )
    ''')
    connection.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS moving_average (
                    ticker_id BIGINT UNSIGNED,
                    MA_5 VARCHAR(255),
                    MA_10 VARCHAR(255),
                    MA_20 VARCHAR(255),
                    MA_50 VARCHAR(255),
                    MA_100 VARCHAR(255),
                    MA_200 VARCHAR(255),
                    PRIMARY KEY (ticker_id),
                    FOREIGN KEY (ticker_id) REFERENCES ticker_list(id)
        )
    ''')
    connection.commit()

    

create_db()



@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/analyze")
async def analyze_stock(ticker: str, request: Request):
    print(ticker)
    stock = yf.Ticker(ticker)
    df = stock.history(period="1y")

    if df.empty:
        raise HTTPException(status_code=404, detail="Ticker not found or no data available")
    else:
       cursor = connection.cursor()
       sql = "INSERT IGNORE INTO ticker_list (ticker_name) VALUES (%s)"
       cursor.execute(sql, (ticker,))
       connection.commit()

       returns = df['Close'].pct_change()
       mean, var, std = functions_package.summary_stats(returns)
       ma_5, ma_10, ma_20 = functions_package.ma_short(returns)
       ma_50, ma_100, ma_200 = functions_package.ma_long(returns)
       omega, alpha, beta, sigma_sq, future_return, future_volatility = functions_package.general_garch(returns)

       cursor.execute("SELECT id FROM ticker_list WHERE ticker_name = %s", (ticker,))
       result = cursor.fetchone()


       sql = """
        INSERT IGNORE INTO stats (ticker_id, mean, variance, standard_deviation)
        VALUES (%s, %s, %s, %s);
        """
       values = (result[0], mean, var, std)
       cursor.execute(sql, values)
       connection.commit()

       sql = """
        INSERT IGNORE INTO garch (ticker_id, omega,
                    alpha, beta, sigma_sq, future_return, future_volatility)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
       values = (result[0], omega, alpha, beta, sigma_sq, future_return, future_volatility)
       cursor.execute(sql, values)
       connection.commit()

       sql = """
        INSERT IGNORE INTO moving_average (ticker_id, 
                    MA_5,
                    MA_10,
                    MA_20,
                    MA_50,
                    MA_100,
                    MA_200)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
       values = (result[0], ma_5, ma_10, ma_20,  ma_50, ma_100, ma_200)
       cursor.execute(sql, values)
       connection.commit()





    returns = df['Close'].pct_change()
    avg, var, std = functions_package.summary_stats(returns)
    ma_5, ma_10, ma_20 = functions_package.ma_short(returns)
    ma_50, ma_100, ma_200 = functions_package.ma_long(returns)
    omega, alpha, beta, sigma_sq, future_return, future_volatility = functions_package.general_garch(returns)

    seasonal_dec = functions_package.plot_season(df["Close"])

    fig, ax = plt.subplots(4, 1, figsize=(10, 8))

    fig.suptitle("Time series decomposition", fontsize=16)
    ax[0].plot(seasonal_dec.observed, label='Observed')
    ax[0].legend(loc='upper left')
    ax[1].plot(seasonal_dec.trend, label='Trend')
    ax[1].legend(loc='upper left')
    ax[2].plot(seasonal_dec.seasonal, label='Seasonal')
    ax[2].legend(loc='upper left')
    ax[3].plot(seasonal_dec.resid, label='Residual')
    ax[3].legend(loc='upper left')


    
    pngImage = io.BytesIO()
    fig.savefig(pngImage)
    pngImageB64String = base64.b64encode(pngImage.getvalue()).decode('ascii')
    return templates.TemplateResponse("stock_analysis.html", {"request": request, "ticker": ticker, 
    "avg": round(avg, 4), "var": round(var, 4), "std": round(std, 4), "ma5": round(ma_5, 4), "ma10": round(ma_10, 4), "ma20": round(ma_20, 4), 
    "ma50": round(ma_50, 4), "ma100": round(ma_100, 4), "ma200": round(ma_200, 4),
    "omega": round(omega, 4), "beta": round(beta, 4), "alpha": round(alpha, 4), "sigma_sq": round(sigma_sq, 4), 
    "future_return": round(future_return, 4), "future_volatility": round(future_volatility, 4), 
    "plot": pngImageB64String})
