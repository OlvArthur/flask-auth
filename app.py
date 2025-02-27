from flask import Flask, request, jsonify
from models.user import User
from database import db
from flask_login import LoginManager, login_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'


login_manager = LoginManager()
db.init_app(app)
login_manager.init_app(app)

login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(user_id)

@app.route('/login', methods=['POST'])
def login():
  data = request.get_json()

  username = data.get('username')
  password = data.get('password')

  if not username or not password:
    return jsonify({'message': 'Missing credentials' }), 400
  
  user = User.query.filter_by(username=username).first()

  if not user or user.password != password:
    return jsonify({'message': 'Invalid credentials' }), 400
  
  login_user(user)

  print(current_user.is_authenticated)

  return jsonify({'message': 'Successfull login'})

@app.route('/hello-world', methods=['GET'])
def hello_world():
  return 'Hello, World'

if __name__=='__main__':
  app.run(debug=True)