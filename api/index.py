from app import app as flask_app, init_db

init_db()
app = flask_app
