import os
import psycopg2
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import jwt
from datetime import datetime, timedelta, timezone
import bcrypt
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Initialize Flask application
server = Flask(__name__)
CORS(server)

# Prometheus metrics
login_count = Counter('login_requests_total', 'Total number of login requests')
auth_errors = Counter('auth_errors_total', 'Total number of authentication errors')
db_operation_duration = Histogram('db_operation_duration_seconds', 'Time spent on database operations')
jwt_operation_duration = Histogram('jwt_operation_duration_seconds', 'Time spent on JWT operations')

# Add metrics endpoint
@server.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# Load configuration from environment variables
db_host = os.environ["DATABASE_HOST"]
db_name = os.environ["DATABASE_NAME"]
db_user = os.environ["DATABASE_USER"]
db_password = os.environ["DATABASE_PASSWORD"]
auth_table = os.environ["AUTH_TABLE"]
jwt_secret = os.environ["JWT_SECRET"]

print("Initializing Auth Service...")
print(f"Database Host: {db_host}")
print(f"Database Name: {db_name}")
print(f"Auth Table: {auth_table}")

def get_db_connection():
    conn = psycopg2.connect(host=db_host,
                           database=db_name,
                           user=db_user,
                           password=db_password,
                           port=5432)
    return conn

def update_password_hash(conn, email, password):
    try:
        with db_operation_duration.time():
            cur = conn.cursor()
            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            query = f"UPDATE {auth_table} SET password = %s WHERE email = %s"
            cur.execute(query, (hashed_password.decode(), email))
            conn.commit()
        return True
    except Exception as e:
        print(f"Error updating password hash: {e}")
        auth_errors.inc()
        return False

@server.route('/login', methods=['POST'])
def login():
    login_count.inc()
    auth_table_name = auth_table
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        auth_errors.inc()
        return 'Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}

    conn = get_db_connection()
    cur = conn.cursor()
    with db_operation_duration.time():
        query = f"SELECT email, password FROM {auth_table_name} WHERE email = %s"
        cur.execute(query, (auth.username,))
        user_row = cur.fetchone()
    
    if user_row is None:
        # User not found
        auth_errors.inc()
        return 'Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}
    else:
        email = user_row[0]
        stored_password = user_row[1]

        # If password is stored as plain text, update it to hash
        if not stored_password.startswith('$2b$'):
            print(f"Updating plain text password for {email} to hash")
            if update_password_hash(conn, email, auth.password):
                stored_password = bcrypt.hashpw(auth.password.encode(), bcrypt.gensalt()).decode()
            else:
                auth_errors.inc()
                return 'Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}

        # Verify password
        if not bcrypt.checkpw(auth.password.encode(), stored_password.encode()):
            auth_errors.inc()
            return 'Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}

        with jwt_operation_duration.time():
            token = CreateJWT(auth.username, jwt_secret)
        print(f"Generated token for {auth.username}: {token}")
        # Return the token as plain text with proper content type
        response = Response(token, content_type='text/plain')
        return response

def CreateJWT(username, secret):
    token = jwt.encode(
        {
            "username": username,
            "exp": datetime.now(timezone.utc) + timedelta(days=1),
            "iat": datetime.now(timezone.utc),
            "authenticated": True,
        },
        secret,
        algorithm="HS256",
    )
    # Ensure the token is a string (some versions of PyJWT return bytes)
    if isinstance(token, bytes):
        return token.decode('utf-8')
    return token

@server.route('/validate', methods=['POST'])
def validate():
    if 'Authorization' not in request.headers:
        auth_errors.inc()
        return jsonify({'error': 'No Authorization header'}), 401

    auth_header = request.headers['Authorization']
    if not auth_header.startswith('Bearer '):
        auth_errors.inc()
        return jsonify({'error': 'Invalid Authorization header format'}), 401

    try:
        with jwt_operation_duration.time():
            encoded_jwt = auth_header.split(' ')[1]
            decoded_jwt = jwt.decode(encoded_jwt, jwt_secret, algorithms=["HS256"])
        return jsonify(decoded_jwt), 200
    except jwt.ExpiredSignatureError:
        auth_errors.inc()
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError as e:
        auth_errors.inc()
        return jsonify({'error': f'Invalid token: {str(e)}'}), 401
    except Exception as e:
        auth_errors.inc()
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5000)
