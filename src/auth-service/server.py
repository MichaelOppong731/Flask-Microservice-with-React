import os
import psycopg2
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import jwt
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask application
server = Flask(__name__)
CORS(server)

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


@server.route('/login', methods=['POST'])
def login():
    auth_table_name = auth_table
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return 'Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}

    conn = get_db_connection()
    cur = conn.cursor()
    query = f"SELECT email, password FROM {auth_table_name} WHERE email = %s"
    cur.execute(query, (auth.username,))
    user_row = cur.fetchone()
    
    if user_row is None:
        # User not found
        return 'Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}
    else:
        email = user_row[0]
        password = user_row[1]

        if auth.username != email or auth.password != password:
            return 'Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'}
        else:
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
        return jsonify({'error': 'No Authorization header'}), 401

    auth_header = request.headers['Authorization']
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Invalid Authorization header format'}), 401

    try:
        encoded_jwt = auth_header.split(' ')[1]
        decoded_jwt = jwt.decode(encoded_jwt, secret, algorithms=["HS256"])
        return jsonify(decoded_jwt), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError as e:
        return jsonify({'error': f'Invalid token: {str(e)}'}), 401
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5000)
