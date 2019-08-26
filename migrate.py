#migrate.py by @ashdawngary

# migrates all data from the csv format to a more parsable and sane format known as json

import argparse
import os
import json
parser = argparse.ArgumentParser()

parser.add_argument("infile",type=str,help="source file to convert in the weird csv format")
parser.add_argument("outfile",type=str,help="out file to convert to the new outformat")
parser.add_argument("-absolute","-a",action="store_true",help="interprets fs paths as absolute rather than relative.")
args = parser.parse_args()

inFileExists = (args.absolute and os.path.isfile(args.infile)) or ((not args.absolute) and os.path.isfile(os.getcwd()+"/"+ args.infile))
if not inFileExists:
    print("Unable to find your file specified. Exiting.")
    exit(-1)




with open(args.infile,"r") as vLoadHandle:
    inData = vLoadHandle.read()
    vLoadHandle.close()



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

def getSanitizedRange(cStr):
    if len(cStr) == 0:
        print("Empty price, returning -5")
        return (-5,-5)
    if '-' == cStr[0]:
        return (-1,-1)
    elif '-' in cStr:
        data = cStr.split('-')
        if len(data) > 2:
            print("Error couldnt get sanitized range for: %s, (%s negative split arguments???)"%(cStr,len(data)))
        value,isSigned = getSanitizedValue(data[0])
        value2,isSigned2 = getSanitizedValue(data[1])
        isSigned = isSigned2 if isSigned == None else isSigned
        isSigned2 = isSigned if isSigned2 == None else isSigned2
        isSigned,isSigned2 = ('c','c') if isSigned == None else (isSigned,isSigned2)
        return (augment(value,isSigned),augment(value2,isSigned2))
    else:
        result = augment(*getSanitizedValue(cStr))
        return (result,result)

#notes
#0 mod 3 is name
#1 mod 3 is item
#2 mod 3 is some garbage
inData = inData.replace('\r','\n')
datapts = inData.split('\n')

#print(len(datapts))
delimeter = ',' if 'csv' == args.infile[-3:] else '\t' # assuming its a tsv file.
opposite = '\t' if 'csv' == args.infile[-3:] else ',' 
nFullLines = int(len(datapts)/3) + 1
pushed_data = []

for ix in range(0,nFullLines):
    nameIndex = 3 * ix
    itemIndex = 3 * ix + 1
    if itemIndex >= len(datapts):
        break

    names = datapts[nameIndex].replace(opposite,"").split(delimeter)
    itemPrices = datapts[itemIndex].replace(opposite,"").split(delimeter)
    
    
    if not len(names) == len(itemPrices):
        print("Got names: %s"%(names))
        print("Got prices: %s"%(itemPrices))
        print("error these two dont match up",len(names), len(itemPrices))
        names = names[:min(len(names),len(itemPrices))]
        itemPrices = itemPrices[:min(len(names),len(itemPrices))]
        
    else:
        for r in range(0,len(names)):
            current_name = names[r]
            current_price = itemPrices[r]
            if min(len(current_name),len(current_price)) == 0:
                continue
            range_interpret = getSanitizedRange(current_price)
            
            pushed_data.append({
                'name':current_name,
                'low': range_interpret[0],
                'hi': range_interpret[1]
                })

print('Successfully migrated %s elements.'%(len(pushed_data)))

with open(args.outfile,"w")  as vWriteHandle:
    vWriteHandle.write(json.dumps(pushed_data))
    vWriteHandle.close()
    
    
    
    
