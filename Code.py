"""
Stock Portfolio Analysis Program
Final Portfolio Assignment - Enhanced Version with Debugging
"""

import csv
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import pandas as pd
import yfinance as yf
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import logging
import os  # Added for path verification

# Configure logging
logging.basicConfig(filename='stock_analysis.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class StockPortfolio:
    def __init__(self):
        """Initialize the stock portfolio with database connection"""
        self.conn = sqlite3.connect('stocks.db')
        self.cursor = self.conn.cursor()
        self._create_tables()
        self.stock_data = []
        
    def _create_tables(self):
        """Create database tables if they don't exist"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume INTEGER NOT NULL
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    shares INTEGER NOT NULL,
                    purchase_price REAL NOT NULL,
                    purchase_date TEXT NOT NULL
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            raise

    def import_from_csv(self, filepath):
        """Import stock data from CSV file into database"""
        try:
            with open(filepath, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.cursor.execute('''
                        INSERT INTO stocks (symbol, date, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (row['Symbol'], row['Date'], float(row['Open']), 
                          float(row['High']), float(row['Low']), 
                          float(row['Close']), int(row['Volume'])))
            self.conn.commit()
            logging.info(f"Successfully imported data from {filepath}")
            return True
        except (FileNotFoundError, csv.Error, ValueError) as e:
            logging.error(f"Error importing CSV: {e}")
            return False

    def add_to_portfolio(self, symbol, shares, purchase_price, purchase_date):
        """Add a stock to the portfolio"""
        try:
            self.cursor.execute('''
                INSERT INTO portfolio (symbol, shares, purchase_price, purchase_date)
                VALUES (?, ?, ?, ?)
            ''', (symbol.upper(), shares, purchase_price, purchase_date))
            self.conn.commit()
            logging.info(f"Added {shares} shares of {symbol} to portfolio")
            return True
        except sqlite3.Error as e:
            logging.error(f"Error adding to portfolio: {e}")
            return False

    def get_portfolio(self):
        """Retrieve all portfolio holdings"""
        try:
            self.cursor.execute('SELECT * FROM portfolio')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error retrieving portfolio: {e}")
            return []

    def get_stock_data(self, symbol):
        """Retrieve historical data for a specific stock"""
        try:
            self.cursor.execute('''
                SELECT date, close FROM stocks 
                WHERE symbol = ? 
                ORDER BY date
            ''', (symbol.upper(),))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error retrieving stock data: {e}")
            return []

    def calculate_portfolio_value(self):
        """Calculate current value of the portfolio"""
        holdings = self.get_portfolio()
        total_value = 0.0
        
        for stock in holdings:
            symbol = stock[1]
            shares = stock[2]
            
            # Get current price from Yahoo Finance API
            try:
                current_price = self.get_current_price(symbol)
                if current_price is not None:
                    total_value += shares * current_price
            except Exception as e:
                logging.error(f"Error getting current price for {symbol}: {e}")
                continue
                
        return total_value

    def get_current_price(self, symbol):
        """Get current stock price using Yahoo Finance API"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period='1d')
            if not data.empty:
                return data['Close'].iloc[-1]
            return None
        except Exception as e:
            logging.error(f"Yahoo Finance API error for {symbol}: {e}")
            return None

    def plot_stock_performance(self, symbol):
        """Plot historical performance of a stock with debug output"""
        data = self.get_stock_data(symbol)
        if not data:
            print(f"No data available for {symbol}")
            return False
            
        dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in data]
        prices = [row[1] for row in data]
        
        plt.figure(figsize=(10, 5))
        plt.plot(dates, prices, label=f'{symbol} Closing Price')
        
        # Formatting
        plt.title(f'{symbol} Historical Performance')
        plt.xlabel('Date')
        plt.ylabel('Price ($)')
        plt.legend()
        plt.grid(True)
        
        # Format x-axis dates
        date_format = DateFormatter("%Y-%m-%d")
        plt.gca().xaxis.set_major_formatter(date_format)
        plt.gcf().autofmt_xdate()
        
        # Debug output
        output_path = f'{symbol}_performance.png'
        plt.savefig(output_path)
        plt.close()
        print(f"Saved performance chart to: {os.path.abspath(output_path)}")
        logging.info(f"Generated performance plot for {symbol}")
        return True

    def portfolio_performance_report(self):
        """Generate a comprehensive portfolio performance report with debug output"""
        holdings = self.get_portfolio()
        if not holdings:
            print("No holdings in portfolio")
            return False, {}
            
        report_data = []
        total_investment = 0
        total_current_value = 0
        
        for stock in holdings:
            symbol = stock[1]
            shares = stock[2]
            purchase_price = stock[3]
            investment = shares * purchase_price
            total_investment += investment
            
            current_price = self.get_current_price(symbol)
            if current_price is None:
                print(f"Could not get current price for {symbol}")
                continue
                
            current_value = shares * current_price
            total_current_value += current_value
            gain_loss = current_value - investment
            gain_loss_pct = (gain_loss / investment) * 100
            
            report_data.append({
                'Symbol': symbol,
                'Shares': shares,
                'Avg Purchase Price': f"${purchase_price:.2f}",
                'Current Price': f"${current_price:.2f}",
                'Investment': f"${investment:.2f}",
                'Current Value': f"${current_value:.2f}",
                'Gain/Loss ($)': f"${gain_loss:.2f}",
                'Gain/Loss (%)': f"{gain_loss_pct:.2f}%"
            })
            
        # Create DataFrame for nice formatting
        df = pd.DataFrame(report_data)
        
        # Summary statistics
        summary = {
            'Total Investment': f"${total_investment:.2f}",
            'Total Current Value': f"${total_current_value:.2f}",
            'Total Gain/Loss ($)': f"${total_current_value - total_investment:.2f}",
            'Total Gain/Loss (%)': f"{((total_current_value - total_investment) / total_investment * 100):.2f}%"
        }
        
        # Save to CSV
        csv_path = 'portfolio_report.csv'
        df.to_csv(csv_path, index=False)
        print(f"Saved portfolio report to: {os.path.abspath(csv_path)}")
        
        # Generate plot
        symbols = [stock[1] for stock in holdings]
        allocations = []
        for stock in holdings:
            price = self.get_current_price(stock[1])
            if price is not None:
                allocations.append(stock[2] * price)
        
        plt.figure(figsize=(8, 8))
        plt.pie(allocations, labels=symbols, autopct='%1.1f%%')
        plt.title('Portfolio Allocation')
        
        # Debug output
        chart_path = 'portfolio_allocation.png'
        plt.savefig(chart_path)
        plt.close()
        print(f"Saved allocation chart to: {os.path.abspath(chart_path)}")
        
        logging.info("Generated portfolio performance report")
        return df, summary

    def export_to_csv(self, filename='stock_data_export.csv'):
        """Export stock data to CSV file with debug output"""
        try:
            self.cursor.execute('SELECT * FROM stocks')
            data = self.cursor.fetchall()
            
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['ID', 'Symbol', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
                writer.writerows(data)
                
            print(f"Exported data to: {os.path.abspath(filename)}")
            logging.info(f"Exported data to {filename}")
            return True
        except (sqlite3.Error, csv.Error, IOError) as e:
            logging.error(f"Error exporting data: {e}")
            return False

    def __del__(self):
        """Clean up database connection when object is destroyed"""
        self.conn.close()

class StockAppGUI:
    def __init__(self, portfolio):
        """Initialize the GUI application"""
        self.portfolio = portfolio
        self.root = tk.Tk()
        self.root.title("Stock Portfolio Manager")
        self.root.geometry("800x600")
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface"""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Import CSV", command=self.import_csv_dialog)
        file_menu.add_command(label="Export CSV", command=self.export_csv_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Main frames
        input_frame = tk.LabelFrame(self.root, text="Portfolio Management", padx=5, pady=5)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        display_frame = tk.LabelFrame(self.root, text="Portfolio Information", padx=5, pady=5)
        display_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Input widgets
        tk.Label(input_frame, text="Symbol:").grid(row=0, column=0, sticky="e")
        self.symbol_entry = tk.Entry(input_frame, width=10)
        self.symbol_entry.grid(row=0, column=1)
        
        tk.Label(input_frame, text="Shares:").grid(row=0, column=2, sticky="e")
        self.shares_entry = tk.Entry(input_frame, width=10)
        self.shares_entry.grid(row=0, column=3)
        
        tk.Label(input_frame, text="Purchase Price:").grid(row=0, column=4, sticky="e")
        self.price_entry = tk.Entry(input_frame, width=10)
        self.price_entry.grid(row=0, column=5)
        
        tk.Label(input_frame, text="Purchase Date (YYYY-MM-DD):").grid(row=0, column=6, sticky="e")
        self.date_entry = tk.Entry(input_frame, width=12)
        self.date_entry.grid(row=0, column=7)
        
        add_btn = tk.Button(input_frame, text="Add to Portfolio", command=self.add_to_portfolio)
        add_btn.grid(row=0, column=8, padx=5)
        
        report_btn = tk.Button(input_frame, text="Generate Report", command=self.generate_report)
        report_btn.grid(row=0, column=9, padx=5)
        
        # Display widgets
        self.text_display = tk.Text(display_frame, wrap="word")
        self.text_display.pack(fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(self.text_display)
        scrollbar.pack(side="right", fill="y")
        self.text_display.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.text_display.yview)
        
    def import_csv_dialog(self):
        """Open file dialog to import CSV"""
        filepath = filedialog.askopenfilename(title="Select CSV File", 
                                             filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        if filepath:
            if self.portfolio.import_from_csv(filepath):
                messagebox.showinfo("Success", "CSV file imported successfully!")
            else:
                messagebox.showerror("Error", "Failed to import CSV file")
    
    def export_csv_dialog(self):
        """Open file dialog to export CSV"""
        filepath = filedialog.asksaveasfilename(title="Save CSV File", 
                                               defaultextension=".csv",
                                               filetypes=(("CSV files", "*.csv"), ("All files", "*.*")))
        if filepath:
            if self.portfolio.export_to_csv(filepath):
                messagebox.showinfo("Success", "Data exported successfully!")
            else:
                messagebox.showerror("Error", "Failed to export data")
    
    def add_to_portfolio(self):
        """Add stock to portfolio from GUI inputs"""
        symbol = self.symbol_entry.get()
        shares = self.shares_entry.get()
        price = self.price_entry.get()
        date = self.date_entry.get()
        
        try:
            shares = int(shares)
            price = float(price)
            
            if self.portfolio.add_to_portfolio(symbol, shares, price, date):
                messagebox.showinfo("Success", f"Added {shares} shares of {symbol} to portfolio")
                self.display_portfolio()
            else:
                messagebox.showerror("Error", "Failed to add to portfolio")
        except ValueError:
            messagebox.showerror("Error", "Invalid input values")
    
    def generate_report(self):
        """Generate and display portfolio report"""
        try:
            report, summary = self.portfolio.portfolio_performance_report()
            
            self.text_display.delete(1.0, tk.END)
            self.text_display.insert(tk.END, "PORTFOLIO PERFORMANCE REPORT\n\n")
            self.text_display.insert(tk.END, "Individual Holdings:\n")
            self.text_display.insert(tk.END, report.to_string(index=False))
            
            self.text_display.insert(tk.END, "\n\nSummary:\n")
            for key, value in summary.items():
                self.text_display.insert(tk.END, f"{key}: {value}\n")
                
            # Show the allocation chart
            try:
                img = tk.PhotoImage(file="portfolio_allocation.png")
                
                # Need to keep reference to avoid garbage collection
                if hasattr(self, 'img_label'):
                    self.img_label.destroy()
                    
                self.img_label = tk.Label(self.root, image=img)
                self.img_label.image = img  # Keep reference
                self.img_label.pack()
            except Exception as e:
                messagebox.showerror("Chart Error", f"Could not load allocation chart: {str(e)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
            logging.error(f"Report generation error: {e}")
    
    def display_portfolio(self):
        """Display current portfolio holdings"""
        holdings = self.portfolio.get_portfolio()
        
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, "CURRENT PORTFOLIO HOLDINGS\n\n")
        
        if not holdings:
            self.text_display.insert(tk.END, "No holdings in portfolio")
            return
            
        headers = ["ID", "Symbol", "Shares", "Purchase Price", "Purchase Date"]
        self.text_display.insert(tk.END, "\t".join(headers) + "\n")
        
        for stock in holdings:
            self.text_display.insert(tk.END, f"{stock[0]}\t{stock[1]}\t{stock[2]}\t${stock[3]:.2f}\t{stock[4]}\n")
    
    def run(self):
        """Run the application"""
        self.display_portfolio()
        self.root.mainloop()

def main():
    """Main function to run the program"""
    print("Stock Portfolio Analysis Program")
    print("--------------------------------")
    print(f"Current working directory: {os.getcwd()}")
    
    portfolio = StockPortfolio()
    
    # Sample data import (for demonstration)
    try:
        if portfolio.import_from_csv('sample_stock_data.csv'):
            print("Sample data imported successfully")
    except FileNotFoundError:
        print("Note: Sample data file not found. You can import your own CSV.")
    
    # Initialize and run GUI
    app = StockAppGUI(portfolio)
    app.run()

if __name__ == "__main__":
    main()