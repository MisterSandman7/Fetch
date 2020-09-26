#________________________________________________________________________________
#                                   FETCH v1.1.1
# A simple Discord bot that allows servers to track Twitter users by sending their 
# tweets to a specified channel within a server. Made thanks to the Python Discord 
# API (Discord.py) and the Python Twitter API (Tweepy).
# UPDATE 1.1.0 : Multi-channel support
#________________________________________________________________________________
import  discord
from    discord.ext import  commands, tasks
import  tweepy
from    tokens      import  *
import  sqlite3
import  logging
import  datetime
import  itertools
import  os
import  sys

reset = False

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
c.execute('''create table if not exists database (
            guild_id    integer,
            screen_name text,
            timestamp   integer,
            channel_id  integer
            )''')

#Twitter connection
auth = tweepy.AppAuthHandler(consumer_token,consumer_secret)
api = tweepy.API(auth)

#________________________________________________________________________________
#                                   CHANNELS
#________________________________________________________________________________

@client.command(name='get-channel')
async def get_channel(ctx, screen_name):
    guild_id = ctx.message.guild.id

    c.execute('select channel_id from database where guild_id = (?) and screen_name = (?)', (guild_id, screen_name))
    row = c.fetchone()
    if row is not None:
        #Channel (and user) exist, post name and ID
        await ctx.send(f'Channel ID: `{row[0]}`\nChannel name: {client.get_channel(row[0])}')
    else:
        #Channel (and user) not found
        await ctx.send('Channel was not found for this user in the database.')

#________________________________________________________________________________
#                                   TWITTER
#________________________________________________________________________________

@client.command(name='add')
@commands.has_permissions(administrator=True)
async def add_account(ctx, screen_name, channel_id = None):
    try:
        if channel_id == None:
            channel_id = ctx.message.channel.id
        guild_id = ctx.message.guild.id
        channel_id = int(channel_id)
        user = api.get_user(screen_name)

        #Check if channel exists
        if client.get_channel(channel_id) is not None:
            # If user exits and channel_id is correct
            c.execute('select * from database where screen_name = (?) and guild_id = (?)', (screen_name, guild_id))
            row = c.fetchone()
            if row is None:
                #User was not found in the database for the server
                c.execute('insert into database values (?,?,0,?)', (guild_id, screen_name, channel_id))
                await ctx.send(f'User {user.screen_name} has been added to {ctx.message.guild.name}.\nChannel: `{channel_id}`')
            else:
                #User was found, check if channel_id is the same
                c.execute('select channel_id from database where screen_name = (?) and guild_id = (?)', (screen_name, guild_id))
                row = c.fetchone()
                if row[0] == channel_id:
                    #Channel_id is the same, no need to change it
                    await ctx.send('User and channel are already registered.')
                else:
                    #Channel_id is different, update it
                    c.execute('update database set channel_id = (?) where guild_id = (?) and screen_name = (?)', (channel_id, guild_id, screen_name))
                    await ctx.send(f'Channel was updated for user {user.screen_name}')
            conn.commit()
        else:
            await ctx.send('Channel does not exist.')
    except tweepy.TweepError as e:
        print(e.response.text)
        await ctx.send('User was not found.')    

@client.command(name='remove')
@commands.has_permissions(administrator=True)
async def remove_account(ctx, screen_name):
    guild_id = ctx.message.guild.id

    #Look if the user is in the database for the server
    c.execute('select * from database where screen_name = (?) and guild_id = (?)', (screen_name, guild_id))
    row = c.fetchone()
    if row is not None:
        #User exists, remove it
        c.execute('delete from database where screen_name = (?) and guild_id = (?)', (screen_name, guild_id))
        await ctx.send(f'User {screen_name} has been removed from the database for {ctx.message.guild.name}')
    else:
        #User is not in the database
        await ctx.send(f'User {screen_name} was not found in the database.')
    conn.commit()

@client.command(name='list')
async def list_accounts(ctx):
    accounts_str = ''
    guild_id = ctx.message.guild.id

    c.execute('select screen_name, channel_id from database where guild_id = (?)', (guild_id, ))
    accounts = c.fetchall()
    if accounts is not None:
        embed_var = discord.Embed(title=f'Account list for {ctx.message.guild.name}')
        accounts_str = ''
        channel_name_str = ''
        channel_id_str = ''
        for account in accounts:
            accounts_str += f'- {account[0]}\n'
            channel_name_str += f'{client.get_channel(account[1])}\n'
            channel_id_str += f'{account[1]}\n'
        embed_var.add_field(name='Account', value=accounts_str, inline=True)
        embed_var.add_field(name='Channel name', value=channel_name_str, inline=True)
        embed_var.add_field(name='Channel ID', value=channel_id_str, inline=True)
        await ctx.send(embed=embed_var)
    else:
        await ctx.send(f'Nothing registered for {ctx.message.guild.name}')

#________________________________________________________________________________
#                                   TIMESTAMP
#________________________________________________________________________________

def update_timestamp(guild_id, screen_name, timestamp):
    c.execute('update database set timestamp = (?) where guild_id = (?) and screen_name = (?)', (timestamp, guild_id, screen_name))
    conn.commit()

def get_timestamp(guild_id, screen_name):
    c.execute('select timestamp from database where guild_id = (?) and screen_name = (?)', (guild_id, screen_name))
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
    c.execute('select guild_id from database')
    y = c.fetchall()
    #Convert to set to eliminate duplicates, then back to list
    temp_set = set(y)
    y = list(temp_set)
    for x in y:
        for guild in x:
            guild_list.append(guild)
    return guild_list

def get_accounts_and_channels(guild_id):
    account_list = []
    channel_list = []
    account_list.clear()
    channel_list.clear()
    c.execute('select screen_name, channel_id from database where guild_id = (?)', (guild_id, ))
    y = c.fetchall()
    for x in y:
        account_list.append(x[0])
        channel_list.append(x[1])
    return account_list, channel_list

def remove_guilds():
    guilds = []
    guilds.clear()
    for guild in client.guilds:
        guilds.append(guild.id)
    guilds_db = get_guilds()
    trimmed_guilds = set(guilds) ^ set(guilds_db)
    for guild in trimmed_guilds:
        c.execute('delete from database where guild_id = (?)', (guild,))
        conn.commit()

client.remove_command('help')
@client.command(name='help')
async def help(ctx):
    embed_var = discord.Embed(title='Commands', description='Use the prefix \'!fetch \' to access the bot, followed by any of these commands.\n**WARNING**: removing the bot from your server will erase all of your Fetch settings from the database.', color=0x0)
    embed_var.add_field(name='add `<screen_name>` `<channel_id>`', value='Add a twitter account to the database, requires twitter handle (exclude @). `<channel_id>` is optional, if none specified current channel will be used. Use this command to update channel ID.', inline=False)
    embed_var.add_field(name='remove `<screen_name>`', value='Remove the user (and channel) from the database.', inline=False)
    embed_var.add_field(name='get-channel `<screen_name>`', value='Returns ID and name of the channel for this user.', inline=False)
    embed_var.add_field(name='list', value='List all twitter accounts that the bot looks out for in this server.', inline=False)
    embed_var.add_field(name='help', value='The command you\'re seeing right now.', inline=False)
    await ctx.send(embed=embed_var)

@tasks.loop(seconds=30.0)
async def update_fetch():
    try:
        #Remove unneeded guilds before starting
        remove_guilds()
        #Get guild list
        guilds = get_guilds()
        for guild in guilds:
            accounts, channels = get_accounts_and_channels(guild)
            for account, channel_id in zip(accounts, channels):
                channel = client.get_channel(channel_id)
                #Check that the channel still exists
                if channel is not None:
                    tweet = api.user_timeline(account, count = 1, tweet_mode = "extended", exclude_replies = True, include_rts = False)[0]
                    tweet_link = f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
                    tweet_timestamp = (tweet.created_at - datetime.datetime(1970,1,1)).total_seconds()
                    old_timestamp = get_timestamp(guild, account)
                    if tweet_timestamp - old_timestamp > 0:
                        update_timestamp(guild, account, tweet_timestamp)
                        await channel.send(tweet_link)
                else:
                    print('ERROR: Channel not found!')
    except tweepy.TweepError as e:
        print(e.response.text)
    
@tasks.loop(minutes=60.0)
async def restart():
    #A simple (and likely placeholder) script to restart the bot.
    #This is needed because the bot suffers from a hanging problem
    #I currently am not able to solve.
    global reset
    if reset is True:
        print('Scheduled restart.')
        update_fetch.stop()
        os.execv(sys.executable, [sys.executable] + sys.argv)
    reset = True

@client.event
async def on_ready():
    print('Bot is online.')
    update_fetch.start()
    restart.start()
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!fetch help"))


client.run(discord_token)