from tempfile import mkdtemp
import os
# enabling debug mode
DEBUG=True
# database uri location
SQLALCHEMY_DATABASE_URI = 'postgresql://temp:1234@localhost:5432/simpleStore'
# secret key
secret_key = os.urandom(24)
# specifies which type of session interface to use
SESSION_TYPE = 'filesystem'
SESSION_FILE_DIR = mkdtemp()
SESSSION_PERMANENT = True

# removes deprecation error on "flask run" or python3 app.p
SQLALCHEMY_TRACK_MODIFICATIONS=False
