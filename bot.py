#!/usr/bin/env python3


# Work with Python 3.6
import discord
from discord.ext import commands
import requests
import re
from bs4 import BeautifulSoup
#import numpy as np

#config = np.loadtxt("config",dtype=str)
#print(type(str(config[0])))

config = np.loadtxt("config",dtype=str)
TOKEN = str(config[0])
USERNAME = str(config[1])
PASSWORD = str(config[2])

print(discord.__version__)
print(TOKEN)
print(USERNAME)
print(PASSWORD)

LOGIN_URL = "https://sso.pokemon.com/sso/login?locale=en&service=https://club.pokemon.com/us/pokemon-trainer-club/caslogin"
URL = "https://www.pokemon.com/us/play-pokemon/pokemon-events/"

bot = commands.Bot(command_prefix='$')

def proc_fields(f,par):
    if(f.startswith('Tournament Name')):
        par['name']=f[len('Tournament Name'):]
    elif(f.startswith('Tournament ID')):
        par['idn']=f[len('Tournament ID'):]
    elif(f.startswith('Category')):
        par['category']=f[len('Category'):]
    elif(f.startswith('Date')):
        par['date']=f[len('Date'):]
    elif(f.startswith('Registration')):
        par['registration']=f[len('Registration'):]
    elif(f.startswith('Product')):
        par['product']=f[len('Product'):]
    elif(f.startswith('Premier Event')):
        par['premier']=f[len('Premier Event'):].strip('\n ')
    elif(f.startswith('Status')):
        par['status']=f[len('Status'):]
    elif(f.startswith('Organizer Name')):
        par['to']=f[len('Organizer Name'):]
    elif(f.startswith('Venue Name')):
        par['venue']=f[len('Venue Name'):]
    elif(f.startswith('Address Line 1')):
        par['address1']=f[len('Address Line 1'):]
    elif(f.startswith('City')):
        par['city']=f[len('City'):]
    elif(f.startswith('Province/State')):
        par['state']=f[len('Province/State'):]
    elif(f.startswith('Postal/Zip Code')):
        par['zipcode']=f[len('Postal/Zip Code'):]
    elif(f.startswith('Country')):
        par['country']=f[len('Country'):]
    elif(f.startswith('\nWebsite\n')):
        par['website']=f[len('\nWebsite\n'):-2]
    elif(f.startswith('Admission')):
        par['cost']=f[len('Admission'):]
    elif(f.startswith('Details')):
        par['details']=f[len('Details'):]
    elif(f.startswith('League Cup')):
        par['sanctioned']='League Cup - ' + f[len('League Cup'):]
    elif(f.startswith('League Challenge')):
        par['sanctioned']='League Challenge - ' + f[len('League Challenge'):]


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------ END')

@bot.command()
async def hello(ctx):
    print('------ START')
    print("hello()")

    msg = r"Hello %s"%(ctx.message.author.mention)
    await ctx.send(msg)

    print('------ END')

@bot.command()
async def info(ctx):
    print("------ START")
    print("info()")
    embed = discord.Embed(title="Lance-A-Bot", description="Bot to aid in tournament organizing")
    embed.add_field(name="$tid [tournament ID] [time (optional)]", value="Grabs the information of the given tournament id number and starts a carpool channel for that event.")
    embed.add_field(name="$tid [tournament ID] lookup", value="Grabs the information of the given tournament id numberumber and posts its information.")
    embed.add_field(name="$info", value="prints this message")
    embed.add_field(name="$hello", value="says hello!")


    await ctx.send(embed=embed)
    print("------ END")

@bot.command()
async def tid(ctx,tid : str,time = None):
    print('------ START')
    print('tid()')

    permission = False
    for r in ctx.author.roles:
        if r.name == 'Shadow Government':
            permission = True
            break
        if r.name == 'Moderators':
            permission = True
            break

    if(not permission):
        await ctx.send("{} You do not have permission to use this command.".format(ctx.author.mention))
        print('------ END')
        return

    session_requests = requests.session()

    # Get login csrf token
    result = session_requests.get(LOGIN_URL)
    content = result.content
    soup = BeautifulSoup(content,'lxml')
    token = soup.find("input", {"name": "lt"}).get("value")

    print(token)
    # Create payload
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "lt": token,
        "execution":"e1s1",
        "_eventId":"submit"
    }

    # Perform login
    result = session_requests.post(LOGIN_URL, data = payload, headers = dict(referer = LOGIN_URL))

    URLT = URL + "%s"%(tid)
    print(URLT+"/")

    result = session_requests.get(URLT, headers = dict(referer = URLT))
    print(result.url)
    while((result.url != URLT+"/") and (result.url != "https://www.pokemon.com/us/play-pokemon/")):
        time.sleep(60)
        result = session_requests.get(URLT, headers = dict(referer = URLT))
        print(result.url)

    if(result.url == "https://www.pokemon.com/us/play-pokemon/"):
        await ctx.send("tournament id does not exist")
        print('------ END')
        return

    soup = BeautifulSoup(result.content, "lxml")
    if(soup.body.find_all(text="Access Denied")):
        print("ACCESS DENIED")
        await ctx.send("WEBSITE ACCESS DENIED")
        print('------ END')        
        return

    tourny = dict(name='',idn='',category='',date='',registration='',product='',premier='',
                  status='',sanctioned='',to='',venue='',address1='',city='',state='',
                  zipcode='',country='',website='',cost='',details='',lat='',lon='')

    fields = []
    ii=0
    while True:
        try:
            fields.append((soup.select('form fieldset li')[ii].text.encode("utf-8")))
            ii = ii+1
        except IndexError:
            break

    for f in fields:
        try:
            print(f)
            proc_fields(f.decode("utf-8"),tourny)
        except:
            pass

    link = soup.find_all('a', {"href" : re.compile(r'http://maps.google.com/*')})

    tourny['lat'] = float(link[0].attrs['href'].split("=")[1].split(' ')[0].strip(','))
    tourny['lon'] = float(link[0].attrs['href'].split("=")[1].split(' ')[1].strip(',').strip())

    #print(tourny)
    color = 0xeee657
    ping_vg = False
    ping_tcg = False
    if("Video" in tourny['product']):
        color = 0x551a8b
        ping_vg = True
        tourny['short'] = "VG"

    elif("Trading" in tourny['product']):
        color = 0xffa500
        ping_tcg = True
        tourny['short'] = "TCG"

    embed = discord.Embed(title="%(name)s"%tourny, description="", color=color)
    embed.add_field(name="Category", value="%(category)s"%tourny)
    embed.add_field(name="Date", value="%(date)s"%tourny)
    embed.add_field(name="Registration", value="%(registration)s"%tourny)
    embed.add_field(name="Premier Event", value="%(premier)s"%tourny)
    embed.add_field(name="Status", value="%(status)s"%tourny)
    embed.add_field(name="Admission", value="%(cost)s"%tourny)


    loc_str = "%(venue)s\n%(address1)s\n%(city)s, %(state)s %(zipcode)s\n<https://www.google.com/maps?q=%(lat)s,+%(lon)s>"%tourny
    embed.add_field(name="Location", value=loc_str,inline=False)
    embed.add_field(name="More Information", value="<%s>"%URLT,inline=False)


    if(time=='lookup'):
        message = await ctx.send(embed=embed)
        print("------ END")
        return

    if(time):
        embed.add_field(name="Carpool", value="The carpool will leave from Lot N (behind the Green Center) at **%s**. Add a reaction to this message to let us know you are coming. Comment below for any other discussion regarding the event or carpool."%time,inline=False)
    else:
        embed.add_field(name="Carpool", value="There will be no carpool to this event by the Mods. Add a reaction to this message to let us know you are coming. Comment below for any other discussion regarding the event or to organize a carpool.",inline=False)



    #print(str(ctx.guild.roles))
    # figure out the role to mention
    role = None
    everyone = None
    for r in ctx.guild.roles:
        if r.name == "TCG" and ping_tcg:
            role = r
        if r.name == "VGC" and ping_vg:
            role = r
        if r.name == "@everyone":
            everyone = r
    # create a channel for discussion about the event
    guild = ctx.message.guild

    category = None
    for cat in guild.categories:
        if cat.name == 'news':
            category = cat

    chanstr = "%(short)s-%(name)s-%(date)s"%tourny

    channel = await guild.create_text_channel(chanstr, category=category)
    await channel.set_permissions(everyone, read_messages = True,
                                      send_messages = True,
                                      read_message_history = True,
                                      embed_links = True,
                                      attach_files = True,
                                      external_emojis = True,
                                      add_reactions = True)

    message = None
    if(role):
        message = await channel.send("{}".format(role.mention),embed=embed)
    else:
        message = await channel.send(embed=embed)

    await message.add_reaction('\U0001F44D')
    await message.pin()

    print('------ END')

bot.run(TOKEN)

