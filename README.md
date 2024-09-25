# pointinator
discord bot that accepts commands from chat and tallies points and calculates reward tiers

# hi helm
so basically you `git clone https://github.com/AisiYidingbai/pointinator.git` this repo, install python, and then `pip install -r requirements.txt`, discord.py, numpy, and pandas, and run it.

(to update requirements.txt use pipreqs (`pip install pipreqs`) inside project folder)

`cd pointinator` and then copy-paste the secret key into `secret.py`, bai'll tell you my secrets if you ask nicely

to stop `secret.py` from updating when you update the repo with `git pull origin`, add it to your `gitignore`: `echo secret.py >> .gitignore`

the syntax is `python pointinator.py -o /path/to/files/` and you'll see the dev instance go up in the discord test server automatically

you need to specify a path where the sheets will live with `-o`, if the sheets aren't there already then pointinator will make them

# instructions if you're not helm
in short, you need to
* create a bot user
* invite it to your server
* generate its secret key so that it can log in
* install pointinator
* install the secret key
* set up a daemon process to let it run in the background

## create a bot user
* go to discord developer portal https://discord.com/developers/applications/ and log in with a user that has manage server permissions in the server you want to use pointinator in
* in applications, create a new application, give it a name, and agree to the tos
* in the settings for your app, go to oauth2, give it the "bot" scope, and give it the "manage roles", "read messages/view channels", "send messages", and "manage messages" permissions
* allow the same permissions in the bot tab and also enable the "message content" privileged gateway intent

## invite it to your server and generate its secret key so that it can log in
* go to the bottom and copy-paste the generated url into your browser. log in again and choose the server you want to use pointinator in
* you'll see pointinator joined. back in bot settings, scroll back up and generate a token with "reset token", note it down. copy-paste it into the `key` variable in `secret.py` in this repo. this is how it logs in
* go to general information and mess around with the settings in there to personalise your pointinator

## install pointinator and the secret key
* in terminal, git clone this repo into the directory where you want pointinator to be installed: `git clone https://github.com/AisiYidingbai/pointinator.git` and then `cd` into it
* install python using your preferred method
* install dependencies: `pip install -r requirements.txt`
* edit `secret.py` and copy-paste the secret key from earlier into the "key" variable
* add secret.py into your gitignore: `echo secret.py >> .gitignore`
* start up an instance of pointinator with `python pointinator.py -o /path/to/files`. it'll log in to your server

## set up a daemon process to let it run in the background
this section lets pointinator run in the background and might be different depending on your system
* create a unit file, e.g. `nano /etc/systemd/system/pointinator.service`
* type this. you'll need to edit the "ExecStart" line for the correct command depending on your installation. also edit the "user" and "group" for the correct user and group that is going to run the pointinator. use `whoami` and `groups` to find these out
```
[Unit]
Description=Pointinator
[Service]
ExecStart=python /home/user/pointinator/pointinator.py -o /home/user/pointinator/
User=user
Group=group
[Install]
WantedBy=multi.user.target
```
* reload: `systemctl daemon-reload`. you might need to `sudo`
* enable: `systemctl enable pointinator`
* start it up: `systemctl start pointinator`

## troubleshooting
* update pointinator: `cd` to the repo folder and run `git pull origin`
* restart pointinator: `systemctl restart pointinator`
* see what's going on with a crashed pointinator: `systemctl status pointinator`

# tl;dr
```
git clone https://github.com/AisiYidingbai/pointinator.git
```
```
cd pointinator
````
```
pip install -r requirements.txt
```
make an app https://discord.com/developers/applications/

give it bot scope; manage roles, read messages/view channels, send messages, and manage messages permissions; and message content privileged gateway intent, and then invite it to your server

put the bot token in `secret.py`

```
echo secret.py >> .gitignore
```

```
python pointinator.py -o /path/to/files/
```

to daemonise pointinator:
```
nano /etc/systemd/system/pointinator.service
```
```
[Unit]
Description=Pointinator
[Service]
ExecStart=python /home/user/pointinator/pointinator.py -o /home/user/pointinator/
User=user
Group=group
[Install]
WantedBy=multi.user.target
```
```
systemctl daemon-reload
```
```
systemctl enable pointinator
```
```
systemctl start pointinator
```
