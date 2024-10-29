import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import getpass
import hashlib
import json

class LifeTracker:
    def __init__(self, db_name="life_tracker.db"):
        self.conn = sqlite3.connect(db_name)
        self.setup_database()
        self.current_user = None
        self.default_metrics = {
            "Health": [
                {
                    "name": "Sleep Quality",
                    "type": "qualitative",
                    "min_value": 1,
                    "max_value": 10,
                    "description": "How refreshed do you feel? (1-10)",
                    "example_low": "1 = Feeling like a zombie who binge-watched all seasons of everything",
                    "example_high": "10 = Ready to fight a bear (not recommended)"
                },
                {
                    "name": "Hours of Sleep",
                    "type": "quantitative",
                    "min_value": 0,
                    "max_value": 24,
                    "description": "How many hours did you sleep? (0-24)",
                    "example": "Round to nearest quarter hour (e.g., 7.25, 7.5, 7.75)"
                },
                {
                    "name": "Daily Steps",
                    "type": "quantitative",
                    "min_value": 0,
                    "max_value": 100000,
                    "description": "How many steps did you take today?",
                    "example": "From your fitness tracker/phone"
                }
            ],
            "Wealth": [
                {
                    "name": "Discretionary Spending",
                    "type": "quantitative",
                    "min_value": 0,
                    "max_value": None,
                    "description": "How much did you spend on non-essentials? ($)",
                    "example": "That coffee you 'needed' counts!"
                },
                {
                    "name": "Financial Stress Level",
                    "type": "qualitative",
                    "min_value": 1,
                    "max_value": 10,
                    "description": "How stressed are you about money? (1-10)",
                    "example_low": "1 = Living your best budget life",
                    "example_high": "10 = Considering selling your comic book collection"
                }
            ],
            "Relationships": [
                {
                    "name": "Quality Time",
                    "type": "quantitative",
                    "min_value": 0,
                    "max_value": 1440,
                    "description": "Minutes spent in meaningful interactions",
                    "example": "Real conversations, not just liking their Instagram posts"
                },
                {
                    "name": "Social Connection",
                    "type": "qualitative",
                    "min_value": 1,
                    "max_value": 10,
                    "description": "How connected do you feel to others? (1-10)",
                    "example_low": "1 = Your plant is your best friend",
                    "example_high": "10 = You're the main character in everyone's story"
                }
            ]
        }

    def setup_database(self):
        """Create the necessary tables if they don't exist."""
        cursor = self.conn.cursor()

        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Create categories table with user_id
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            name TEXT NOT NULL,
            UNIQUE(user_id, name),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)

        # Create metrics table with description fields
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            category_id INTEGER,
            name TEXT NOT NULL,
            type TEXT CHECK(type IN ('quantitative', 'qualitative')),
            min_value REAL,
            max_value REAL,
            description TEXT,
            example TEXT,
            example_low TEXT,
            example_high TEXT,
            UNIQUE(user_id, name),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
        """)

        # Create entries table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            metric_id INTEGER,
            value REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (metric_id) REFERENCES metrics (id)
        )
        """)

        self.conn.commit()

    def hash_password(self, password):
        """Hash a password for storing."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def register_user(self):
        """Register a new user."""
        print("\n🌟 Welcome to Life Tracker! Let's set up your account! 🌟")

        while True:
            username = input("Choose a username: ").strip()
            if not username:
                print("❌ Username cannot be empty!")
                continue

            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone() is not None:
                print("❌ Username already taken!")
                continue

            password = getpass.getpass("Choose a password: ")
            if not password:
                print("❌ Password cannot be empty!")
                continue

            confirm_password = getpass.getpass("Confirm password: ")
            if password != confirm_password:
                print("❌ Passwords don't match!")
                continue

            break

        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, self.hash_password(password))
        )
        self.conn.commit()
        self.current_user = {
            'id': cursor.lastrowid,
            'username': username
        }

        print("\n✅ Account created successfully!")
        self.setup_user_metrics()

    def login_user(self):
        """Log in an existing user."""
        while True:
            username = input("Username: ").strip()
            password = getpass.getpass("Password: ")

            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, password_hash FROM users WHERE username = ?",
                (username,)
            )
            result = cursor.fetchone()

            if result and result[1] == self.hash_password(password):
                self.current_user = {
                    'id': result[0],
                    'username': username
                }
                print(f"\n✅ Welcome back, {username}!")
                return True

            print("❌ Invalid username or password!")
            retry = input("Try again? (y/n): ").lower()
            if retry != 'y':
                return False

    def setup_user_metrics(self):
        """Set up initial metrics for a new user."""
        print("\n🎯 Let's set up your tracking metrics!")
        print("1. Use default metrics")
        print("2. Create your own metrics")

        choice = input("\nYour choice (1-2): ")

        if choice == "1":
            self.setup_default_metrics()
        else:
            self.create_custom_metrics()

    def setup_default_metrics(self):
        """Set up the default set of metrics for a user."""
        cursor = self.conn.cursor()

        for category_name, metrics in self.default_metrics.items():
            # Create category
            cursor.execute(
                "INSERT INTO categories (user_id, name) VALUES (?, ?)",
                (self.current_user['id'], category_name)
            )
            category_id = cursor.lastrowid

            # Create metrics
            for metric in metrics:
                cursor.execute("""
                    INSERT INTO metrics (
                        user_id, category_id, name, type, min_value, max_value,
                        description, example, example_low, example_high
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.current_user['id'], category_id, metric['name'],
                    metric['type'], metric['min_value'], metric['max_value'],
                    metric['description'],
                    metric.get('example'),
                    metric.get('example_low'),
                    metric.get('example_high')
                ))

        self.conn.commit()
        print("\n✅ Default metrics set up successfully!")

    def create_custom_metrics(self):
        """Guide user through creating custom metrics."""
        print("\n📊 Let's create your custom metrics!")

        categories = {}
        while True:
            print("\nFirst, let's create categories (e.g., Health, Work, Hobbies)")
            category_name = input("Enter category name (or press Enter to finish): ").strip()

            if not category_name:
                if not categories:
                    print("❌ You need at least one category!")
                    continue
                break

            categories[category_name] = []

            while True:
                print(f"\nAdding metric to {category_name}")
                metric = {}

                metric['name'] = input("Metric name (or press Enter to finish category): ").strip()
                if not metric['name']:
                    break

                while True:
                    metric_type = input("Type (1 for qualitative, 2 for quantitative): ").strip()
                    if metric_type in ['1', '2']:
                        metric['type'] = 'qualitative' if metric_type == '1' else 'quantitative'
                        break
                    print("❌ Please enter 1 or 2!")

                metric['min_value'] = float(input("Minimum value: "))
                metric['max_value'] = float(input("Maximum value (or -1 for no maximum): "))
                if metric['max_value'] == -1:
                    metric['max_value'] = None

                metric['description'] = input("Description: ")

                if metric['type'] == 'qualitative':
                    metric['example_low'] = input(f"Example for lowest value ({metric['min_value']}): ")
                    metric['example_high'] = input(f"Example for highest value ({metric['max_value']}): ")
                else:
                    metric['example'] = input("Example: ")

                categories[category_name].append(metric)

        # Save custom metrics to database
        cursor = self.conn.cursor()

        for category_name, metrics in categories.items():
            cursor.execute(
                "INSERT INTO categories (user_id, name) VALUES (?, ?)",
                (self.current_user['id'], category_name)
            )
            category_id = cursor.lastrowid

            for metric in metrics:
                cursor.execute("""
                    INSERT INTO metrics (
                        user_id, category_id, name, type, min_value, max_value,
                        description, example, example_low, example_high
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.current_user['id'], category_id, metric['name'],
                    metric['type'], metric['min_value'], metric['max_value'],
                    metric['description'],
                    metric.get('example'),
                    metric.get('example_low'),
                    metric.get('example_high')
                ))

        self.conn.commit()
        print("\n✅ Custom metrics set up successfully!")

    def manage_metrics(self):
        """Manage existing metrics."""
        while True:
            print("\n🔧 Metric Management")
            print("1. View current metrics")
            print("2. Add new metric")
            print("3. Edit existing metric")
            print("4. Delete metric")
            print("5. Back to main menu")

            choice = input("\nYour choice (1-5): ")

            if choice == "1":
                self.view_metrics()
            elif choice == "2":
                self.add_new_metric()
            elif choice == "3":
                self.edit_metric()
            elif choice == "4":
                self.delete_metric()
            elif choice == "5":
                break
            else:
                print("❌ Invalid choice!")

    def view_metrics(self):
        """View all current metrics."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.name, m.name, m.type, m.min_value, m.max_value, m.description
            FROM metrics m
            JOIN categories c ON m.category_id = c.id
            WHERE m.user_id = ?
            ORDER BY c.name, m.name
        """, (self.current_user['id'],))

        results = cursor.fetchall()
        current_category = None

        print("\n" + "="*50)
        print("📊 YOUR CURRENT METRICS 📊".center(50))
        print("="*50 + "\n")

        for row in results:
            category, name, type_, min_val, max_val, desc = row
            if current_category != category:
                current_category = category
                print(f"\n{category.upper()}")
                print("-"*25)
            print(f"• {name} ({type_})")
            print(f"  └─ {desc}")
            print(f"  └─ Range: {min_val} to {max_val if max_val is not None else 'unlimited'}")

    def add_new_metric(self):
        """Add a new metric."""
        print("\n➕ Add New Metric")

        # Show existing categories and option to create new
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name FROM categories WHERE user_id = ?",
            (self.current_user['id'],)
        )
        categories = cursor.fetchall()

        print("\nExisting categories:")
        for i, (_, name) in enumerate(categories, 1):
            print(f"{i}. {name}")
        print(f"{len(categories) + 1}. Create new category")

        while True:
            try:
                choice = int(input("\nSelect category number: "))
                if 1 <= choice <= len(categories):
                    category_id = categories[choice-1][0]
                    category_name = categories[choice-1][1]
                    break
                elif choice == len(categories) + 1:
                    category_name = input("Enter new category name: ").strip()
                    cursor.execute(
                        "INSERT INTO categories (user_id, name) VALUES (?, ?)",
                        (self.current_user['id'], category_name)
                    )
                    category_id = cursor.lastrowid
                    break
            except ValueError:
                print("❌ Please enter a number!")

        # Get metric details
        metric = {}
        metric['name'] = input("Metric name: ").strip()

        while True:
            metric_type = input("Type (1 for qualitative, 2 for quantitative): ").strip()
            if metric_type in ['1', '2']:
                metric['type'] = 'qualitative' if metric_type == '1' else 'quantitative'
                break
            print("❌ Please enter 1 or 2!")

        metric['min_value'] = float(input("Minimum value: "))
        metric['max_value'] = float(input("Maximum value (or -1 for no maximum): "))
        if metric['max_value'] == -1:
            metric['max_value'] = None

        metric['description'] = input("Description: ")

        if metric['type'] == 'qualitative':
            metric['example_low'] = input(f"Example for lowest value ({metric['min_value']}): ")
            metric['example_high'] = input(f"Example for highest value ({metric['max_value']}): ")
            metric['example'] = None
        else:
            metric['example'] = input("Example: ")
            metric['example_low'] = None
            metric['example_high'] = None

        # Save to database
        cursor.execute("""
            INSERT INTO metrics (
                user_id, category_id, name, type, min_value, max_value,
                description, example, example_low, example_high
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.current_user['id'], category_id, metric['name'],
            metric['type'], metric['min_value'], metric['max_value'],
            metric['description'], metric['example'],
            metric['example_low'], metric['example_high']
        ))

        self.conn.commit()
        print("\n✅ New metric added successfully!")

    def edit_metric(self):
        """Edit an existing metric."""
        self.view_metrics()

        cursor = self.conn.cursor()
        metric_name = input("\nEnter the name of the metric to edit: ").strip()

        cursor.execute("""
            SELECT id, type, min_value, max_value, description,
                   example, example_low, example_high
            FROM metrics
            WHERE user_id = ? AND name = ?
        """, (self.current_user['id'], metric_name))

        metric = cursor.fetchone()
        if not metric:
            print("❌ Metric not found!")
            return

        metric_id = metric[0]
        print("\nLeave blank to keep current value")

        # Get new values
        new_min = input(f"New minimum value [{metric[2]}]: ").strip()
        new_max = input(f"New maximum value [{metric[3]}]: ").strip()
        new_desc = input(f"New description [{metric[4]}]: ").strip()

        if metric[1] == 'qualitative':
            new_ex_low = input(f"New example for lowest value [{metric[6]}]: ").strip()
            new_ex_high = input(f"New example for highest value [{metric[7]}]: ").strip()
            new_ex = None
        else:
            new_ex = input(f"New example [{metric[5]}]: ").strip()
            new_ex_low = None
            new_ex_high = None

        # Update database with new values, keeping old values where blank
        cursor.execute("""
            UPDATE metrics
            SET min_value = ?,
                max_value = ?,
                description = ?,
                example = ?,
                example_low = ?,
                example_high = ?
            WHERE id = ?
        """, (
            float(new_min) if new_min else metric[2],
            float(new_max) if new_max else metric[3],
            new_desc if new_desc else metric[4],
            new_ex if new_ex else metric[5],
            new_ex_low if new_ex_low else metric[6],
            new_ex_high if new_ex_high else metric[7],
            metric_id
        ))

        self.conn.commit()
        print("\n✅ Metric updated successfully!")

    def delete_metric(self):
        """Delete an existing metric."""
        self.view_metrics()

        metric_name = input("\nEnter the name of the metric to delete: ").strip()

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id FROM metrics
            WHERE user_id = ? AND name = ?
        """, (self.current_user['id'], metric_name))

        metric = cursor.fetchone()
        if not metric:
            print("❌ Metric not found!")
            return

        confirm = input(f"\n⚠️ Are you sure you want to delete '{metric_name}'? This will delete all associated data! (y/n): ")
        if confirm.lower() != 'y':
            print("Deletion cancelled.")
            return

        # Delete metric and its entries
        cursor.execute("DELETE FROM entries WHERE metric_id = ?", (metric[0],))
        cursor.execute("DELETE FROM metrics WHERE id = ?", (metric[0],))
        self.conn.commit()

        print("\n✅ Metric and associated data deleted successfully!")

    def interactive_entry(self, entry_date=None):
        """Interactive command-line interface for data entry."""
        if self.current_user is None:
            print("❌ Please log in first!")
            return

        cursor = self.conn.cursor()

        if entry_date is None:
            entry_date = datetime.now()
            date_str = "today"
        else:
            date_str = entry_date.strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT m.name, m.type, m.min_value, m.max_value, c.name,
                   m.description, m.example, m.example_low, m.example_high
            FROM metrics m
            JOIN categories c ON m.category_id = c.id
            WHERE m.user_id = ?
            ORDER BY c.name, m.name
        """, (self.current_user['id'],))

        metrics = cursor.fetchall()

        print("\n" + "="*50)
        print(f"🌟 DAILY TRACKING - {date_str.upper()} 🌟".center(50))
        print("="*50 + "\n")

        current_category = None
        for metric in metrics:
            name, type_, min_val, max_val, category, desc, ex, ex_low, ex_high = metric

            if current_category != category:
                current_category = category
                print(f"\n{category.upper()}")
                print("-"*25)

            print(f"\n• {name}")
            print(f"  └─ {desc}")

            if type_ == 'qualitative':
                print(f"  └─ Low: {ex_low}")
                print(f"  └─ High: {ex_high}")
            elif ex:
                print(f"  └─ Example: {ex}")

            while True:
                try:
                    value = input("Your response (press Enter to skip): ")
                    if not value.strip():
                        print("➡️ Skipping...")
                        break  # Break out of the inner while loop only

                    value = float(value)

                    cursor.execute("""
                        INSERT INTO entries (user_id, metric_id, value, timestamp)
                        SELECT ?, m.id, ?, ?
                        FROM metrics m
                        WHERE m.user_id = ? AND m.name = ?
                    """, (self.current_user['id'], value, entry_date,
                         self.current_user['id'], name))

                    self.conn.commit()
                    print("✅ Recorded!")
                    break  # Break out of the inner while loop only
                except ValueError as e:
                    print(f"❌ Oops! {e}. Let's try that again.")

        print("\n✅ Daily tracking complete!")

    def get_correlation(self, metric1_name, metric2_name, days):
        """Calculate correlation between two metrics for the specified number of days."""
        if self.current_user is None:
            print("❌ Please log in first!")
            return None

        cursor = self.conn.cursor()

        query = """
        WITH metric_data AS (
            SELECT
                m.name,
                e.value,
                date(e.timestamp) as date
            FROM entries e
            JOIN metrics m ON e.metric_id = m.id
            WHERE
                m.user_id = ?
                AND m.name IN (?, ?)
                AND e.timestamp >= date('now', ?)
        )
        SELECT
            m1.date,
            m1.value as metric1_value,
            m2.value as metric2_value
        FROM
            (SELECT * FROM metric_data WHERE name = ?) m1
        JOIN
            (SELECT * FROM metric_data WHERE name = ?) m2
        ON m1.date = m2.date
        ORDER BY m1.date
        """

        days_ago = f'-{days} days'
        cursor.execute(query, (
            self.current_user['id'], metric1_name, metric2_name,
            days_ago, metric1_name, metric2_name
        ))

        results = cursor.fetchall()
        if not results:
            return None

        df = pd.DataFrame(results, columns=['date', 'metric1', 'metric2'])
        correlation = df['metric1'].corr(df['metric2'])

        return correlation

    def visualize_metric(self, metric_name, days=7):
        """Visualize a single metric over the specified number of days."""
        if self.current_user is None:
            print("❌ Please log in first!")
            return

        cursor = self.conn.cursor()

        query = """
        SELECT
            date(e.timestamp) as date,
            e.value
        FROM entries e
        JOIN metrics m ON e.metric_id = m.id
        WHERE
            m.user_id = ?
            AND m.name = ?
            AND e.timestamp >= date('now', ?)
        ORDER BY e.timestamp
        """

        days_ago = f'-{days} days'
        cursor.execute(query, (self.current_user['id'], metric_name, days_ago))

        results = cursor.fetchall()
        if not results:
            print(f"No data available for {metric_name} in the past {days} days.")
            return

        dates, values = zip(*results)

        plt.figure(figsize=(10, 6))
        plt.plot(dates, values, 'bo-')
        plt.title(f'{metric_name} - Past {days} Days')
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.show()

def main():
    tracker = LifeTracker()

    while True:
        print("\n" + "="*50)
        print("🌈 LIFE TRACKER 🌈".center(50))
        print("="*50 + "\n")

        if tracker.current_user is None:
            print("Please choose an option:")
            print("-"*25)
            print("1. 👤 Login")
            print("2. ✨ Register")
            print("3. ❌ Exit")
            print("-"*25)

            choice = input("\nYour choice (1-3): ")

            if choice == "1":
                if not tracker.login_user():
                    continue
            elif choice == "2":
                tracker.register_user()
            elif choice == "3":
                print("\n👋 Thanks for using Life Tracker!")
                break
            else:
                print("❌ Invalid choice!")
                continue

        # Main menu for logged-in users
        print(f"\nWelcome, {tracker.current_user['username']}!")
        print("-"*50)
        print("Available actions:")
        print("-"*25)
        print("1. 📝 Enter today's data")
        print("2. 📊 Check correlation between metrics")
        print("3. 📅 Enter data for a different date")
        print("4. 📈 Visualize metric over time")
        print("5. ⚙️  Manage metrics")
        print("6. 👋 Logout")
        print("-"*25)

        choice = input("\nWhat would you like to do? (1-6): ")

        if choice == "1":
            tracker.interactive_entry()
        elif choice == "2":
            # TODO: Implement correlation check
            print("Feature coming soon!")
        elif choice == "3":
            try:
                date_str = input("Enter date (YYYY-MM-DD): ")
                entry_date = datetime.strptime(date_str, "%Y-%m-%d")
                tracker.interactive_entry(entry_date)
            except ValueError:
                print("❌ Invalid date format! Please use YYYY-MM-DD")
        elif choice == "4":
            # TODO: Implement visualization
            print("Feature coming soon!")
        elif choice == "5":
            tracker.manage_metrics()
        elif choice == "6":
            tracker.current_user = None
            print("\n👋 Logged out successfully!")
        else:
            print("❌ Invalid choice!")

if __name__ == "__main__":
    main()
