import sqlite3

def check_stripe_connect_id():
    conn = sqlite3.connect('zenpay.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, email FROM users WHERE email = 'test@example.com'")
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        print(f"User ID: {user_data[0]}, Email: {user_data[1]}")
    else:
        print("Test user not found.")

if __name__ == '__main__':
    check_stripe_connect_id()