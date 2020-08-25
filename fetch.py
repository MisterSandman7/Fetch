#________________________________________________________________________________
#                                   FETCH v1.00
#A simple Discord bot to relay Twitter messages to servers in specific channels
#based on requestes from the formers.
#The bot allows customization of the channel used and the Twitter accounts to
#look after.
#________________________________________________________________________________

import  discord
from    discord.ext import  commands, tasks
import  os
import  tweepy
from    tokens      import *
import  sqlite3
import  logging
import  datetime

#Init client object and assign prefix
client = commands.Bot(command_prefix='!fetch ')

#Logger utility
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='fetch.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

#Connect to database
conn = sqlite3.connect('fetch.db')
c = conn.cursor()

#Create tables
c.execute('''create table if not exists channels (
            guild_id    integer,
            channel_id  integer
            )''')

c.execute('''create table if not exists servers (
            guild_id    integer,
            screen_name text,
            timestamp   integer
            )''')

#Twitter connection
auth = tweepy.AppAuthHandler(consumer_token,consumer_secret)
api = tweepy.API(auth)

#________________________________________________________________________________
#                                   CHANNELS
#________________________________________________________________________________

@client.command(name='set-channel')
@commands.has_permissions(administrator=True)
async def set_channel(ctx, channel_id):
    guild_id = ctx.message.guild.id
    channel_id = int(channel_id)

    #Check if channel exists
    if client.get_channel(channel_id) is not None:
        #Check if channel is already in the database
        c.execute('select channel_id from channels where guild_id = (?)', (guild_id,))
        row = c.fetchone()
        if row is None:
            #Channel is not in the database, add it
            c.execute('insert into channels values(?,?)', (guild_id, channel_id))
            await ctx.send('Channel added in the database.')
        elif row[0] == channel_id:
            #Channel is already in the database and is the same as the new one
            await ctx.send('Channel is already in the database.')
        else:
            #Update channel in the database
            c.execute('update channels set channel_id = (?) where guild_id = (?)', (channel_id, guild_id))
            await ctx.send('Channel updated in the database.')
    else:
        await ctx.send('Channel does not exist.')
    #Commit all changes
    conn.commit()

@client.command(name='remove-channel')
@commands.has_permissions(administrator=True)
async def remove_channel(ctx):
    guild_id = ctx.message.guild.id

    #Check if channel is in the database
    c.execute('select * from channels where guild_id = (?)', (guild_id,))
    row = c.fetchone()
    if row is None:
        #Channel was not found in the database
        await ctx.send('Channel was not found in the database.')
    else:
        #Chanel found, remove it from the database
        c.execute('delete from channels where guild_id=(?)', (guild_id,))
        await ctx.send('Channel was removed from the database.')
    #Commit all changes
    conn.commit()

@client.command(name='get-channel')
async def get_channel(ctx):
    guild_id = ctx.message.guild.id

    #Check if channel exists
    c.execute('select channel_id from channels where guild_id = (?)', (guild_id,))
    row = c.fetchone()
    if row is not None:
        #Channel exists, post name and ID
        await ctx.send(f'Channel ID: {row[0]}\nChannel name: {client.get_channel(row[0])}')
    else:
        #Channel was not found
        await ctx.send('Channel was not found in the database.')

#________________________________________________________________________________
#                                   TWITTER
#________________________________________________________________________________

@client.command(name='add-account')
@commands.has_permissions(administrator=True)
async def add_account(ctx, screen_name):
    guild_id = ctx.message.guild.id
    
    try:
        user = api.get_user(screen_name)
        if user is not None:
            #If user exists
            c.execute('select * from servers where screen_name = (?) and guild_id = (?)', (screen_name, guild_id))
            row = c.fetchone()
            if row is None:
                #User was not found in the database for the server
                c.execute('insert into servers values (?,?,0)', (guild_id, screen_name))
                await ctx.send(f'User {user.screen_name} has been added to the database for {ctx.message.guild.name}')
            else:
                #User was found in the database for the server
                await ctx.send(f'User {user.screen_name} is already in the database for {ctx.message.guild.name}')
    except tweepy.TweepError as e:
        print(e.response.text)
        await ctx.send('User does not exist.')
    conn.commit()

@client.command(name='remove-account')
@commands.has_permissions(administrator=True)
async def remove_account(ctx, screen_name):
    guild_id = ctx.message.guild.id

    #Look if the user is in the database for the server
    c.execute('select * from servers where screen_name = (?) and guild_id = (?)', (screen_name, guild_id))
    row = c.fetchone()
    if row is not None:
        #User exists, remove it
        c.execute('delete from servers where screen_name = (?) and guild_id = (?)', (screen_name, guild_id))
        await ctx.send(f'User {screen_name} has been removed from the database for {ctx.message.guild.name}')
    else:
        #User is not in the database
        await ctx.send(f'User {screen_name} was not found in the database.')
    conn.commit()

@client.command(name='list-accounts')
async def list_accounts(ctx):
    accounts_str = ''
    guild_id = ctx.message.guild.id

    c.execute('select screen_name from servers where guild_id = (?)', (guild_id,))
    accounts = c.fetchall()
    for account in accounts:
        accounts_str += f'- {account[0]}\n'
    await ctx.send(f'List of accounts for {ctx.message.guild.name}:\n{accounts_str}')

#________________________________________________________________________________
#                                   TIMESTAMP
#________________________________________________________________________________

def update_timestamp(guild_id, screen_name, timestamp):
    c.execute('update servers set timestamp = (?) where guild_id = (?) and screen_name = (?)', (timestamp, guild_id, screen_name))
    conn.commit()

def get_timestamp(guild_id, screen_name):
    c.execute('select timestamp from servers where guild_id = (?) and screen_name = (?)', (guild_id, screen_name))
    row = c.fetchone()
    if row is not None:
        return row[0]
    else:
        #Just for safety, should never be executed
        return 0

#________________________________________________________________________________
#                                   HELP UTILITY
#________________________________________________________________________________

def get_guilds():
    guild_list = []
    guild_list.clear()
    c.execute('select guild_id from channels')
    y = c.fetchall()
    for x in y:
        for guild in x:
            guild_list.append(guild)
    return guild_list

def get_accounts(guild_id):
    account_list = []
    account_list.clear()
    c.execute('select screen_name from servers where guild_id = (?)', (guild_id,))
    y = c.fetchall()
    for x in y:
        for account in x:
            account_list.append(account)
    return account_list

def client_get_channel(guild_id):
    c.execute('select channel_id from channels where guild_id = (?)', (guild_id,))
    row = c.fetchone()
    if row is not None:
        return row[0]
    else:
        return None

def remove_guilds():
    #Compares guilds in database and actual guilds, then removes the
    #guilds in the database that don't have Fetch in them anymore
    guilds = []
    guilds.clear()
    for guild in client.guilds:
        guilds.append(guild.id)
    guilds_db = get_guilds()
    trimmed_guilds = set(guilds) ^ set(guilds_db)
    for guild in trimmed_guilds:
        c.execute('delete from channels where guild_id = (?)', (guild,))
        c.execute('delete from servers where guild_id = (?)', (guild,))
        conn.commit()

client.remove_command('help')
@client.command(name='help')
async def help(ctx):
    embed_var = discord.Embed(title='Commands',desciption='Use the prefix \'!fetch \' to access the bot, followed by any of these commands.\n**WARNING**: removing the bot from your server will erase all of your Fetch settings from the database.', color=0x0)
    embed_var.add_field(name='set-channel `<channel_id>`', value='Set the channel in which the bot will post. Requires channel ID.', inline=False)
    embed_var.add_field(name='remove-channel', value='Remove the channel that the bot uses from the database.', inline=False)
    embed_var.add_field(name='get-channel', value='Returns ID and name of the channel that the bot uses.', inline=False)
    embed_var.add_field(name='add-account `<screen_name>`', value='Add a twitter account to the database. Requires twitter handle, but exclude the @!', inline=False)
    embed_var.add_field(name='remove-account `<screen_name>`', value='Remove a twitter account from the database.', inline=False)
    embed_var.add_field(name='list-accounts', value='List all twitter accounts that the bot looks out for in this server.', inline=False)
    embed_var.add_field(name='help', value='The command you\'re seeing right now.', inline=False)
    await ctx.send(embed=embed_var)

#________________________________________________________________________________
#                                   UPDATE LOOP
#________________________________________________________________________________

@tasks.loop(seconds=30.0)
async def update_fetch():
    try:
        #Remove unneeded guilds before starting
        remove_guilds()
        #Get guild list
        guilds = get_guilds()
        for guild in guilds:
            #Get account list for the guild
            accounts = get_accounts(guild)
            for account in accounts:
                #Get channel for the guild
                channel_id = client_get_channel(guild)
                #Check that the channel has been set
                if channel_id is not None:
                    #If there is a channel, go ahead
                    channel = client.get_channel(channel_id)
                    tweet = api.user_timeline(account, count = 1, tweet_mode = "extended", exclude_replies = True, include_rts = False)[0]
                    tweet_link = f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
                    tweet_timestamp = (tweet.created_at - datetime.datetime(1970,1,1)).total_seconds()
                    old_timestamp = get_timestamp(guild, account)
                    if tweet_timestamp - old_timestamp > 0:
                        update_timestamp(guild, account, tweet_timestamp)
                        await channel.send(tweet_link)
    except tweepy.TweepError as e:
        print(e)

@client.event
async def on_ready():
    print('Bot is online.')
    update_fetch.start()

client.run(discord_token)