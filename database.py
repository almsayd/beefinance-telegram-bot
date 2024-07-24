import sqlite3
from datetime import datetime


def connect():
    return sqlite3.connect("telegram.db")
    # cs = db.cursor()


def create_db():
    db = connect()
    cs = db.cursor()

    cs.execute("""
        create table if not exists users(
            id integer primary key,
            nickname varchar not null ,
            username varchar not null,
            balance integer real
        )
    """)
    cs.execute("""
        CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY,
            user_id REFERENCES users(id),
            amount INTEGER REAL,
            type STRING CHECK ( type in ('income' , 'expense') ),
            category STRING,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cs.execute("""
        CREATE TABLE IF NOT EXISTS reminders(
            id INTEGER PRIMARY KEY ,
            user_id REFERENCES users(id),
            message VARCHAR,
            date DATE,
            time TIME,
            isEveryDay BOOLEAN DEFAULT 0
        )
    """)

    db.commit()


# название говорит само за себя
def close_db():
    db = connect()
    cs = db.cursor()
    db.close()


#добавление юзера в бд с проверкой на идентичных юзеров
def user_exists(user_id):
    with connect() as db:
        cs = db.cursor()
        cs.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        exists = cs.fetchone() is not None
    return exists


def fetch_all_users():
    with connect() as db:
        cs = db.cursor()
        cs.execute("SELECT id FROM users ")
        users = cs.fetchall()
        return [
            user_id[0] for user_id in users
        ]


def register_user(user_id, username, balance, nickname):
    with connect() as db:
        cs = db.cursor()
        cs.execute("INSERT INTO users (id, username, balance , nickname) VALUES (?, ?, ?, ?)", (user_id, username,
                                                                                                balance, nickname))


def get_username(user_id):
    with connect() as db:
        cs = db.cursor()
        cs.execute("""
            SELECT username FROM users WHERE id =? 
        """, (user_id,))
        result = cs.fetchone()
        if result is None:
            return None
        else:
            return result[0]


def get_balance(user_id):
    with connect() as db:
        cs = db.cursor()
        cs.execute("""
            SELECT balance FROM users WHERE id =?
        """, (user_id,))
        balance = cs.fetchone()

        return balance[0]


def add_transaction(user_id, amount, type, category):
    with connect() as db:
        cs = db.cursor()
        try:
            cs.execute("INSERT INTO transactions (user_id, amount, type, category) VALUES (?, ?, ?, ?)",
                       (user_id, amount, type, category))
            if type == 'income':
                cs.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
            elif type == 'expense':
                cs.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, user_id))
            db.commit()
            return True
        except Exception as e:
            print(f"Ошибка при добавлении транзакции: {e}")
            return False


def get_transactions(user_id):
    with connect() as db:
        cs = db.cursor()

        cs.execute("SELECT amount,type,category,date FROM transactions WHERE user_id=?", (user_id,))
        transactions = cs.fetchall()
        return transactions


def set_reminder(user_id, message, date, time, isEveryDay):
    current_year = datetime.now().year

    full_date = f"{current_year}-{date}"

    formatted_date = datetime.strptime(full_date, '%Y-%m-%d').strftime('%Y-%m-%d')
    formatted_time = datetime.strptime(time, '%H:%M').strftime('%H:%M')
    with connect() as db:
        cs = db.cursor()
        try:
            cs.execute("INSERT INTO reminders (user_id, message, date, time, isEveryDay) VALUES (?, ?, ?, ?, ?)",
                       (user_id, message, formatted_date, formatted_time, isEveryDay))
            db.commit()
        except Exception as e:
            print(f"Ошибка при добавлении напоминания: {e}")
    db.commit()




def get_expense_stats(user_id, start, end):
    with connect() as db:
        cs = db.cursor()
        end_date_time = f"{end} 23:59:59"
        cs.execute("""
            SELECT category , SUM(amount) as total_expense, date(date) as transaction_date
            FROM transactions
            WHERE  user_id = ? and date between ? and ? and type = 'expense'
            GROUP BY category , transaction_date
            ORDER BY transaction_date
        """, (user_id, start, end_date_time))
        return cs.fetchall()

# чтобы получить те напоминалки время которых совпадает с нынешним временем
def get_reminders_for_now():
    now = datetime.now()
    current_date = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M')

    with connect() as db:
        cs = db.cursor()
        cs.execute("""
            SELECT user_id, message , isEveryDay
            FROM reminders 
            WHERE (date = ? AND time = ?) OR (isEveryDay = 1 AND time = ?)
        """, (current_date, current_time, current_time))
        return cs.fetchall()


def delete_user(user_id):
    with connect() as db:
        cs = db.cursor()
        cs.execute(" DELETE FROM users WHERE id = ? ", (user_id,))
        db.commit()


# тут такая логика что если у нас не имеется статуса isEveryDay то мы удаляем это напоминание с таблицы базы данных
# чтобы не хранить лишние данные
def delete_sent_reminders(user_id, date, time):
    with connect() as db:
        cs = db.cursor()
        cs.execute("""
            DELETE FROM reminders 
            WHERE user_id = ? AND date = ? AND time = ? AND isEveryDay = 0
        """, (user_id, date, time))
        db.commit()
