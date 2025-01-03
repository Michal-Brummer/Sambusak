from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

# Initialize Flask, database, and Socket.IO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Models for users and messages
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# Track connected users
connected_users = {}

# Register a new user
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"})

# Login an existing user
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return jsonify({"message": "Login successful"})
    return jsonify({"error": "Invalid credentials"}), 401

# Handle WebSocket connections
@socketio.on('connect')
def handle_connect():
    emit('message', {'sender': 'System', 'message': 'Welcome to the chat!'}, room=request.sid)

@socketio.on('login')
def handle_login(data):
    username = data.get('username')
    if username:
        connected_users[request.sid] = username
        emit('message', {'sender': 'System', 'message': f"{username} joined the chat!"}, broadcast=True)
        emit('connected_users', list(connected_users.values()), broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    username = connected_users.pop(request.sid, None)
    if username:
        emit('message', {'sender': 'System', 'message': f"{username} left the chat!"}, broadcast=True)
        emit('connected_users', list(connected_users.values()), broadcast=True)

@socketio.on('message')
def handle_message(data):
    sender = data.get('sender')
    message = data.get('message')

    if not sender or not message:
        emit('message', {'sender': 'System', 'message': 'Invalid message format'}, room=request.sid)
        return

    new_message = Message(sender=sender, message=message)
    db.session.add(new_message)
    db.session.commit()

    emit('message', {
        'sender': sender,
        'message': message,
        'timestamp': new_message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    }, broadcast=True)

# Handle private messages
@socketio.on('private_message')
def handle_private_message(data):
    sender = connected_users.get(request.sid)
    recipient_username = data.get('recipient')
    message = data.get('message')

    if not sender or not recipient_username or not message:
        emit('message', {'sender': 'System', 'message': 'Invalid private message format'}, room=request.sid)
        return

    recipient_sid = None
    for sid, username in connected_users.items():
        if username == recipient_username:
            recipient_sid = sid
            break

    if recipient_sid:
        # Add timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Send message to the recipient
        emit('private_message', {
            'sender': sender,
            'message': message,
            'timestamp': timestamp  # Include timestamp
        }, room=recipient_sid)

        # Acknowledge the sender
        emit('private_message', {
            'sender': sender,
            'message': f"(To {recipient_username}) {message}",
            'timestamp': timestamp  # Include timestamp
        }, room=request.sid)
    else:
        # Notify sender if recipient is not connected
        emit('message', {'sender': 'System', 'message': f"User {recipient_username} is not connected."}, room=request.sid)


# Run the server
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
