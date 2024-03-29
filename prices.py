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
    def __init__(self, jsonFormattedData,jsonFormattedAliases,localDest = 'data.json',localAlias = 'alias.json'):
        self.original_data = jsonFormattedData
        self.original_alias = jsonFormattedAliases

        self.data = {}
        self.alias = {}
        self.dest = localDest
        self.aliasDest = localAlias
        for data in self.original_data:
            self.data[data['name']] = data
        for data in self.original_alias:
            self.alias[data["src"]]=  data
        self.names = set(map(lambda x: x['name'],self.original_data))
        self.aliasSet = set(map(lambda x: x['src'],self.original_alias))
        self.loggedChanges = []
    def traceAliasTree(self,currentAlias):
        # traces an alias chain until it reaches a valid identifier.
        while not currentAlias in self.names:
            currentAlias = self.alias[currentAlias]['dest']
        return currentAlias

    def guestimate(self,name):
        if name in self.names:
           return [name,0]
        else:
            name_answer = min([ [potname,metric(name,potname)] for potname in self.names ],key = lambda x: x[1])
            aliased_answer = min([ [potname,metric(name,potname)] for potname in self.aliasSet ],key = lambda x: x[1])
            print(name_answer,aliased_answer)
            if name_answer[1] < aliased_answer[1]:
                return name_answer
            else:
                return [self.traceAliasTree(aliased_answer[0]),aliased_answer[1]]
    def addAlias(self,alias_name,target):
        # target can be an alias too, it will point to the tree.
        if (not target in self.aliasSet) and (not target in self.names):
            print("error, the destination `%s` is not a valid alias or a valid name."%(self.target))
            return -1
        self.aliasSet.add(alias_name)
        self.alias[alias_name] = {
            'src': alias_name,
            'dest' : target
        }
        self.loggedChanges.append("Aliased %s to %s"%(alias_name,target))
        with open(self.aliasDest,"w") as outHandle:
            outHandle.write(json.dumps(list(self.alias.values())))
            outHandle.close()
    def query(self,name,mistakes_tolerance = 6):
        name = name.lstrip().rstrip().lower().replace(' ','_')
        revised,distance = self.guestimate(name)
	
        if revised != name:
            print("Autocorrected to: %s"%(revised))
        if distance > mistakes_tolerance:
            return {'name':None,'low':None,'hi':None, 'suggest': revised}
        else:
            return self.data[revised]
    def removeItem(self,name,root=True):
        # reomves item and all all aliases
        if name in self.names:
            # its a name
            collateral = []
            for i in self.alias:
                if self.alias[i]['dest'] == name:
                    collateral.append(self.alias[i]['src'])
            self.data.pop(name)
            self.names.remove(name)
            self.loggedChanges.append("Removed The Item: %s"%(name))
            for leaves in collateral:
                self.removeItem(leaves,root=False)
        elif name in self.alias:
            collateral = []
            destroy = []
            for i in self.alias: # i = src key
                if  i == name:
                    destroy.append(self.alias[i])
                elif self.alias[i]['dest'] == target:
                    collateral.append(i['src']) # remove deadlinks on tree
            
            for i in collateral:
                self.removeItem(i,root=False)
            for i in destroy:
                self.alias.pop(i['src'])
                self.aliasSet.remove(i['src'])            
                self.loggedChanges.append("Removed Alias point from <%s> to <%s>"%(i['src'],i['dest']))
                
        if root:
            with open(self.aliasDest,"w") as aliasWriter:
                aliasWriter.write(json.dumps(self.alias))
                aliasWriter.close()
            with open(self.dest,"w") as outHandle:
                outHandle.write(json.dumps(list(self.data.values())))
                outHandle.close()
            self.publish()
        
    def addItem(self,name,lo,hi):
        if not name in self.names:
            self.names.add(name)
            self.data[name] = {
                'name': name,
                'low': lo,
                'hi': hi
            }
            self.loggedChanges.append("Added new Item %s with bounds [%s,%s]"%(name,lo,hi))
            with open(self.dest,"w") as outHandle:
                outHandle.write(json.dumps(list(self.data.values())))
                outHandle.close()
        else:
            print("Item %s already exists."%(name))

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
        subprocess.call(["git", "commit", "-m \"Automated Refresh \n Changes:\n%s\""%('\n'.join(self.loggedChanges))])
        self.loggedChanges = []
        subprocess.call(["git","push","origin","master"])

    def estimate_literalOrItem(self,eStr,mistakes_tolerance = 6):
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
            value = self.query(eStr,mistakes_tolerance = mistakes_tolerance)
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

q = PricesTable(loadJsonViaGithub(),loadJsonViaGithub(file='alias.json'))
