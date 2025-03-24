# pointinator
discord bot that accepts commands from chat and tallies points, calculates reward tiers, and manages roles

## roles supported
Vell, Sailies, Guildbosses, Khan, Leeching, PvP, Atoraxxion, Othergaming, Black Shrine

yep this bot is designed for bdo. there's no reason you can't use it for other things though

## points features
pointinator listens for commands and keeps counts of points. use `add Yidingbai 40` to give flat points, `split Yidingbai Helmutchan 60` to divide points, and `payout` to calculate the leaderboard

nicknames and shorthand syntax is supported, e.g. `a yid 40`, `s yid helm 60`, and `p`

leaderboard tiering supports logarithmic and logistic scaling and tiers can also be given directly

access to commands is limited by role. anyone with the Officers role gets direct access to pointinator commands. anyone without adds their commands to the queue for approval by an Officer

upon a reset, pointinator remembers the names of participants awarded with at least 1 point or tier from the previous leaderboard

# hi helm
so basically you `git clone https://github.com/AisiYidingbai/pointinator.git` this repo, install python, and then `pip install -r requirements.txt`, discord.py, numpy, and pandas, and run it.

(to update requirements.txt use pipreqs (`pip install pipreqs`) inside project folder)

`cd pointinator` and then copy-paste the secret key into `secret.py`, bai'll tell you my secrets if you ask nicely

to stop `secret.py` from updating when you update the repo with `git pull origin`, add it to your `gitignore`: `echo secret.py >> .gitignore`

the syntax is `python pointinator.py -o /path/to/files/` and you'll see the dev instance go up in the discord test server automatically

you need to specify a path where the sheets will live with `-o`, if the sheets aren't there already then pointinator will make them

# instructions if you're not helm
in short, you need to
1. create a bot user
2. invite it to your server and generate its secret key so that it can log in
3. install pointinator and install the secret key
4. let it run in the background
5. prepare your server
6. test it out
7. np enjoy

## 1. create a bot user
* go to discord developer portal https://discord.com/developers/applications/ and log in with a user that has manage server permissions in the server you want to use pointinator in
* in applications, create a new application, give it a name, and agree to the tos
* in the settings for your app, go to oauth2, give it the "bot" scope, and give it the "manage roles", "read messages/view channels", "send messages", and "manage messages" permissions
* allow the same permissions in the bot tab and also enable the "message content" privileged gateway intent

## 2. invite it to your server and generate its secret key so that it can log in
* go to the bottom and copy-paste the generated url into your browser. log in again and choose the server you want to use pointinator in
* you'll see pointinator joined. back in bot settings, scroll back up and generate a token with "reset token", note it down. copy-paste it into the `key` variable in `secret.py` in this repo. this is how it logs in
* go to general information and mess around with the settings in there to personalise your pointinator

## 3. install pointinator and the secret key
* in terminal, git clone this repo into the directory where you want pointinator to be installed: `git clone https://github.com/AisiYidingbai/pointinator.git` and then `cd` into it
* install python using your preferred method
* install dependencies: `pip install -r requirements.txt`
* edit `secret.py` and copy-paste the secret key from earlier into the "key" variable
* add secret.py into your gitignore: `echo secret.py >> .gitignore`
* start up an instance of pointinator with `python pointinator.py -o /path/to/files`. it'll log in to your server

## 4. let it run in the background
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

## 5. prepare your server
pointinator stalks chat in the #points and #roles channels. add them, and add the roles that pointinator manages. the list is at the top of this readme
* add a #points channel
* add a #roles channel
* add the roles that pointinator can manage. make sure those roles are below the pointinator role

## 6. test it out
* try out some commands in #roles such as `give othergaming`
* try out some commands in #points such as `add Yidingbai 40`
* get a syntax reminder in the #roles channel by keyboardsmashing
* see information in the #points channel by typing `help`, `info`, and `points`

## troubleshooting
* update pointinator: `cd` to the repo folder and run `git pull origin`
* restart pointinator: `systemctl restart pointinator`
* see what's going on with a crashed pointinator: `systemctl status pointinator`

# Using a specific python version

You can use [uv](https://github.com/astral-sh/uv) to handle the virtual environment for you.

* First, make sure you've installed uv. They provide a one-liner to do so:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

* Then switch to the top-level directory of pointinator:

```
$ cd /path/to/pointinator
```

* Now you can create a virtual environment, and (using the `--python` parameter) pin it down to a specific python version:

```
$ uv venv --python 3.12
```

* Install the dependencies into the venv:

```
$ uv pip install -r requirements.txt
```

`uv` will automatically detect the venv (located in `.venv`) and run a virtual pip (and be much faster doing so).
By default the venv created by `uv` comes without the pip module installed. You can add it manually by running `$ uv pip install pip`.

* Now whenever you want to run pointinator, you can do so either by using uv or sourcing the venv:

```
$ uv run python pointinator.py # run using uv

$ source .venv/bin/activate # or source virtual environment
$ python pointinator.py # and run manually
```

`uv` has many more features. Check out the docs to learn more!

# tl;dr
```
git clone https://github.com/AisiYidingbai/pointinator.git
```
```
cd pointinator
```
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

to background pointinator:
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
