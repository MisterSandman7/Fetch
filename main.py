#________________________________________________________________________________
#                                   FETCH
# A simple Discord bot that allows servers to track Twitter users by sending their 
# tweets to a specified channel within a server. Made thanks to the Python Discord 
# API (Discord.py) and the Python Twitter API (Tweepy).
# UPDATE 1.1.0 : Multi-channel support
# UPDATE 2.0 : Twitter thread support and rewrite
#________________________________________________________________________________

from    setup       import discord_token, client, logger
from    user_utils  import api, discord
from    utils       import remove_guilds, get_guilds, get_accounts_and_channels, get_timestamp, update_timestamp, remove_account
from    discord.ext import tasks
import  datetime
import  tweepy

@tasks.loop(seconds=30.0)
async def update_fetch():
    #Remove unneeded guilds before starting
    remove_guilds()
    #Get updated guild list
    guilds = get_guilds()

    for guild in guilds:
        accounts, channels = get_accounts_and_channels(guild)

        for account, channel_id in zip (accounts, channels):
            try:
                channel = client.get_channel(channel_id)
                #Check that the channel still exists
                if channel is not None:
                    #Tries to find both self replies and original tweet with replies ON
                    tweet = api.user_timeline(account,
                                            count = 1,
                                            tweet_mode = "extended",
                                            exclude_replies = False,
                                            include_rts = False)[0]
                    if (tweet.in_reply_to_screen_name == tweet.user.screen_name or tweet.in_reply_to_screen_name == None) == False:
                        #If the last tweet is a reply to another user, rollback to last original tweet
                        tweet = api.user_timeline(account,
                                                count = 1,
                                                tweet_mode = "extended",
                                                exclude_replies = True,
                                                include_rts = False)[0]

                    tweet_timestamp = (tweet.created_at - datetime.datetime(1970,1,1)).total_seconds()
                    tweet_link = f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
                    old_timestamp = get_timestamp(guild, account)
                    if tweet_timestamp - old_timestamp > 0:
                        update_timestamp(guild, account, tweet_timestamp)
                        await channel.send(tweet_link)

                else:
                    print('ERROR: Channel not found!')

            #In case added account has no tweets
            except IndexError as e:
                logger.exception(e)
                print('GUILD : ' + client.get_guild(guild).name + ' - ERROR : ' + str(e))
                error_str = 'Error!\nUser {} has no tweets!\nRemoving user...'.format(account)
                await channel.send(error_str)
                remove_account(guild, account)
                continue

            #In case rate limit in exceeded
            except tweepy.RateLimitError as e:
                logger.exception(e)
                print('GUILD : ' + client.get_guild(guild).name + ' - ERROR : ' + str(e))
                error_str = 'Error!\nTwitter Rate Limit exceeded!'
                await channel.send(error_str)

            #Generic Twitter error
            except tweepy.TweepError as e:
                logger.exception(e)
                print('GUILD : ' + client.get_guild(guild).name + ' - ERROR : ' + str(e))
                error_str = 'Error!\n `Code : {}`'.format(str(e))
                #await channel.send(error_str)
                continue   


@client.event
async def on_ready():
    print('Bot is online.')
    update_fetch.start()
    #restart.start()
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!fetch help"))

client.run(discord_token)