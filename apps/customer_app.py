"""GetACar customer app: browse cars and record purchases in the OLTP database.

Usage (from repo root):
    python -m apps.customer_app
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem
from PyQt5.uic import loadUi
import mysql.connector
from datetime import datetime

from src import config
from src.db import get_connection


class GetACarApp(QMainWindow):
    def __init__(self):
        super(GetACarApp, self).__init__()
        loadUi(str(config.UI_DIR / "customer_app.ui"), self)

        # Database connection (credentials from .env)
        self.db = get_connection(config.OLTP_DB)
        self.cursor = self.db.cursor()

        # Navigation setup
        self.stackedWidget.setCurrentWidget(self.loginPage)
        self.loginButton.clicked.connect(self.handle_login)
        self.viewCarsButton.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.viewCarsPage))
        self.buyCarsButton.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.buyCarsPage))
        self.backToMainFromView.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.mainPage))
        self.backToMainFromBuy.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.mainPage))
        self.completeTransactionButton.clicked.connect(self.handle_transaction)

        # Load cars into dropdown and table
        self.load_cars()

        # Populate payment modes dropdown
        self.paymentModeDropdown.addItems(["Cash", "Credit Card", "Debit Card", "UPI"])

    def handle_login(self):
        username = self.usernameLineEdit.text()
        password = self.passwordLineEdit.text()

        if username == config.CUSTOMER_APP_USER and password == config.CUSTOMER_APP_PASSWORD:
            QMessageBox.information(self, "Login Successful", "Welcome to GetACar!")
            self.stackedWidget.setCurrentWidget(self.mainPage)
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password!")

    def load_cars(self):
        try:
            # Fetch cars from database
            self.cursor.execute("SELECT CarID, Name, Price, Company FROM Cars")
            cars = self.cursor.fetchall()
            print("Fetched Cars Data:", cars)  # Debug print for car data

            # Populate dropdown
            self.carDropdown.clear()
            for car in cars:
                if car[1] and car[2]:  # Ensure name and price are valid
                    print("Adding to ComboBox:", car[1], car[0])  # Debug print for dropdown items
                    self.carDropdown.addItem(f"{car[1]} - ${car[2]}", car[0])

            # Initialize table
            self.carsTable.setRowCount(len(cars))
            self.carsTable.setColumnCount(3)
            self.carsTable.setHorizontalHeaderLabels(["Name", "Price", "Company"])

            # Populate table
            for row_idx, car in enumerate(cars):
                name = car[1] if car[1] else "Unknown"
                price = f"${car[2]}" if car[2] else "N/A"
                company = car[3] if car[3] else "Unknown"
                print(f"Setting table row {row_idx}: {name}, {price}, {company}")  # Debug print for table items
                self.carsTable.setItem(row_idx, 0, QTableWidgetItem(name))
                self.carsTable.setItem(row_idx, 1, QTableWidgetItem(price))
                self.carsTable.setItem(row_idx, 2, QTableWidgetItem(company))

        except mysql.connector.Error as err:
            print(f"Database error during load_cars: {err}")  # Debug print for database errors
            QMessageBox.critical(self, "Database Error", f"Error loading car data: {err}")

    def handle_transaction(self):
        # Handle new car purchase
        selected_car = self.carDropdown.currentData()  # Get CarID
        customer_name = self.customerName.text()
        customer_address = self.customerAddress.text()
        payment_mode = self.paymentModeDropdown.currentText()
        transaction_date = datetime.now().strftime('%Y-%m-%d')
        amount = self.carDropdown.currentText().split('$')[1]

        if not customer_name or not customer_address:
            QMessageBox.warning(self, "Incomplete Details", "Please fill in all required fields.")
            return

        try:
            # Insert or update customer details
            self.cursor.execute("""
                INSERT INTO Customers (FullName, Address)
                VALUES (%s, %s) ON DUPLICATE KEY UPDATE Address = VALUES(Address)
            """, (customer_name, customer_address))
            self.db.commit()

            # Fetch CustomerID
            self.cursor.execute("SELECT CustomerID FROM Customers WHERE FullName = %s", (customer_name,))
            customer_id = self.cursor.fetchone()[0]

            # Insert transaction
            self.cursor.execute("""
                INSERT INTO Transactions (CarID, CustomerID, PaymentMode, TransactionDate, Amount)
                VALUES (%s, %s, %s, %s, %s)
            """, (selected_car, customer_id, payment_mode, transaction_date, amount))
            self.db.commit()

            QMessageBox.information(self, "Transaction Successful", "Purchase completed successfully!")
            self.stackedWidget.setCurrentWidget(self.mainPage)
        except mysql.connector.Error as err:
            print(f"Database error during transaction: {err}")  # Debug print for database errors
            QMessageBox.critical(self, "Database Error", f"An error occurred: {err}")

    def closeEvent(self, event):
        # Close database connection
        self.db.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = GetACarApp()
    mainWindow.show()
    sys.exit(app.exec_())
