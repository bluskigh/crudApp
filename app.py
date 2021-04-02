from flask import Flask, render_template, request, redirect, jsonify, abort, url_for
from flask_migrate import Migrate 
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://temp:1234@localhost:5432/crudApp'
db = SQLAlchemy(app)

migrate = Migrate(app, db)

class List(db.Model):
  __tablename__ = 'lists'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  children = db.relation('Todo', backref='list', lazy=True)

class Todo(db.Model):
  __tablename__ = 'todos'
  id = db.Column(db.Integer, primary_key=True)
  description = db.Column(db.String(), nullable=False)
  completed= db.Column(db.Boolean, nullable=False, default=False)
  list_id = db.Column(db.Integer, db.ForeignKey('lists.id'))

  def __repr__(self):
    return f'<Todo {self.id}, {self.description}>'

# no need to use db.create_all() to sync the models, instead we want the migration version to store what we craete and modify
# db.create_all()

@app.route('/')
def index():
  return redirect(url_for('get_list_todos', list_id=1))

@app.route('/lists/<list_id>')
def get_list_todos(list_id):
  lists = db.session.query(List).all()
  return render_template('index.html', data=db.session.query(Todo).filter_by(list_id=list_id).order_by('id').all(), id=list_id, lists=lists, name=db.session.query(List).get(list_id).name)

@app.route('/todos/create', methods=['POST'])
def create():
  # get_json fetches the body 
  desc = request.get_json()['desc']
  id = request.get_json()['id']
  error = False
  todo = {}  
  try:
    if desc:
      # in the transient stage
      temp = Todo(description=desc, list_id=id)
      # in the pending stage
      db.session.add(temp)
      # flushed, and committed to the database
      db.session.commit()
      todo['id']  = temp.id 
      todo['desc']  = temp.description
  except Exception as e:
    print(e)
    db.session.rollback();
    error = True
  finally:
    db.session.close()
  if not error:
    return jsonify({
      'result': todo
    })
  else:
    abort(400)

@app.route('/todos/check', methods=['POST'])
def check():
  try:
    todo_id = request.get_json()['id']
    todo = Todo.query.get(int(todo_id))
    if todo:
      completed = None
      todo.completed = not todo.completed
      completed = todo.completed
      db.session.commit()
      return jsonify({'result': True, 'completed': completed})
    else:
      abort(404)
  except Exception as e:
    print(e)
    db.session.rollback()
  finally :
    db.session.close()

@app.route('/todos/<todo_id>/remove')
def remove(todo_id): 
  error = False
  try:
    todo = db.session.query(Todo).get(todo_id)
    db.session.delete(todo)
    db.session.commit()
  except Exception as e:
    print(e)
    error = True
    db.session.rollback()
  finally:
    db.session.close()

  if not error:
    return jsonify({'result': True})
  else:
    abort(500)

@app.route('/todos', methods=['GET'])
def todos():
  result = db.session.query(Todo).all()
  return jsonify(result)

if __name__ == '__main__':
  app.run()
