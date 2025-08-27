from flask import Flask, request, jsonify
import os, pymysql, time

app = Flask(__name__)

def connect_db(retries: int = 30, delay: float = 2.0):
    host = os.environ.get("DB_HOST", "mysql-db")
    user = os.environ.get("DB_USER", "root")
    password = os.environ.get("DB_PASSWORD", "NIMA123")
    database = os.environ.get("DB_NAME", "flaskdb")
    last_err = None
    for _ in range(retries):
        try:
            conn = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                autocommit=True,
                cursorclass=pymysql.cursors.DictCursor,
            )
            return conn
        except Exception as e:
            last_err = e
            time.sleep(delay)
    raise last_err

db = connect_db()

def init_db():
    with db.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            );
            """
        )

init_db()

@app.route('/')
def home():
    return "Flask App Connected to MySQL!"

@app.route('/add', methods=['POST'])
def add():
    data = request.json or {}
    name = data.get('name')
    if not name:
        return jsonify({"error": "'name' is required"}), 400
    with db.cursor() as cursor:
        cursor.execute("INSERT INTO users (name) VALUES (%s)", (name,))
    return jsonify({"message": "User Added!"}), 201

@app.route('/health')
def health():
    return "ok", 200

@app.route('/users', methods=['GET'])
def users():
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        result = cursor.fetchall()
    return jsonify(result)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
