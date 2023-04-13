import datetime

class CheckIn():
    def __init__(self, number, text):
        self.number = float(number)
        self.text = text
        self.replies = []
    
    def reply(self,user,text):
        self.replies.append((user,text))

    def readReplies(self):
        out = ""
        for user,reply in self.replies: 
            out += f"\n{user}: {reply}"
        return out

    def readCheckIn(self):
        return f"{repr(self)} Check-in: {self.number}\n{self.text}"

    def readThread(self):
        return f"{self.readCheckIn()}\n"+self.readReplies()