import  discord
from    discord.ext     import  commands
from    setup           import client, c, conn, api, logger
from    utils           import get_guilds, get_accounts_and_channels
import  time
from    main            import version

@client.command(name='get-channel')
async def get_channel(ctx, screen_name):
    try:
        guild_id = ctx.message.guild.id

        c.execute('select channel_id from database where guild_id = (?) and screen_name = (?)', (guild_id, screen_name))
        row = c.fetchone()
        if row is not None:
            #Channel (and user) exist, post name and ID
            await ctx.send(f'Channel ID: `{row[0]}`\nChannel name: {client.get_channel(row[0])}')
        else:
            #Channel (and user) not found
            await ctx.send('Channel was not found for this user in the database.')
    except Exception as e:
        logger.exception(e)
        print('GUILD : ' + ctx.message.guild.name + ' - ERROR : ' + str(e))
        error_str = 'Error!\n `Code : {}`'.format(str(e))
        await ctx.send(error_str)

@client.command(name='add')
@commands.has_permissions(administrator=True)
async def add_account(ctx, screen_name, channel_id = None):
    try:
        if channel_id == None:
            channel_id = ctx.message.channel.id

        guild_id = ctx.message.guild.id
        channel_id = int(channel_id)

        #Check if the channel exists before doing anything else
        if client.get_channel(channel_id) is None:
            await ctx.send('Channel does not exist.')
            return

        #Make sure the account has no @
        if screen_name.startswith('@'):
            await ctx.send('Type the account name without the @.')
            return

        user = api.get_user(screen_name)

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

    except Exception as e:
        logger.exception(e)
        print('GUILD : ' + ctx.message.guild.name + ' - ERROR : ' + str(e))
        error_str = 'Error!\n `Code : {}`'.format(str(e))
        await ctx.send(error_str)

@client.command(name='remove')
@commands.has_permissions(administrator=True)
async def remove_account(ctx, screen_name):
    try:
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

    except Exception as e:
        logger.exception(e)
        print('GUILD : ' + ctx.message.guild.name + ' - ERROR : ' + str(e))
        error_str = 'Error!\n `Code : {}`'.format(str(e))
        await ctx.send(error_str)

@client.command(name='list')
async def list_accounts(ctx):
    try:
        guild_id = ctx.message.guild.id
        accounts_str = ''
        
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

    except Exception as e:
        logger.exception(e)
        print('GUILD : ' + ctx.message.guild.name + ' - ERROR : ' + str(e))
        error_str = 'Error!\n `Code : {}`'.format(str(e))
        await ctx.send(error_str)

@client.command(name='info')
async def info(ctx):
    guild_list = get_guilds()
    guilds = len(guild_list)
    accounts_one = len(get_accounts_and_channels(ctx.message.guild.id)[0])
    accounts_all = 0

    for guild in guild_list:
        accounts_all += len(get_accounts_and_channels(guild)[0])

    embed_var = discord.Embed(title='Info')
    embed_var.add_field(name='Description', value='A simple Discord bot that allows servers to track Twitter users by sending their tweets to a specified channel within a server. Made thanks to the Python Discord API (Discord.py) and the Python Twitter API (Tweepy).', inline=False)
    embed_var.add_field(name='Version', value='{}'.format(version), inline=False)
    embed_var.add_field(name='Guilds', value='{}'.format(guilds), inline=False)
    embed_var.add_field(name='Twitter accounts', value='For this server : {}\nTotal : {}'.format(accounts_one, accounts_all), inline=False)
    embed_var.add_field(name='Discord Websocket latency', value='{}ms'.format(round(client.latency*1000, 2)), inline=False)
    await ctx.send(embed=embed_var)

@client.command(name='help')
async def help(ctx):
    try:
        embed_var = discord.Embed(title='Commands', description='Use the prefix \'!fetch \' to access the bot, followed by any of these commands.\n**WARNING**: removing the bot from your server will erase all of your Fetch settings from the database.', color=0x0)
        embed_var.add_field(name='info', value='General bot statistics and info.', inline=False)
        embed_var.add_field(name='add `<screen_name>` `<channel_id>`', value='Add a twitter account to the database, requires twitter handle (exclude @). `<channel_id>` is optional, if none specified current channel will be used. Use this command to update channel ID.', inline=False)
        embed_var.add_field(name='remove `<screen_name>`', value='Remove the user (and channel) from the database.', inline=False)
        embed_var.add_field(name='get-channel `<screen_name>`', value='Returns ID and name of the channel for this user.', inline=False)
        embed_var.add_field(name='list', value='List all twitter accounts that the bot looks out for in this server.', inline=False)
        embed_var.add_field(name='help', value='The command you\'re seeing right now.', inline=False)
        await ctx.send(embed=embed_var)
    except Exception as e:
        logger.exception(e)
        print('GUILD : ' + ctx.message.guild.name + ' - ERROR : ' + str(e))
        error_str = 'Error!\n `Code : {}`'.format(str(e))
        await ctx.send(error_str)