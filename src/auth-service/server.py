import jwt, datetime, os
import psycopg2
from flask import Flask, request, jsonify

server = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(host=os.getenv('DATABASE_HOST', 'capstone.c18g4q48md9n.eu-west-1.rds.amazonaws.com'),
                            database=os.getenv('DATABASE_NAME', 'auth'),
                            user=os.getenv('DATABASE_USER', 'root'),
                            password=os.getenv('DATABASE_PASSWORD', 'rootpassword'),
                            port=5432)
    return conn


@server.route('/login', methods=['POST'])
def login():
    auth_table_name = os.getenv('AUTH_TABLE', 'auth_user')
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
            return CreateJWT(auth.username, os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-2024!@#$%^&*()'), True)

def CreateJWT(username, secret, authz):
    return jwt.encode(
        {
            "username": username,
            "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1),
            "iat": datetime.datetime.now(tz=datetime.timezone.utc),
            "admin": authz,
        },
        secret,
        algorithm="HS256",
    )

@server.route('/validate', methods=['POST'])
def validate():
    if 'Authorization' not in request.headers:
        return jsonify({'error': 'No Authorization header'}), 401

    auth_header = request.headers['Authorization']
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Invalid Authorization header format'}), 401

    try:
        encoded_jwt = auth_header.split(' ')[1]
        decoded_jwt = jwt.decode(encoded_jwt, os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-2024!@#$%^&*()'), algorithms=["HS256"])
        return jsonify(decoded_jwt), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError as e:
        return jsonify({'error': f'Invalid token: {str(e)}'}), 401
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5000)
