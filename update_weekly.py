import mysql.connector
import functions_package
import yfinance as yf

username = 'doadmin'
password = 
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

def update_stock_data():
    cursor = connection.cursor()
    cursor.execute("SELECT id, ticker_name FROM ticker_list")
    tickers = cursor.fetchall()
    
    for ticker_id, ticker_name in tickers:
        stock = yf.Ticker(ticker_name)
        df = stock.history(period="1y")
        
        if df.empty:
            print(f"No data available for {ticker_name}")
            continue
        
        returns = df['Close'].pct_change()
        mean, var, std = functions_package.summary_stats(returns)
        ma_5, ma_10, ma_20 = functions_package.ma_short(returns)
        ma_50, ma_100, ma_200 = functions_package.ma_long(returns)
        omega, alpha, beta, sigma_sq, future_return, future_volatility = functions_package.general_garch(returns)
        
        sql = """
        UPDATE stats SET
        mean = %s,
        variance = %s,
        standard_deviation = %s
        WHERE ticker_id = %s;
        """
        values = (mean, var, std, ticker_id)
        cursor.execute(sql, values)
        connection.commit()
        
        sql = """
        UPDATE garch SET
        omega = %s,
        alpha = %s,
        beta = %s,
        sigma_sq = %s,
        future_return = %s,
        future_volatility = %s
        WHERE ticker_id = %s;
        """
        values = (omega, alpha, beta, sigma_sq, future_return, future_volatility, ticker_id)
        cursor.execute(sql, values)
        connection.commit()
        
        sql = """
        UPDATE moving_average SET
        MA_5 = %s,
        MA_10 = %s,
        MA_20 = %s,
        MA_50 = %s,
        MA_100 = %s,
        MA_200 = %s
        WHERE ticker_id = %s;
        """
        values = (ma_5, ma_10, ma_20, ma_50, ma_100, ma_200, ticker_id)
        cursor.execute(sql, values)
        connection.commit()
        
        connection.commit()

        print(f"Updated data for {ticker_name}")

    cursor.close()
    connection.close()

update_stock_data()
