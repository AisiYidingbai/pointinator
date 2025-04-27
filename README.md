# Pointinator
An interactive text-based scoreboard and role manager for Discord.

## Features

* Scorekeeper. Type `add Yidingbai 100` to give Yidingbai 100 points.
* Glorified calculator. Type `split Yidingbai Helmutchan 100` to give Yidingbai and Helmutchan 50 points each.
* Scale fitter. Based on participants' points, fit them on a scale from 1 to 10 using a logarithmic or logistic curve.
* Social butterfly. Next time Helmutchan earns points, just type `add helm 50`. Pointinator knows who `helm` is.
* Custodian. Choose who is able to award points and who needs to queue their awards for approval.
* Roleplay enabler. Let your Discord members manage their own roles by asking Pointinator for them.
* Multiple hat-wearer. Pointinator is highly customisable for a range of purposes and roles.


## Installation

You can run Pointinator with Docker or Docker-compose (recommended), or you can install from this repo manually.

Pointinator requires a Discord server for which you have "Manage Server" permissions.

### Docker-compose (recommended)

1. Clone this repo and `cd` into it
```
git clone https://github.com/AisiYidingbai/pointinator.git
```
```
cd pointinator/
```
2. Copy-paste a Discord bot token into the `secret/secret.key` file. See the Discord bot setup below on how to get a bot token.
3. Create a copy of `default_config.ini` as `config.ini`.
```
cp default_config.ini config.ini
```
4. Start the Docker-compose instance.
```
docker-compose up -d
```
5. Done! You should see Pointinator online on Discord, ready for commands.

### Docker

1. Clone this repo and `cd` into it
```
git clone https://github.com/AisiYidingbai/pointinator.git
```
```
cd pointinator/
```
2. Build the Docker image from the Dockerfile
```
docker build -t aisiyidingbai/pointinator docker/
```
3. Copy-paste a Discord bot token into the `secret/secret.key` file. See the Discord bot setup below on how to get a bot token.
4. Run the Docker image. At run-time, bind mount the root directory of this repo into the container at `/pointinator/`.
```
docker run --rm -v .:/pointinator/ aisiyidingbai/pointinator
```
5. Done! You should see Pointinator online on Discord, ready for commands.

### Manual installation

1. Clone this repo and `cd` into it.
```
git clone https://github.com/AisiYidingbai/pointinator.git
```
```
cd pointinator/
```
2. Install Python 3.10 or higher using the appropriate method for your system. For example:
```
apt-get install python3
```
3. Install the prerequisite Python modules.
```
pip install -r requirements.txt
```
4. Copy-paste a Discord bot token into the `secret/secret.key` file. See the Discord bot setup below on how to get a bot token.
5. Run Pointinator, where `path/to/files/` is where you want Pointinator to store its data.
```
python pointinator.py -o path/to/files/
```
6. Optionally, create a daemon process for Pointinator so that it runs in the background. Assuming you can use unit files, you can do something like this:
```
nano /etc/systemd/system/pointinator.service
```
Create the unit file. Adjust according to the user and group that will be running Pointinator and the command being executed.
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
And activate and start the daemon.
```
systemctl daemon-reload
systemctl enable pointinator
systemctl start pointinator
```
7. Done! You should see Pointinator online on Discord, ready for commands.

### Migration

To migrate Pointinator, all you need are the `data/`, `secret/`, and `config.ini` folders and files. Paste them into a freshly-pulled repo and continue with the installation instructions as above.

## Discord setup

Pointinator works by logging in as a bot user. You'll need to create a bot user for your instance of Pointinator, generate a bot token so that it can log in, and invite it to your server.

### Create a bot user
1. Go to the Discord developer portal https://discord.com/developers/applications/ and log in with a user that has manage server permissions in the server you want to use Pointinator in.
2. In applications, create a new application, give it a name, and continue if you agree to the Terms of Service.
3. In the settings for your app, go to OAuth2, give it the "bot" scope, and give it the "manage roles", "read messages/view channels", "send messages", and "manage messages" permissions.
4. Allow the same permissions in the Bot tab and also enable the "message content" privileged gateway intent.

### Invite it to your server and generate its secret key so that it can log in
5. Go to the bottom and copy-paste the generated URL into your browser. When prompted, log in again and choose the server you want to use Pointinator in.
6. You'll see Pointinator joined. Back in bot settings, scroll back up and generate a token with "reset token" and note it down. Copy-paste it into the `secret/secret.key` file from when you pulled this repo.
7. If you want, go to general information and mess around with the settings in there to personalise your Pointinator.
8. Log in with Pointinator by running the command appropriate for how you installed Pointinator. You should see it come online.

### Customise your server
9. Now Pointinator has come online, you'll see a new file, `config.ini`. Edit this file as you wish, then restart Pointinator to make your changes take effect.
10. If you want Pointinator to manage roles, make sure that those roles are below the Pointinator role.

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

