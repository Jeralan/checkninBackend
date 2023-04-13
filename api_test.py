import requests

uri = "http://localhost:8080"

def enroll(username, password):
    url = uri+"/enroll"
    json = {"username":username,"password":password}
    response = requests.post(url, json=json)
    return response

def getThreads(username, password):
    url = uri+"/get"
    json = {"username":username,"password":password}
    response = requests.post(url, json=json).json()
    print(response["threads"])
    return response

def readThread(username, password, date):
    url = uri+"/read"
    json = {"username":username,"password":password,"date":date}
    response = requests.post(url, json=json).json()
    print("Mood:",response["number"])
    print(response["text"])
    for user,reply in response["replies"]:
        print(f"{user}:",reply)
    return response

def replyThread(username, password, date, text):
    url = uri+"/reply"
    json = {"username":username,"password":password,"date":date,"text":text}
    response = requests.post(url, json=json)
    return response

def newThread(username, password, date, mood, text):
    url = uri+"/new"
    json = {"username":username,"password":password,
            "date":date,"mood":mood,"text":text}
    response = requests.post(url, json=json)
    return response