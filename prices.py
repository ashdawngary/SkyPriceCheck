import json
import urllib.request
import os
import subprocess

#Skyblock Price Table
# Features autocorrect, string eval, full sanitizer

# Three methods of loading files for prices.

def loadJsonFileRemote(url):
    with urllib.request.urlopen(url) as urlHandle:
        return json.loads(urlHandle.read().decode())
def loadJsonViaGithub(user='ashdawngary',repo = 'SkyPriceCheck',file = 'data.json',branch='master'):
    return loadJsonFileRemote('https://raw.githubusercontent.com/%s/%s/%s/%s'%(user,repo,branch,file))
def loadJsonViaLocal(fname,absolute=False):
    prefix = "" if absolute else os.getcwd()+"/"
    with open(prefix+fname,"r") as fileHandle:
        data = fileHandle.read()
    return json.loads(data)

def metric(s1, s2):
    # levenshtein distance metric using dp
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

def getSanitizedValue(some_value):
    some_value = some_value.lstrip().rstrip()
    common_signs = ['k','m','b']
    sign = None
    if some_value[-1] in common_signs:
        sign = some_value[-1]
        some_value = some_value[:-1]
    if "$" in some_value and sign == None:
        sign = 'c'
        some_value = some_value.replace('$','')

    if ('.' in some_value):
        return (float(some_value),sign)
    else:
        try:
            return (int(some_value),sign)
        except:
            print("Failed to cast to number: %s"%(some_value))
            return (0,None)

def augment(numerical,signature):
    return {'c':1,'k':10**3,'m':10**6,'b':10**9,None:1}[signature] * numerical


class PricesTable:
    def __init__(self, jsonFormattedData,localDest = 'data.json'):
        self.original_data = jsonFormattedData
        self.data = {}
        self.dest = localDest
        for data in self.original_data:
            self.data[data['name']] = data
        self.names = set(map(lambda x: x['name'],self.original_data))
        self.loggedChanges = []
    def guestimate(self,name):
        if name in self.names:
           return [name]
        else:
            return min([ [potname,metric(name,potname)] for potname in self.names ],key = lambda x: x[1])

    def query(self,name):
        name = name.lstrip().rstrip().lower().replace(' ','_')
        revised = self.guestimate(name)[0]
        if revised != name:
            print("Autocorrected to: %s"%(revised))
        return self.data[revised]

    def modify(self,name,field,value):
        self.data[name][field] = value
        if field == 'name':
            temp = self.data.pop(name)
            self.data[value] = temp
            self.names.remove(name)
            self.names.add(value)
        humane_readable = {
            'hi': 'upper bound price',
            'low': 'lower bound price',
            'name': 'formal name'
        }
        self.loggedChanges.append("Changed the %s of %s to %s"%(humane_readable[field], name, value))
        with open(self.dest,"w") as outHandle:
            outHandle.write(json.dumps(list(self.data.values())))
            outHandle.close()

    def publish(self):
        # time to do some subprocess magic
        subprocess.call("git add -A".split(" "))
        subprocess.call(["git", "commit", "-m Automated Refresh" " \nChanges:\n%s"%('\n'.join(self.loggedChanges))])
        self.loggedChanges = []
        subprocess.call(["git","push","origin","master"])

    def estimate_literalOrItem(self,eStr):
        alpha = 0
        numeric = 0
        for i in eStr:
            if '0' <= i and i <= '9':
                numeric += 1
            elif 'a' <= i and i <= 'z':
                alpha += 1
        if numeric > alpha:
            # treat is as a number
            data =  augment(*getSanitizedValue(eStr))
            return [data,data]
        else:
            value = self.query(eStr)
            return [value["low"],value["hi"]]
    def eval(self,gStr,incog = True):
        gStr = gStr.lower()

        current_price = [0,0]
        data = list(gStr)
        currentLevel = 0
        parsed_symbols = [""]
        while len(data) != 0:
            nextChar = data.pop(0)
            if nextChar == '(':
                currentLevel += 1
                epic = []
                while len(data) != 0 and currentLevel > 0:
                    nexChar = data.pop(0)
                    if nexChar == ')':
                        currentLevel -= 1
                    elif nexChar == '(':
                        currentLevel += 1
                    if currentLevel > 0:
                        epic.append(nexChar)

                value = self.eval(''.join(epic))
                if len(parsed_symbols[-1].lstrip()) != 0:
                    #print("did not overwrite answer")
                    parsed_symbols[-1] = self.estimate_literalOrItem(parsed_symbols[-1])
                    parsed_symbols.append(value)
                else:
                    #print("overwrote answer")
                    parsed_symbols[-1] = value
                    #print(parsed_symbols)
                parsed_symbols.append("")
            elif nextChar in ['*','/','+','-']:
                if len(parsed_symbols[-1].lstrip()) != 0:
                    parsed_symbols[-1] = self.estimate_literalOrItem(parsed_symbols[-1])
                    parsed_symbols.append(nextChar)
                else:
                    parsed_symbols[-1] = nextChar
                parsed_symbols.append("")
            else:
                parsed_symbols[-1] += nextChar

        if type(parsed_symbols[-1]) == str:
            if len(parsed_symbols[-1]) > 0:
                parsed_symbols[-1] = self.estimate_literalOrItem(parsed_symbols[-1])
            else:
                parsed_symbols.pop()
        current_price = parsed_symbols.pop(0)
        currentop = ""
        functions = {
            '*': lambda x,y: (x[0]*y[0],x[1]*y[1]),
            '+': lambda x,y: (x[0]+y[0],x[1]+y[1]),
            '-': lambda x,y: (x[0]-y[0],x[1]-y[1]),
            '/': lambda x,y: (x[0]/y[0],x[1]/y[1])
        }
        for i in parsed_symbols:
            if i in ['*','/','+','-']:
                currentop = i
            else:
                #print(current_price,i)
                current_price = functions[currentop](current_price,i)
        if not incog:
            print("answer is between %s and %s"%(current_price[0],current_price[1]))
        return current_price

q = PricesTable(loadJsonViaGithub())
