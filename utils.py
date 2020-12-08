from setup import client, c, conn

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