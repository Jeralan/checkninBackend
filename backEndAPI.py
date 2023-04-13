from CheckIn import CheckIn
from requestConstants import systemMessage
from flask import Flask, request, jsonify
import hashlib
from base64 import b64encode,b64decode
from cryptography.fernet import Fernet
from flask_sqlalchemy import SQLAlchemy
import os
import pickle
import requests

app = Flask(__name__)
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql://{os.environ['RDS_USERNAME']}:{os.environ['RDS_PASSWORD']}@{os.environ['RDS_HOSTNAME']}:{os.environ['RDS_PORT']}/{os.environ['RDS_DB_NAME']}"
#app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///convos.db"
db.init_app(app)

class ThreadsDB(db.Model):
    username = db.Column(db.String(128), primary_key=True, unique=True)
    #passHash, salt1, salt2, threads are in b64encoded form
    passHash = db.Column(db.String(128))
    salt1 = db.Column(db.String(128))
    salt2 = db.Column(db.String(128))
    threads = db.Column(db.String(1280))

with app.app_context():
    db.create_all()

def addUserMessage(messages,content):
    messages.append({"role":"user",
                         "content":content})
    return messages

def getResponse(username, threads, responseDate):
    key = os.environ['OPENAI_API_KEY']
    messages = [{"role":"system","content":systemMessage}]
    for date in threads:
        thread = threads[date]
        if date != responseDate:
            messages = addUserMessage(messages,
                                    f"For context, here is {username}'s other check in from {date}")
            messages = addUserMessage(messages,
                                    f"Mood: {thread.number}\n{thread.text}")
    
    messages = addUserMessage(messages, f"Now here is {username}'s {date} check in thread. Your next response will be added verbatim as a new reply from 'Nin'")
    thread = threads[responseDate]
    content = f"Mood: {thread.number}\n{thread.text}"
    if len(thread.replies) > 0:
        content += "\nReplies:\n"
        content += "\n".join([f"{user}: {reply}" for (user,reply) in thread.replies])
    messages = addUserMessage(messages,content)
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}"
            }
    json = {"model":"gpt-3.5-turbo","messages":messages,"temperature":0.75,"max_tokens":500}
    response = requests.post(url, json=json, headers=headers).json()["choices"][0]["message"]["content"]
    if response.startswih("Nin: "):
        response = response[5:]
    thread.replies.append(("Nin",response))

def getThreads(username,password):
    user = db.session.execute(db.select(ThreadsDB).where(ThreadsDB.username == username)).scalar()
    salt1 = b64decode(user.salt1)
    passHash = b64encode(hashlib.pbkdf2_hmac("sha512",bytes(password,"utf-8"),salt1,500000))
    assert(passHash == user.passHash)
    salt2 = b64decode(user.salt2)
    key = hashlib.pbkdf2_hmac("sha512",bytes(password,"utf-8"),salt2,500000)
    fernet = Fernet(b64encode(key[-32:]))
    pickledThreads = fernet.decrypt(b64decode(user.threads))
    return pickle.loads(pickledThreads),fernet,user

@app.route("/",methods=["GET"])
def alive():
    return "API ALIVE"

@app.route("/new",methods=["POST"])
def newThread():
    content = request.get_json()
    username = content["username"]
    password = content["password"]
    date = content["date"]
    mood = content["mood"]
    text = content["text"]
    newThread = CheckIn(mood,text)
    threads,fernet,userEntry = getThreads(username,password)
    threads[date] = newThread
    getResponse(username, threads, date)
    pickledThreads = pickle.dumps(threads)
    userEntry.threads = b64encode(fernet.encrypt(pickledThreads))
    db.session.commit()
    return "Success"

@app.route("/reply",methods=["POST"])
def newReply():
    content = request.get_json()
    username = content["username"]
    password = content["password"]
    date = content["date"]
    text = content["text"]
    threads,fernet,userEntry = getThreads(username,password)
    threads[date].replies.append((username,text))
    getResponse(username, threads, date)
    pickledThreads = pickle.dumps(threads)
    userEntry.threads = b64encode(fernet.encrypt(pickledThreads))
    db.session.commit()
    return "Success"

@app.route("/read",methods=["POST"])
def readThread():
    content = request.get_json()
    username = content["username"]
    password = content["password"]
    date = content["date"]
    threads,fernet,userEntry = getThreads(username,password)
    thread = threads[date]
    return jsonify({"number":thread.number,
                    "text":thread.text,
                    "replies":thread.replies})

@app.route("/get",methods=["POST"])
def threadRequest():
    content = request.get_json()
    username = content["username"]
    password = content["password"]
    threads,_,_ = getThreads(username,password)
    dates = list(threads.keys())
    return jsonify({"threads":dates})

@app.route("/enroll",methods=["POST"])
def enrollUser():
    content = request.get_json()
    username = content["username"]
    password = content["password"]
    user = db.session.execute(db.select(ThreadsDB).where(ThreadsDB.username == username)).scalar()
    if user != None: return
    user = ThreadsDB()
    user.username = username
    salt1,salt2 = os.urandom(32),os.urandom(32)
    user.salt1 = b64encode(salt1)
    user.salt2 = b64encode(salt2)
    user.passHash = b64encode(hashlib.pbkdf2_hmac("sha512",bytes(password,"utf-8"),salt1,500000))
    key = hashlib.pbkdf2_hmac("sha512",bytes(password,"utf-8"),salt2,500000)
    fernet = Fernet(b64encode(key[-32:]))
    user.threads = b64encode(fernet.encrypt(pickle.dumps(dict())))
    db.session.add(user)
    db.session.commit()
    return "Success"

if __name__ == "__main__":
    from waitress import serve
    serve(app)