import json
import urllib.request
import os
import subprocess


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
        


q = PricesTable(loadJsonViaGithub())
    
