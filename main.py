import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import random
from matplotlib import colors as mcolors
from tkinter import *
from tkinter import messagebox
import requests
import json
import pyodbc
import logging


# Database connections

load_dotenv()  # Load environment variables from .env file

# Check if the variable is loaded correctly


def get_database_connection():
    connection_string = os.getenv('DATABASE_CONNECTION_STRING')
    if not connection_string:
        raise ValueError("DATABASE_CONNECTION_STRING is not set in the environment variables.")
    try:
        logging.debug(f"Attempting to connect with connection string: {connection_string}")
        return pyodbc.connect(connection_string)
    except pyodbc.Error as e:
        logging.error(f"Database connection error: {e}")
        raise


def add_coin(crypto_id, symbol, name):

    try:
        # Validate crypto_id (positive integer)
        if not isinstance(crypto_id, int) or crypto_id <= 0:
            raise ValueError("Crypto ID must be a positive integer")

        # Validate symbol (alphabetic characters)
        if not symbol.isalpha():
            raise ValueError("Ticker symbol must be alphabetic")

        # Validate name (alphabetic characters)
        if not name.isalpha():
            raise ValueError("Coin name must be alphabetic")

        # If validations pass, insert into database
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO cryptocurrencies (crypto_id, symbol, name) VALUES (?, ?, ?)", (crypto_id, symbol, name))
        connection.commit()
        connection.close()
    
    except Exception as e:
        messagebox.showerror(message=f'Error adding coin: {e}')
        

def transaction_data(crypto_id, transaction_id, quantity, price, cost):
    try:
        # Validate inputs
        if not isinstance(crypto_id, int) or crypto_id <= 0:
            raise ValueError("Crypto ID must be a positive integer")
        
        if not isinstance(transaction_id, int) or transaction_id <= 0:
            raise ValueError("Transaction ID must be a positive integer")

        if not isinstance(quantity, float) or quantity <= 0:
            raise ValueError("Quantity must be a positive float")

        if not isinstance(price, float) or price <= 0:
            raise ValueError("Price must be a positive float")

        if not isinstance(cost, float) or cost <= 0:
            raise ValueError("Total cost must be a positive float")

        # If all validations pass, insert into database
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO transactions (crypto_id, transaction_id, quantity, price, cost) VALUES (?, ?, ?, ?, ?)", (crypto_id, transaction_id, quantity, price, cost))
        connection.commit()
        connection.close()

    except ValueError as ve:
        messagebox.showerror(message=f'Validation Error: {ve}')
        print(f"Validation Error: {ve}")
    except Exception as e:
        messagebox.showerror(message=f'Error inserting transaction data: {e}')
        print(f"Error inserting transaction data: {e}")


    

def symbol_exists(symbol):
    try:
        connection = get_database_connection()
        cursor = connection.cursor()

        # Check if the symbol exists in cryptocurrencies table
        cursor.execute("SELECT TOP 1 1 FROM cryptocurrencies WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()

        connection.close()

        return row is not None

    except Exception as e:
        messagebox.showerror(message=f'Error checking symbol existence: {e}')
        print(f"Error checking symbol existence: {e}")
        return False


def buy_transaction(symbol, new_quantity, new_cost):
    try:
        connection = get_database_connection()
        cursor = connection.cursor()

        # Update query to update quantity based on symbol
        update_query = """
        UPDATE t
        SET t.quantity = t.quantity + ?,
            t.cost = t.cost + ?
        FROM transactions t
        JOIN cryptocurrencies c ON t.crypto_id = c.crypto_id
        WHERE c.symbol = ?
        """

        # Execute the update query
        cursor.execute(update_query, (new_quantity, new_cost, symbol))
        connection.commit()

    

    except Exception as e:
        print(f"Error updating quantity: {e}")

    finally:
        connection.close()

def sell_transaction(symbol, new_quantity, new_cost):
    try:
        connection = get_database_connection()
        cursor = connection.cursor()

        # Check if there are enough quantities to sell
        select_query = """
            SELECT t.quantity
            FROM transactions t
            JOIN cryptocurrencies c ON t.crypto_id = c.crypto_id
            WHERE c.symbol = ?
        """
        cursor.execute(select_query, (symbol,))
        current_quantity = cursor.fetchone()[0]

        if float(new_quantity) <= current_quantity:
            # Update query to update quantity and cost based on symbol for selling
            update_query = """
                UPDATE t
                SET t.quantity = t.quantity - ?,
                    t.cost = t.cost - ?
                FROM transactions t
                JOIN cryptocurrencies c ON t.crypto_id = c.crypto_id
                WHERE c.symbol = ?
            """

            # Execute the update query
            cursor.execute(update_query, (new_quantity, new_cost, symbol))
            connection.commit()

            cursor.execute(select_query, (symbol,))
            updated_quantity = cursor.fetchone()[0]

            if updated_quantity == 0:
                delete_transactions_query = """
                    DELETE FROM transactions
                    WHERE crypto_id = (SELECT crypto_id FROM cryptocurrencies WHERE symbol = ?)
                """
                cursor.execute(delete_transactions_query, (symbol,))
                connection.commit()

                delete_cryptocurrencies_query = """
                    DELETE FROM cryptocurrencies
                    WHERE symbol = ?
                """
                cursor.execute(delete_cryptocurrencies_query, (symbol,))
                connection.commit()


                connection.close()
                return "deleted"
            else:
                connection.close()
                return "updated"
            
        else:
            connection.close()
            return "not_enough"
        
    except Exception as e:
        messagebox.showerror(message=f'An error occurred: {e}')
        print(f"An error occurred: {e}")
   



def fetch_coins():
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT c.crypto_id, c.symbol, c.name,
               t.transaction_id, t.quantity, t.price, t.cost
        FROM cryptocurrencies c
        LEFT JOIN transactions t ON c.crypto_id = t.crypto_id
        ORDER BY c.crypto_id ASC  
        """
        
        cursor.execute(query)
        data = cursor.fetchall()
        
        # Close the connection
        connection.close()
        
        return data
    
    except Exception as e:
        messagebox.showerror(message=f'Error fetching coins: {e}')
        print(f"Error fetching coins: {e}")
        return []


# End of database connections

coins = []

coins = fetch_coins()


win = Tk()

win.title("Folio App")

win.iconbitmap ("icon.ico")

# Heading for the app

heading_frame = Frame(win, borderwidth=5, relief = "ridge")
heading_frame.grid(row=0, column=0, columnspan=7, padx = (20), pady=(10, 20), sticky=E+W)

heading = Label(heading_frame, text="Folio - The Cryptocurrency Portfolio App", fg="#FF9800", font="Arial 24 bold")
heading.pack(padx=10, pady=10)  

# Frame to contain portfolio

portfolio_frame = Frame(win)
portfolio_frame.grid(row=1, column=0, columnspan = 8, padx = (20), pady=(5), sticky=E+W)

 
def portfolio_headings():

    """
    Creates the headings for the columns of the portfolio, and rows with 
    information on the coins can then be placed underneath

    """

    coin_id = Label(portfolio_frame, text = "Coin ID", bg = "Blue", fg= "white", font= "Arial 12 bold", borderwidth=2, relief= "raised")
    coin_id.grid(row=1, column=0, padx = (20,5), sticky=E+W)

    number_of_coins = Label(portfolio_frame, text = "Number owned", bg = "Blue", fg= "white", font= "Arial 12 bold", borderwidth=2, relief= "raised")
    number_of_coins.grid(row=1, column=1, padx = 5, sticky=E+W)

    coin_name = Label(portfolio_frame, text = "Coin Name", bg = "Blue", fg= "white", font= "Arial 12 bold", borderwidth=2, relief= "raised")
    coin_name.grid(row=1, column=2, padx = 5, sticky=E+W)

    ticker = Label(portfolio_frame, text = "Ticker", bg = "Blue", fg= "white", font= "Arial 12 bold", borderwidth=2, relief= "raised")
    ticker.grid(row=1, column=3, padx = 5, sticky=E+W)

    cost = Label(portfolio_frame, text = "Cost", bg = "Blue", fg= "white", font= "Arial 12 bold", borderwidth=2, relief= "raised")
    cost.grid(row=1, column=4,  padx= 5, sticky=E+W)

    current_value = Label(portfolio_frame, text = "Current Value", bg = "Blue", fg= "white", font= "Arial 12 bold", borderwidth=2, relief= "raised")
    current_value.grid(row=1, column=5, padx= 5, sticky=E+W)

    profit_or_loss = Label(portfolio_frame, text = "Profit/Loss", bg = "Blue", fg= "white", font= "Arial 12 bold", borderwidth=2, relief= "raised")
    profit_or_loss.grid(row=1, column=6, padx= 5, sticky=E+W)

    percentage = Label(portfolio_frame, text="%  Gain/Loss", bg="Blue", fg="white", font= "Arial 12 bold", borderwidth=2, relief= "raised" )
    percentage.grid(row=1, column=7, padx=5, sticky=E+W)

    
    win.grid_columnconfigure(1, weight=1)
    portfolio_frame.grid_columnconfigure(0, weight=1)
    portfolio_frame.grid_columnconfigure(1, weight=1)
    portfolio_frame.grid_columnconfigure(2, weight=1)
    portfolio_frame.grid_columnconfigure(3, weight=1)
    portfolio_frame.grid_columnconfigure(4, weight=1)
    portfolio_frame.grid_columnconfigure(5, weight=1)
    portfolio_frame.grid_columnconfigure(6, weight=1)
    portfolio_frame.grid_columnconfigure(7, weight=1)


def profit_loss_indicator(number):

    """
    This function can be used to change text or background to green
    if in profit or red if in loss
    """

    if number > 0:
        return "green"
    elif number == 0:
        return "blue"
    else:
        return "red"
    


load_dotenv()  # Load environment variables from .env file

def get_api_key():
    return os.getenv('API_KEY')

def fetch_api_data(api_key):
    """
    Fetches data from CoinMarketCap API.
    """
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    parameters = {
        'start': '1',
        'limit': '200',
        'convert': 'GBP'
    }
    headers = {
        'X-CMC_PRO_API_KEY': api_key
    }

    try:
        api_request = requests.get(url, headers=headers, params=parameters)
        if api_request.status_code == 200:
            return api_request.json()
        else:
            print("Failed to fetch API data. Status code:", api_request.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print("Error fetching API data:", e)
        return None

# Code inside this block runs only when the script is executed directly
if __name__ == "__main__":
    api_key = get_api_key()
    if api_key:
        api_data = fetch_api_data(api_key)
        
    else:
        print("API key is missing.")


def populate_portfolio():  

    """
    Populate the portfolio frame with data fetched from an API and stored in the database.

    for loop with auto incrementing i to loop through the list fetched by API
    len is determined by the length of the list retrevied through the api call

    Iterates through the cryptocurrency symbol in data fetched from an API and
    if it matches with symbol stored in "coins" list (fetched from the database) it 
    is used to calculate current values, profit/loss and percentage change for each
    cryptocurrency in the portfolio

    It then updates the GUI with this information

    Returns:
            - Total current value of the portfolio.
            - Total profit or loss of the portfolio.
            - Row number for inserting data in the GUI.
            - pie (list): List of cryptocurrency symbols for use in pie chart.
            - pie_size (list): List of sizes for each cryptocurrency slice in a pie chart.
            - crypto_colors (list): List of random colors for each slice of pie chart.

    """

    total_profit_and_loss = 0 

    total_portfolio_value = 0
    
    insertion_row = 2

    pie = []
    pie_size = []


    for i in range(len(api_data["data"])):
        for coin in coins:
            
            if api_data["data"][i]["symbol"] == coin[1]:
                current_price = api_data["data"][i]["quote"]["GBP"]["price"]
                current_value = current_price * float(coin[4])
                purchase_cost = coin[5] * coin[4]
                profit_and_loss = (current_price * (coin[4])) - (purchase_cost)
                percentage_change = (float(profit_and_loss)/float(purchase_cost))*100
                total_profit_and_loss += profit_and_loss
                total_portfolio_value += current_value
                number_of_coins_value = coin[4]
                insertion_row +=1
                pie.append(coin[1])
                pie_size.append((current_value))
                


                coin_id = Label(portfolio_frame, text = coin[0], bg = "Blue", fg= "white")
                coin_id.grid(row= insertion_row, column=0, padx = (20,5), sticky=E+W)

                number_of_coins = Label(portfolio_frame, text = f'{number_of_coins_value:.1f}', bg = "Blue", fg= "white")
                number_of_coins.grid(row= insertion_row, column=1, padx = 5, sticky=E+W)

                coin_name = Label(portfolio_frame, text = api_data["data"][i]["name"], bg = "Blue", fg= "white")
                coin_name.grid(row= insertion_row, column=2, padx = 5, sticky=E+W)

                ticker = Label(portfolio_frame, text = api_data["data"][i]["symbol"], bg = "Blue", fg= "white")
                ticker.grid(row= insertion_row, column=3, padx= 5, sticky=E+W)

                cost = Label(portfolio_frame, text = f'£{purchase_cost:.2f}', bg = "Blue", fg= "white")
                cost.grid(row= insertion_row, column=4, padx= 5, sticky=E+W)

                current_value = Label(portfolio_frame, text = f'£{current_value:.2f}', bg = "Blue", fg= "white")
                current_value.grid(row= insertion_row, column=5, padx= 5, sticky=E+W)

                profit_or_loss = Label(portfolio_frame, text = f'£{profit_and_loss:.2f}', bg = profit_loss_indicator(profit_and_loss), fg= "white")
                profit_or_loss.grid(row= insertion_row, column=6, padx= 5, sticky=E+W)

                percentage = Label(portfolio_frame, text= f'{percentage_change:.2f}', bg= profit_loss_indicator(percentage_change), fg="white")
                percentage.grid(row= insertion_row, column=7, padx=5, sticky=E+W)
    
    pies_size=[]
    for pies in pie_size:
        pies_size.append(pies/total_portfolio_value) 
    
    

    num_crypto = len(pie)
    crypto_colors = random.sample(list(mcolors.CSS4_COLORS.values()), num_crypto)     


    return total_portfolio_value, total_profit_and_loss, insertion_row, pie, pies_size, crypto_colors

    
portfolio_headings()
total_portfolio_value, total_profit_and_loss, insertion_row, pie, pies_size, crypto_colors = populate_portfolio()

    
portfolio_headings()
total_portfolio_value, total_profit_and_loss, insertion_row, pie, pies_size, crypto_colors = populate_portfolio()
print(insertion_row)
# Total value and P/L

total_value_frame = Frame(win)
total_value_frame.grid(row=insertion_row + 1, column=0, columnspan=7, pady=(10, 0), padx=10, sticky="ew")

total_value_frame.grid_columnconfigure(0, weight=1)
total_value_frame.grid_columnconfigure(1, weight=1)
total_value_frame.grid_columnconfigure(2, weight=1)
total_value_frame.grid_columnconfigure(3, weight=1)

total_value_label = Label(total_value_frame, text=f"Total portfolio value: £{total_portfolio_value:.2f}", font=("Helvetica", 14, "bold"), fg="#FF9800")
total_value_label.grid(row=0, column=1, padx=10, sticky="e")

profit_and_loss_label = Label(total_value_frame, text=f"Total P/L: £{total_profit_and_loss:.2f}", font=("Helvetica", 14, "bold"), fg=profit_loss_indicator(total_profit_and_loss))
profit_and_loss_label.grid(row=0, column=2, padx=10, sticky="w")



def fetch_price():

    """
    Fetches price from the api and coin name and calculates the cost of transaction 
    based on the ticker(symbol) entered in to an entry widget
    """
    entered_symbol = coin_symbol_entry.get().upper()
    for coin in api_data["data"]:
        if coin["symbol"] == entered_symbol:
            coin_price = coin["quote"]["GBP"]["price"]
            price_entry.insert(0, f'{coin_price:.2f}')
            crypto_name = coin["name"]
            coin_name_entry.insert(0, crypto_name)
            cost = (coin["quote"]["GBP"]["price"])*float(amount_entry.get())
            total_cost_entry.insert(0, f'{cost:.2f}')   

   
# Entry widgets frame

entry_widget_frame = Frame(win,borderwidth=2, relief = "sunken")
entry_widget_frame.grid(row=insertion_row+2, column=0, columnspan=7, padx=(20), pady=(20), sticky=E+W)

# Entry widgets and labels

coin_id_label = Label(entry_widget_frame, text="Coin ID", bg="#FF9800", fg="black")
coin_id_label.grid(row=0, column=0, pady=5, padx=10)
coin_id_entry = Entry(entry_widget_frame)
coin_id_entry.grid(row=1, column=0, padx=5, pady=5)

transaction_id_label = Label(entry_widget_frame, text="Trans ID", bg="#FF9800", fg="black")
transaction_id_label.grid(row=0, column=1, pady=5)
transaction_id_entry = Entry(entry_widget_frame)
transaction_id_entry.grid(row=1, column=1, padx=5, pady=5)

ticker_label = Label(entry_widget_frame, text="Ticker", bg="#FF9800", fg="black")
ticker_label.grid(row=0, column=2, pady=5)
coin_symbol_entry = Entry(entry_widget_frame)
coin_symbol_entry.grid(row=1, column=2, padx=5, pady=5)

amount_label = Label(entry_widget_frame, text="Amount", bg="#FF9800", fg="black")
amount_label.grid(row=0, column=3, pady=5)
amount_entry = Entry(entry_widget_frame)
amount_entry.grid(row=1, column=3, padx=5, pady=5)

coin_name_label = Label(entry_widget_frame, text="Coin Name", bg="#FF9800", fg="black")
coin_name_label.grid(row=0, column=4, pady=5)
coin_name_entry = Entry(entry_widget_frame)
coin_name_entry.grid(row=1, column=4, padx=5, pady=5)

price_label = Label(entry_widget_frame, text="Price", bg="#FF9800", fg="black")
price_label.grid(row=0, column=5, pady=5)
price_entry = Entry(entry_widget_frame)
price_entry.grid(row=1, column=5, padx =5, pady=5)

total_cost_label = Label(entry_widget_frame, text="Total Cost", bg="#FF9800", fg="black")
total_cost_label.grid(row=0, column=6, pady=5)
total_cost_entry = Entry(entry_widget_frame)
total_cost_entry.grid(row=1, column=6, padx=5, pady=5)


#Frame for crypto banner
image_frame = Frame(win, width=400, height=120)
image_frame.grid(row=insertion_row+3, column=0, columnspan=7, padx=20, pady=(10,20), sticky=E+W)

image = PhotoImage(file="crypto_banner1.png")

image_label = Label(image_frame, image=image)
image_label.place(x=0, y=0, relwidth=1, relheight=1)  # Use place() to position it inside the frame

    
# Function to add populate entry fields with data

def add_data():

    """
    Validates data entered in to entry widgets to create transactions
    Calls different functions to add, update or delete info from 
    database depending on transaction type
    """


    try:
        # Fetch values from GUI entries or wherever they are input
        transaction_id_value = transaction_id_entry.get()
        quantity_value = amount_entry.get()
        price_value = price_entry.get()
        cost_value = total_cost_entry.get()
        crypto_id_value = coin_id_entry.get()
        symbol_value = coin_symbol_entry.get().upper()
        name_value = coin_name_entry.get()
        transaction_type = transaction_var.get()

        # Validate and convert transaction ID
        try:
            transaction_id_value = int(transaction_id_value)
            if transaction_id_value <= 0:
                raise ValueError("Transaction ID must be a positive integer")
        except ValueError:
            messagebox.showerror(message= "Transaction ID must be a positive integer")
            return

        # Validate and convert quantity
        try:
            quantity_value = float(quantity_value)
            if quantity_value <= 0:
                raise ValueError("Amount must be a positive float")
        except ValueError:
            messagebox.showerror(message= "Amount must be a positive float")
            return

        # Validate and convert price
        try:
            price_value = float(price_value)
            if price_value <= 0:
                raise ValueError("Price must be a positive float")
        except ValueError:
            messagebox.showerror(message = "Price must be a positive float")
            return

        # Validate and convert cost
        try:
            cost_value = float(cost_value)
            if cost_value <= 0:
                raise ValueError("Total cost must be a positive float")
        except ValueError:
            messagebox.showerror(message = "Total cost must be a positive float")
            return

        # Validate and convert coin ID
        try:
            crypto_id_value = int(crypto_id_value)
            if crypto_id_value <= 0:
                raise ValueError("Coin ID must be a positive integer")
        except ValueError:
            messagebox.showerror(message= "Coin ID must be a positive integer")
            return

        # Validate symbol and name
        if not symbol_value.isalpha() or len(symbol_value) > 5:
            messagebox.showerror(message = "Ticker symbol must be alphabetic and no longer than 5 characters")
            return
        if not name_value.isalpha():
            messagebox.showerror(message = "Coin name must be alphabetic")
            return
        if transaction_type not in (1, 2):
            messagebox.showerror(message= "Invalid transaction type")
            return

        # Check if the symbol exists in cryptocurrencies table
        if symbol_exists(symbol_value):
            if transaction_type == 1:
                buy_transaction(symbol_value, quantity_value, cost_value)
                messagebox.showinfo(message=f'You have bought £{cost_value:.2f} of {symbol_value}')
            elif transaction_type == 2:
                sell_status = sell_transaction(symbol_value, quantity_value, cost_value)
                if sell_status == "deleted":
                    messagebox.showinfo(message=f"You have sold all of your {symbol_value}, it has been deleted from your portfolio")
                elif sell_status == "updated":
                    messagebox.showinfo(message=f'You have sold £{cost_value:.2f} of {symbol_value}')
                elif sell_status == "not_enough":
                    messagebox.showerror(message=f'You dont have enough {symbol_value} available to sell')
                else:
                    messagebox.showerror(message=f'An error occurred while selling {symbol_value}')
            else:
                messagebox.showerror(message=f'Invalid transaction type: {transaction_type}')

        else:
            if transaction_type == 1:  # Only attempt to add if it's a buy transaction
                add_coin(crypto_id_value, symbol_value, name_value)
                transaction_data(crypto_id_value, transaction_id_value, quantity_value, price_value, cost_value)
                messagebox.showinfo(message=f'You have added £{cost_value:.2f} of {symbol_value}')
            else:
                messagebox.showerror(message=f'You do not own any {symbol_value} to sell')
        
        # Clear input fields
        transaction_id_entry.delete(0, END)
        amount_entry.delete(0, END)
        price_entry.delete(0, END)
        total_cost_entry.delete(0, END)
        coin_id_entry.delete(0, END)
        coin_symbol_entry.delete(0, END)
        coin_name_entry.delete(0, END)

        global coins
        coins = fetch_coins()

        # Update the portfolio display with the refreshed data
        populate_portfolio()

    except Exception as e:
        messagebox.showerror(message= f"An unexpected error occurred: {e}")
        


def graph(pie, pies_size, crypto_colors):
        
        """
        Generates a pie chart to show proprtions of cryptocurrency holdings
        in the portfolio
        """

        labels = pie
        sizes = pies_size
        colors = crypto_colors
        patches, texts = plt.pie(sizes, colors=colors, shadow=True, startangle=90)
        plt.legend(patches, labels, loc="best")
        plt.axis('equal')
        plt.tight_layout()
        plt.show()


# Instructions popup

def instructions():

    """
    Creates instructions popup window
    """

    win1=Tk()
    win1.title("Instructions")
    instructions_frame = Frame(win1)
    instructions_frame.grid(row=2, pady = 20, padx = 20)
    add_new_coin_heading=Label(instructions_frame, text="Add New Coin", font=("Helvetica", 14, "bold"))
    add_new_coin_heading.pack()
    add_new_coin_body_text = """
    1. Enter a unique number into the crypto id and the same number into the transaction id fields.

    2. Enter the ticker into the ticker field.

    3. Select 'Buy'.

    4. Enter the amount of coins you wish to buy into the 'Amount' field.

    5. Click 'Fetch Price' to populate the remaining fields.
    
    6. Click 'Add' 
    """
    add_new_coin_body = Label(instructions_frame, font=("Helvetica", 12), 
                              text=add_new_coin_body_text,
                              wraplength=400) 
   
    add_new_coin_body.pack()

    buy_or_sell_heading=Label(instructions_frame, text="Buy or Sell Existing Coin", font=("Helvetica", 14, "bold"))
    buy_or_sell_heading.pack()
    buy_or_sell_body_text = """
    1. Check the portfolio for the crypto id.

    2. Enter the corresponding number into the crypto id and transaction id fields.

    3. Enter the coin ticker into the ticker field.

    4. Select 'Buy' or 'Sell'.

    5. Enter the amount of coins you wish to buy or sell into the 'Amount' field.

    6. Click 'Fetch Price' to populate the remaining fields.

    7. Click 'Add' 
    """


    buy_or_sell_body = Label(instructions_frame, font=("Helvetica", 12), 
                              text=buy_or_sell_body_text,wraplength=400)                            
    buy_or_sell_body.pack()

# Price checker function

def price_checker():

    """
    Creates price checker popup window
    """

    win2 = Tk()
    win2.title("Price Checker")
    
    coin_ticker_label = Label(win2, text="Enter the coin ticker")
    coin_ticker_label.grid(row=0, pady=20, padx=20)
    
    coin_ticker_entry = Entry(win2)
    coin_ticker_entry.grid(row=1, padx=20)


    crypto_price_label = Label(win2, text='')
    crypto_price_label.grid(row=3, pady=20, padx=20)

    def check_price():

        """
        Gets symbol from entry box and matches it to a symbol from api
        data that has been interated over, if match found will show price

        if no match will show error message
        """
        entered_symbol = coin_ticker_entry.get().upper()
        
        try:
            # Check if the input is alphabetic
            if not entered_symbol.isalpha() or len(entered_symbol) > 6:
                raise ValueError("The coin ticker must be alphabetical and max lenth of 6")
            

            

            # Check if the coin is in the API data
            for coin in api_data["data"]:
                if coin["symbol"] == entered_symbol:
                    crypto_price = coin["quote"]["GBP"]["price"]
                    crypto_price_label.config(text=f'The price of {entered_symbol} is £{crypto_price:.2f}')
                    crypto_price_label.grid(row=3, pady=20, padx=20)
                    coin_ticker_entry.delete(0, 'end')
                    break  # Exit the loop after finding the coin
            else:
                # If no match is found
                crypto_price_label.config(text=f"Coin not found")
                crypto_price_label.grid(row=3, pady=20, padx=20)
        
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))

        coin_ticker_entry.delete(0, 'end')

    checker_button = Button(win2, text="Check Price", bg="#FF9800", fg="black", command=check_price)
    checker_button.grid(row=2, pady=20)
    
    win2.mainloop()

# Buttons

instructions_button = Button(entry_widget_frame, text="Instructions", bg="#FF9800", fg="black",command= instructions)
instructions_button.grid(row=3, column=0, padx=(0,5), pady=10)

# Radio buy/sell buttons

# To determine which radio button has been selected, 1 = buy, 2= sell
transaction_var = IntVar()

buy_button = Radiobutton(entry_widget_frame, text="Buy", variable=transaction_var, value=1)
buy_button.grid(row=3, column=1, pady=5, padx=(15,0), sticky=W)
sell_button = Radiobutton(entry_widget_frame, text="Sell", variable=transaction_var, value=2)
sell_button.grid(row=3, column=1, pady=5, padx =(0,15), sticky=E)

# Button to get price
get_price_button = Button(entry_widget_frame, text="Fetch Info", command=fetch_price, bg = "#FF9800", fg="black")
get_price_button.grid(row=3, column=2, pady=5)

# Add transaction button
add_button = Button(entry_widget_frame, text="Add", bg="#FF9800", fg="black", command=add_data)
add_button.grid(row=3, column=3, pady=5)

# Button to generate pie chart
graph_button = Button(entry_widget_frame, text="Pie Chart", bg="#FF9800", fg="black", command= lambda: graph(pie, pies_size, crypto_colors))
graph_button.grid(row=3, column=4, pady=5)

# Price checker button
price_checker_button= Button(entry_widget_frame, text="Price Checker", bg="#FF9800", fg="black", command= price_checker)
price_checker_button.grid(row=3, column=6, pady=5)

win.mainloop()