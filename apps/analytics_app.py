"""GetAnalysis manager dashboard: reads the analytical warehouse.

Usage (from repo root):
    python -m apps.analytics_app
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QVBoxLayout
from PyQt5.uic import loadUi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import mysql.connector

from src import config
from src.db import get_connection


class GetAnalysisApp(QMainWindow):
    def __init__(self):
        super(GetAnalysisApp, self).__init__()
        loadUi(str(config.UI_DIR / "analytics_app.ui"), self)

        # Apply styles to the date filters
        self.startDateEdit.setStyleSheet("""
            QDateEdit {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
            }
            QCalendarWidget QAbstractItemView {
                background-color: white;
                color: black; /* Make dates visible */
                selection-background-color: lightblue;
            }
            QCalendarWidget QWidget {
                color: black; /* Ensure all text is visible */
            }
        """)

        self.endDateEdit.setStyleSheet("""
            QDateEdit {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
            }
            QCalendarWidget QAbstractItemView {
                background-color: white;
                color: black; /* Make dates visible */
                selection-background-color: lightblue;
            }
            QCalendarWidget QWidget {
                color: black; /* Ensure all text is visible */
            }
        """)

        # Database connection (credentials from .env)
        self.db = get_connection(config.WAREHOUSE_DB)
        self.cursor = self.db.cursor()

        # Navigation setup
        self.stackedWidget.setCurrentWidget(self.loginPage)
        self.loginButton.clicked.connect(self.handle_login)
        self.viewTransactionsButton.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.viewTransactionsPage))
        self.viewAnalyticsButton.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.viewAnalyticsPage))
        self.revenueTrendsButton.clicked.connect(self.plot_revenue_trends)
        self.topPerformingCarsButton.clicked.connect(self.plot_top_performing_cars)
        self.totalRevenueButton.clicked.connect(self.show_total_revenue)
        self.backToMainFromTransactions.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.mainPage))
        self.backToMainFromAnalytics.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.mainPage))
        self.backToAnalyticsFromRevenue.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.viewAnalyticsPage))
        self.backToAnalyticsFromTopCars.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.viewAnalyticsPage))
        self.backToAnalyticsFromTotalRevenue.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.viewAnalyticsPage))
        self.applyDateFilterButton.clicked.connect(self.filter_transactions)

        # Populate data
        self.load_transactions()

    def handle_login(self):
        username = self.usernameLineEdit.text()
        password = self.passwordLineEdit.text()

        if username == config.MANAGER_APP_USER and password == config.MANAGER_APP_PASSWORD:
            QMessageBox.information(self, "Login Successful", "Welcome to GetAnalysis!")
            self.stackedWidget.setCurrentWidget(self.mainPage)
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password!")

    def load_transactions(self):
     try:
        # Fetch all transactions by default
        self.cursor.execute("""
            SELECT t.TransactionID, c.Name AS CarName, t.Amount, t.PaymentMode, t.TransactionDate
            FROM Transactions t
            JOIN Cars c ON t.CarID = c.CarID
        """)
        transactions = self.cursor.fetchall()

        # Set up the table
        self.transactionsTable.setRowCount(len(transactions))
        self.transactionsTable.setColumnCount(5)  # TransactionID, CarName, Amount, PaymentMode, Date
        self.transactionsTable.setHorizontalHeaderLabels(["Transaction ID", "Car Name", "Amount ($)", "Payment Mode", "Date"])

        for row_idx, transaction in enumerate(transactions):
            self.transactionsTable.setItem(row_idx, 0, QTableWidgetItem(str(transaction[0])))  # Transaction ID
            self.transactionsTable.setItem(row_idx, 1, QTableWidgetItem(transaction[1]))  # Car Name
            self.transactionsTable.setItem(row_idx, 2, QTableWidgetItem(f"${transaction[2]:.2f}"))  # Amount
            self.transactionsTable.setItem(row_idx, 3, QTableWidgetItem(transaction[3]))  # Payment Mode
            self.transactionsTable.setItem(row_idx, 4, QTableWidgetItem(transaction[4].strftime('%Y-%m-%d')))  # Date
     except mysql.connector.Error as err:
        QMessageBox.critical(self, "Database Error", f"Error loading transactions: {err}")

    def filter_transactions(self):
     try:
        # Get selected date range
        start_date = self.startDateEdit.date().toPyDate()
        end_date = self.endDateEdit.date().toPyDate()

        # Fetch filtered transactions
        self.cursor.execute("""
            SELECT t.TransactionID, c.Name AS CarName, t.Amount, t.PaymentMode, t.TransactionDate
            FROM Transactions t
            JOIN Cars c ON t.CarID = c.CarID
            WHERE t.TransactionDate BETWEEN %s AND %s
        """, (start_date, end_date))
        transactions = self.cursor.fetchall()

        # Set up the table
        self.transactionsTable.setRowCount(len(transactions))
        for row_idx, transaction in enumerate(transactions):
            self.transactionsTable.setItem(row_idx, 0, QTableWidgetItem(str(transaction[0])))  # Transaction ID
            self.transactionsTable.setItem(row_idx, 1, QTableWidgetItem(transaction[1]))  # Car Name
            self.transactionsTable.setItem(row_idx, 2, QTableWidgetItem(f"${transaction[2]:.2f}"))  # Amount
            self.transactionsTable.setItem(row_idx, 3, QTableWidgetItem(transaction[3]))  # Payment Mode
            self.transactionsTable.setItem(row_idx, 4, QTableWidgetItem(transaction[4].strftime('%Y-%m-%d')))  # Date
     except mysql.connector.Error as err:
        QMessageBox.critical(self, "Database Error", f"Error applying date filter: {err}")


    def plot_revenue_trends(self):
     try:
        # Ensure the widget has a layout
        if not isinstance(self.revenueTrendsPage.layout(), QVBoxLayout):
            self.revenueTrendsPage.setLayout(QVBoxLayout())

        # Clear existing layout content
        layout = self.revenueTrendsPage.layout()
        while layout.count():
            widget_to_remove = layout.takeAt(0).widget()
            if widget_to_remove:
                widget_to_remove.deleteLater()

        # Query pre-aggregated revenue trends
        self.cursor.execute("""
            SELECT CONCAT(Year, '-', LPAD(Month, 2, '0')) AS MonthYear, TotalRevenue
            FROM RevenueTrends
            ORDER BY Year, Month
        """)
        data = self.cursor.fetchall()

        # Check for empty data
        if not data:
            QMessageBox.information(self, "No Data", "No revenue trends data available.")
            return

        # Separate months and revenues
        months = [row[0] for row in data]
        revenues = [row[1] for row in data]

        # Plot the data
        figure = Figure(figsize=(10, 6), dpi=100)
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)

        # Plot and style
        ax.plot(
            months, revenues, marker="o", linestyle="-", color="#1f77b4", linewidth=2,
            markersize=6, label="Monthly Revenue"
        )
        ax.fill_between(months, revenues, color="#d0e2f2", alpha=0.4)  # Add area fill for aesthetics

        # Titles and labels
        ax.set_title("Revenue Trends Over Time", fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel("Month-Year", fontsize=12, labelpad=10)
        ax.set_ylabel("Revenue (Million $)", fontsize=12, labelpad=10)

        # Customizing x-axis
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months, rotation=45, fontsize=10, ha="right")
        ax.xaxis.set_tick_params(width=0.8, length=6)
        ax.yaxis.set_tick_params(width=0.8, length=6)

        # Grid and background
        ax.grid(color="gray", linestyle="--", linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(True)  # Ensure grid lines are behind the plot
        ax.set_facecolor("#f5f5f5")  # Light background color for plot area

        # Add legend
        ax.legend(loc="upper left", fontsize=10, frameon=False)

        # Add canvas to layout
        layout.addWidget(canvas)

        # Transition to the Revenue Trends page
        self.stackedWidget.setCurrentWidget(self.revenueTrendsPage)

     except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to load revenue trends: {e}")




    def plot_top_performing_cars(self):
     try:
        # Ensure the widget has a layout
        if not isinstance(self.topPerformingCarsPage.layout(), QVBoxLayout):
            self.topPerformingCarsPage.setLayout(QVBoxLayout())

        # Clear existing layout content
        layout = self.topPerformingCarsPage.layout()
        while layout.count():
            widget_to_remove = layout.takeAt(0).widget()
            if widget_to_remove:
                widget_to_remove.deleteLater()

        # Query pre-aggregated top-performing cars
        self.cursor.execute("""
            SELECT CarName, TotalSales
            FROM TopPerformingCars
            ORDER BY TotalSales DESC
            LIMIT 10
        """)
        data = self.cursor.fetchall()

        # Check for empty data
        if not data:
            QMessageBox.information(self, "No Data", "No top-performing cars data available.")
            return

        # Separate car names and sales
        car_names = [row[0] for row in data]
        total_sales = [row[1] for row in data]

        # Plot the data
        figure = Figure(figsize=(10, 6), dpi=100)
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)

        # Bar plot and styling
        bars = ax.barh(
            car_names, total_sales, color="#ff7f0e", edgecolor="black", height=0.6
        )

        # Add text labels for each bar
        for bar in bars:
            width = bar.get_width()
            ax.text(
                width + 2,  # Position text to the right of the bar
                bar.get_y() + bar.get_height() / 2,
                f"{width:,}",  # Format the number with commas
                va="center",
                fontsize=10,
                color="black",
            )

        # Titles and labels
        ax.set_title("Top Performing Cars (Most Sold)", fontsize=16, fontweight="bold", pad=20)
        ax.set_xlabel("Total Sales", fontsize=12, labelpad=10)
        ax.set_ylabel("Car Names", fontsize=12, labelpad=10)

        # Grid and background
        ax.xaxis.set_tick_params(width=0.8, length=6)
        ax.yaxis.set_tick_params(width=0.8, length=6)
        ax.grid(axis="x", linestyle="--", color="gray", alpha=0.7)
        ax.set_axisbelow(True)  # Ensure grid lines are behind the bars
        ax.set_facecolor("#f5f5f5")  # Light background for plot

        # Adjust layout
        ax.set_xlim(0, max(total_sales) * 1.1)  # Add some space on the right for labels
        ax.invert_yaxis()  # Invert y-axis for better readability (largest at the top)

        # Add the canvas to the layout
        layout.addWidget(canvas)

        # Transition to the Top Performing Cars page
        self.stackedWidget.setCurrentWidget(self.topPerformingCarsPage)

     except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to load top-performing cars: {e}")




    def show_total_revenue(self):
        try:
            self.cursor.execute("SELECT TotalRevenue FROM TotalRevenueSummary ORDER BY TotalRevenue DESC LIMIT 1")
            total_revenue = self.cursor.fetchone()[0]
            self.totalRevenueValue.setText(f"${total_revenue:,.2f}")
            self.stackedWidget.setCurrentWidget(self.totalRevenuePage)

        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Database Error", f"Error loading total revenue: {err}")
 

    def closeEvent(self, event):
        self.db.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = GetAnalysisApp()
    mainWindow.show()
    sys.exit(app.exec_())
