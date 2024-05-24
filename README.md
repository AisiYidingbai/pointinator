# pointinator
discord bot that accepts commands from chat and tallies points and calculates reward tiers

# hi helm
so basically you `git clone https://github.com/AisiYidingbai/pointinator.git` this repo, install python, and then `pip install -r requirements.txt`, discord.py, numpy, and pandas, and run it.

(to update requirements.txt use pipreqs (`pip install pipreqs`) inside project folder)

copy-paste the secret key into `secret.py`, bai'll tell you my secrets if you ask nicely

the syntax is `python pointinator.py -o /path/to/files/` and you'll see the dev instance go up in the discord test server automatically

you need to specify a path where the sheets will live with `-o`, if the sheets aren't there already then pointinator will make them

# instructions if you're not helm

same as above but you need to create a bot user, invite it to your server, and generate a secret key for it so that it can log in

* go to discord developer portal https://discord.com/developers/applications/ and log in with a user that has manage server permissions in the server you want to use pointinator in
* in applications, create a new application, give it a name, and agree to the tos
* in the settings for your app, go to oauth2, give it the "bot" scope, and give it the "manage roles", "read messages/view channels", "send messages", and "manage messages" permissions
* go to the bottom and copy-paste the generated url into your browser. log in again and choose the server you want to use pointinator in
* you'll see pointinator joined. back in oauth2, scroll back up and note down the client secret. copy-paste it into the `key` variable in `secret.py` in this repo. this is how it logs in
* go to general information and mess around with the settings in there to personalise your pointinator
* start up an instance of pointinator with `python pointinator.py -o /path/to/files`. it'll log in to your server
* np enjoy

# tl;dr
`git clone https://github.com/AisiYidingbai/pointinator.git`

`cd pointinator`

`pip install -r requirements.txt`

make an app https://discord.com/developers/applications/

give it bot, manage roles, read messages/view channels, send messages, manage messages, and then invite it

put the client key in `secret.py`

`python pointinator.py -o /path/to/files/`

# daemonise
diy but you can google crontab and/or systemd unit files. idk about windows prob task scheduler. gl
