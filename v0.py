import sys, getopt
import requests
import pickle
import datetime
from CheckIn import CheckIn

def readFile(filename):
    f = open(filename+"-chat","rb")
    out = pickle.load(f)
    f.close()
    return out

def saveFile(obj,filename):
    f = open(filename+"-chat","wb")
    out = pickle.dump(obj,f)
    f.close()
    return out

def botReply(checkIns,index,user,key):
    messages = [{"role":"system","content":"You are 'Nin,' an AI user of a daily mental check in app that replies to user's check ins consisting of a 1-10 score for the day and some text."}]
    if index > 0:
        checkInText = ""
        for i in range(index):
            checkInText += checkIns[i].readCheckIn()+"\n"
        messages.append({"role":"user","content":f"Here are some of the user {user}'s past check ins:"})
        messages.append({"role":"user","content":checkInText})
    messages.append({"role":"user","content":f"Here is user {user}'s current check in thread:"})
    messages.append({"role":"user","content":checkIns[index].readThread()})
    messages.append({"role":"user","content":f"Your next message will be posted verbatim as a new comment to this thread by 'Nin'"})
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}"
            }
    json = {"model":"gpt-3.5-turbo","messages":messages,"temperature":0.75,"max_tokens":250}
    response = requests.post(url, json=json, headers=headers).json()["choices"][0]["message"]["content"]
    if response.startswith("Nin: "):
        response = response[5:]
    checkIns[index].reply("Nin",response)

def usage():
    print("Usage: python v0.py -u <user> -k <OpenAI key>")

def getInput(checkIns):
    print(f"Check Ins: {str(checkIns)}")
    userIn = input(f"Date (M/D/YYYY): ")
    return userIn

def main(argv: list[str]):
    try:
        opts, args = getopt.getopt(argv,"u:k:",["user=","key="])
        opts = dict(opts)
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        return
    try:
        key = opts.get("-k",opts.get("--key"))
        user = opts.get("-u",opts.get("--user"))
        assert(key)
        assert(user)
    except AssertionError:
        usage()
        return
    try:
        checkIns = readFile(user)
    except FileNotFoundError:
        checkIns = []
    
    dates = [checkIn.date for checkIn in checkIns]
    userIn = getInput(checkIns)
    while userIn != "":
        m,d,y = userIn.split("/")
        date = datetime.date(int(y),int(m),int(d))
        if date in dates:
            ind = dates.index(date)
            checkIn = checkIns[ind]
            print(checkIn.readThread())
        else:
            score = input("Check In score (0-10): ")
            checkIn = input("Check In: ")
            checkIn = CheckIn(date,score,checkIn)
            checkIns.append(checkIn)
            ind = len(checkIns)-1
            botReply(checkIns,ind,user,key)
            saveFile(checkIns,user)
            print(checkIn.readReplies())
        reply = input("Reply?: ")
        while reply != "":
            checkIn.reply(user,reply)
            botReply(checkIns,ind,user,key)
            print(checkIn.readReplies())
            saveFile(checkIns,user)
            reply = input("Reply?: ")
        checkIns.sort(key = lambda x:x.date)
        dates = [checkIn.date for checkIn in checkIns]
        userIn = getInput(checkIns)

if __name__ == "__main__":
    out = main(sys.argv[1:])