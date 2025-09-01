from flask import Flask, request, jsonify
import os, pymysql, time

app = Flask(__name__)

def connect_db(retries: int = 30, delay: float = 2.0):
    """Create a new DB connection with retries. Uses only environment variables.
    Avoids hardcoded secrets and import-time connections.
    """
    host = os.environ.get("DB_HOST", "mysql-db")
    user = os.environ.get("DB_USER", "root")
    # Do not hardcode real passwords; expect via environment
    password = os.environ.get("DB_PASSWORD", "")
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

def init_db():
    # Initialize schema if DB is reachable; otherwise skip (app can still start)
    try:
        with connect_db() as db:
            with db.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL
                    );
                    """
                )
    except Exception:
        # In CI or when DB is not ready, we don't block app import
        pass

@app.route('/')
def home():
    return "Flask App Connected to MySQL!"

@app.route('/add', methods=['POST'])
def add():
    data = request.json or {}
    name = data.get('name')
    if not name:
        return jsonify({"error": "'name' is required"}), 400
    with connect_db() as db:
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO users (name) VALUES (%s)", (name,))
    return jsonify({"message": "User Added!"}), 201

@app.route('/health')
def health():
    return "ok", 200

@app.route('/users', methods=['GET'])
def users():
    with connect_db() as db:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            result = cursor.fetchall()
    return jsonify(result)

@app.before_first_request
def _init_on_first_request():
    init_db()

if __name__ == '__main__':
    # For local dev only; in containers we use gunicorn
    app.run(host="0.0.0.0", port=5000)
