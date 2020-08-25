# Fetch!
<p align="center">
  <img src="./fetch_logo.png">
</p>

A simple Discord bot that allows servers to track Twitter users by relaying their posts to a specific channel within the server itself.
Made thanks to the Discord API and the Python Twitter API (Tweepy).

## Bot commands
Command | Input | Description
--------|-------|------------
Use the prefix '!fetch ' to access the bot, followed by any of these commands. **WARNING**: removing the bot from yours server will erase all of your Fetch settings from the database.
**set-channel** | `<channel_id>` | Set the channel in which the bot will post. Requires channel ID.
**remove-channel** | `None` | Remove the channel that the bot uses from the database.
**get-channel** | `None` | Returns ID and name of the channel that the bot uses.
**add-account** | `<scree_name>` | Add a twitter account to the database. Requires twitter handle, but exclude the @!
**remove-account** | `<screen_name>` |Remove a twitter account from the database.
**list-accounts** | `None` | List all twitter accounts that the bot looks out for in this server.
**help** | `None` | The command you're seeing right now.

You can add the bot to your server via [this link](https://discord.com/api/oauth2/authorize?client_id=695045455473672344&permissions=125952&scope=bot)

## License
**GNU GENERAL PUBLIC LICENSE**
*Version 3, 29 June 2007*

Copyright (C) 2007 Free Software Foundation, Inc. [https://fsf.org/](https://fsf.org/)
Everyone is permitted to copy and distribute verbatim copies
of this license document, but changing it is not allowed.