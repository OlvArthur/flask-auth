from flask import Flask, request, jsonify
from models.user import User
from database import db
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:admin123@127.0.0.1:3306/flask-auth'


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

  missing_credentials = not username or not password

  if missing_credentials:
    return jsonify({'message': 'Missing credentials' }), 400
  
  user = User.query.filter_by(username=username).first()

  user_not_found = not user
  user_password = getattr(user, "password", None)
  wrong_password = not bcrypt.checkpw(str.encode(password), str.encode(user_password))

  if user_not_found or wrong_password:
    return jsonify({'message': 'Invalid credentials' }), 400
  
  login_user(user)

  return jsonify({'message': 'Successfull login'})


@app.route('/logout', methods=['GET'])
@login_required
def logout():
  logout_user()
  return jsonify({
    'message': 'Successfully loged out'
  })

@app.route('/users', methods=['POST'])
def create_user():
  data = request.get_json()

  username = data.get('username')
  password = data.get('password')
  role = data.get('role')


  missing_credentials = not username or not password

  if missing_credentials:
    return jsonify({'message': 'Missing credentials' }), 400
  
  hashed_password = bcrypt.hashpw(str.encode(password), bcrypt.gensalt())
  new_user = User(username=username, password=hashed_password, role=role or 'user')

  db.session.add(new_user)
  db.session.commit()

  return jsonify({'message': 'User successfully created'})

@app.route('/users', methods=['GET'])
@login_required
def get_user():
  users: list[User] = User.query.all()
  
  users = [user.to_dict() for user in users]

  return jsonify({
    'users': users,
  })

@app.route('/users/<int:id>',methods=['GET'])
@login_required
def read_users(id):
  found_user: User | None = User.query.get(id)

  if not found_user:
    return jsonify({'message': 'User not found'})

  
  return { 'user': found_user.to_dict() }


@app.route('/users/<int:id>',methods=['PUT'])
@login_required
def update_user(id):
  data = request.json
  new_role = data.get('role')
  new_password = data.get('password')

  found_user: User | None = User.query.get(id)

  if not found_user:
    return jsonify({'message': f'User {id} not found'}), 404

  if current_user.role != 'admin':
    if new_role:
      return jsonify({'message': 'You are not allowed to change a user role'}), 403
    
    if new_password and current_user.id != id:
      return jsonify({'message': 'You are not allowed to change other user`s passwords'}), 403

  found_user.password = new_password or found_user.password

  number_admins = User.query.filter_by(role='admin').limit(2).count()

  if number_admins == 1 and new_role and current_user.id == id:
    return jsonify({'message': 'You can not change your role as you are the only admin'}), 403

  found_user.role = new_role or found_user.role


  db.session.commit()

  return jsonify({'message': f'User {id} successfully updated'})


@app.route('/users/<int:id>', methods=['DELETE'])
@login_required
def delete_user_by_id(id):
  found_user: User | None = User.query.get(id)

  if current_user.role != 'admin':
    return jsonify({'message': 'You are not allowed to delete a user'}), 403

  if id == current_user.id:
    return jsonify({'message': 'You can not delete yourself'}), 403

  if not found_user:
    return jsonify({'message': 'User not found'}), 404
  
  db.session.delete(found_user)
  db.session.commit()

  return jsonify({'message':f'User {id} successfully deleted'})


if __name__=='__main__':
  app.run(debug=True)