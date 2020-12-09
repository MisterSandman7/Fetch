import  discord
from    discord.ext     import  commands
import  tweepy
from    tokens          import consumer_secret, consumer_token, discord_token
import  sqlite3
import  logging

version = '2.0.3'

#Create handler
logger = logging.getLogger('Fetch!')
file_handler = logging.FileHandler('debug/output.log')

#Level and format
file_handler.setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

#Init client object and assign prefix
client = commands.Bot(command_prefix='!fetch ')

#Twitter connection
auth = tweepy.AppAuthHandler(consumer_token,consumer_secret)
api = tweepy.API(auth, 
                retry_count=3,
                retry_delay=5,
                wait_on_rate_limit=True,
                wait_on_rate_limit_notify=True,
                timeout=60)

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