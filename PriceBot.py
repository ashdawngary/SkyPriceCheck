import discord
import tasks
import time
#from itertools import cycle
from asyncio import sleep
from discord.ext import commands
from prices import *
#from oauth2client.service_account import ServiceAccountCredentials

currentPriceTable = PricesTable(loadJsonViaGithub())
client = commands.Bot(command_prefix = '$')
#Fancy Status Message
timeout = 10
status = "no status dont ask"
async def change_status():
    while True:
        await client.change_presence(activity=discord.Game(status))
        await sleep(10)

def resanitize(price):
    if price < 10**3:
        return str(price)
    elif price < 10**6:
        return str(round(price/10**3,3))+"K"
    elif price < 10**9:
        return str(round(price/10**6,3))+"M"
    else:
        return str(round(price/10**9,3))+"B"
#common used functions
def findPrice(item):
    estimated = currentPriceTable.estimate_literalOrItem(item)
    return 'between %s and %s'%(resanitize(estimated[0]),resanitize(estimated[1]))

def eval(stringinput):
    estimate = currentPriceTable.eval(stringinput)
    return estimate

def findRatio(item1, item2):
    a_price = findPrice(item1)
    b_price = findPrice(item2)
    if a_price < b_price:
        return '%s is %s more worth %s'%(item2,item1)
    return
#Console Start MSG
@client.event
async def on_ready():
    print('CORE>>>STARTUP task done')
    print('CORE>>>CORE Version 1.2')
    print(f'DEBUG>>>Bot USERNAME: {client.user.name}')
    print(f'DEBUG>>>Bot ID: {client.user.id}')
    print('PLUGIN>>>JerryPlugin.FancyStatus-v1.1..........ENABLED')
    await change_status()


#$price command
@client.command (name ='price', description = 'Price Checks an item, usage $price <item>, make sure all letters are in small case and replace space with "_"', brief = '$price <item>')
async def price(ctx, *, item):

    try:


        q = currentPriceTable.guestimate(item)[0] # returns [Item_Guessed,distance_to_autocorrect] l m a o ask questions please
        extramessage = ""
        if not q == item:
            extramessage = "(corrected %s as %s)"%(item,q)
        await ctx.send(f'price: {findPrice(item)}{extramessage}') # i copied it from ur old code thiccc

        #print(f'{item} is {findPrice(item)}')
    except Exception as e:
        await ctx.send(f'i broke because of : {e}(ur mom)')

        print(f'Failed to price check {item}')

@client.command (name ='calculate', description = 'Basically a calculator(crazy op) usage $calculate <item>', brief = '$calculate <item>')
async def price(ctx, *, item):

    try:
        result = eval(item)
        await ctx.send(f'calculating: between {resanitize(result[0])} and {resanitize(result[1])}') # i copied it from ur old code thiccc

    except Exception as e:
        await ctx.send(f'i broke lmao i am now s a a d : {e}')

        print(f'Failed to price check {item}')


#$request command
@client.command(name='request', description='Request Price Checkers to manually price check an item for you, also add it into the bot''s database', brief = '$request <item>')
async def request(ctx, item):
        await ctx.send(f'<@&593161930273849354> , please price check the following item {item}, and add it to the database, thank you!')

client.run('NjE1NzUyNDQxMjExNzgxMTMx.XWSmKg.WtKgoM1UsFgWIWeVMx_0cFkOb44')
