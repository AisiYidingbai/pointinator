#!/bin/env python

# -*- coding: utf-8 -*-

"""
Created on Mon Jan 31 15:42:10 2022

@author: AisiYidingbai
"""

import __main__ as main
import discord                         # Discord
import argparse                        # Commandline interface
import pandas as pd                    # Dataframes
import numpy as np                     # Math
import logging                         # Logging
import json                            # File I/O
import re                              # Text matching
import os                              # File I/O
import uuid                            # Random tokens
from datetime import datetime          # Date and time
from math import e                     # Constant e
from pathlib import Path               # High-level file system access
from configparser import ConfigParser  # Config parsing
ver = "2.5.1"
updated = "7-Jun-2025"


# %% Load configuration from file


program_path = Path(__file__).parent.resolve()

config_file_path = program_path / "config.ini"

if not config_file_path.is_file():
    print("[WARN] No configuration file found")

    default_config_file_path = Path("default_config.ini")
    with (
        open(config_file_path, "wb") as ofile,
        open(default_config_file_path, "rb") as ifile
    ):
        ofile.write(ifile.read())
    print(f"[INFO] Created default configuration file `{config_file_path}`")

with open(config_file_path, "r", encoding="utf-8") as ifile:
    config = ConfigParser()
    config.read_file(ifile)

key_file_path = program_path / config["general"]["key_file"]


admin_key_file_path = program_path / config["general"]["admin_key_file"]
admin_db_file_path = program_path / config["general"]["admin_db_file"]

admin_key = None

if not admin_db_file_path.is_file():
    print("[INFO] No admin database file found. Creating one...")
    admin_db_file_path.touch()

if not admin_key_file_path.is_file():
    print("[INFO] No admin key file found. Creating one with random key...")

    new_admin_key = uuid.uuid4().hex

    with open(admin_key_file_path, "w") as ofile:
        ofile.write(new_admin_key)

    print("[INFO] New admin key:")
    print('*' * (len(new_admin_key) + 4))
    print("* ", new_admin_key, " *", sep='')
    print('*' * (len(new_admin_key) + 4))

    admin_key = new_admin_key
else:
    with open(admin_key_file_path, "r") as ifile:
        lines = ifile.readlines()

    admin_key = lines[0].strip()


# %% Load admin key


# %% Load secret key for API access


secret_key = None

if key_file_path.is_file():
    with open(key_file_path, "r", encoding="utf-8") as key_file:
        lines = key_file.readlines()

    nonempty_lines = [line.strip() for line in lines if line.strip()]

    if len(nonempty_lines) != 1:
        raise RuntimeError(f"`{key_file_path}` must contain exactly 1 API token. {len(nonempty_lines)} given.")

    secret_key = nonempty_lines[0]
else:
    # Fallback to importing `secret.py`
    try:
        import secret
    except ModuleNotFoundError as err:
        raise FileNotFoundError("File `secret.py` not found!") from err

    secret_key = secret.key
    print("[WARN] Usage of `secret.py` has been deprecated and might be removed in future versions.",
          "Please use `secret.key` instead.")


# %% Common I/O functions


def io_points_load():
    x = pd.read_csv(file_points)
    x = x[['Participant', 'Value', 'Type', 'Date']]
    return x


def io_queue_load():
    x = pd.read_csv(file_queue)
    x = x[['Requestor', 'Request', 'Time']]
    return x


def io_params_load():
    with open(file_params) as f:
        x = json.load(f)
    return x


def io_points_save(x):
    if (os.path.exists(bak3_points)):
        os.remove(bak3_points)                    # Rotate existing backups
    if (os.path.exists(bak2_points)):
        os.rename(bak2_points, bak3_points)
    if (os.path.exists(bak1_points)):
        os.rename(bak1_points, bak2_points)
    if (os.path.exists(file_points)):
        os.rename(file_points, bak1_points)
    # Write to file
    x.to_csv(file_points)


def io_queue_save(x):
    if (os.path.exists(bak3_queue)):
        os.remove(bak3_queue)                      # Rotate existing backups
    if (os.path.exists(bak2_queue)):
        os.rename(bak2_queue, bak3_queue)
    if (os.path.exists(bak1_queue)):
        os.rename(bak1_queue, bak2_queue)
    if (os.path.exists(file_queue)):
        os.rename(file_queue, bak1_queue)
    # Write to file
    x.to_csv(file_queue)


def io_params_save(x):
    with open(file_params, 'w') as f:
        json.dump(x, f, indent=4)


# %% Common helper functions


# Find an exact or partial match for string x within list y. Return None
# if not found.
def interpret(x, y):
    r = None
    # Remove non-alphanumeric characters
    x = re.sub("[^a-zA-Z0-9]", "", x)
    y = set(y)
    if (r is None):
        for i in y:                                                            # x exists in y
            if (x == i):
                r = i
                break
    if (r is None):
        for i in y:                                                            # Element in y ends with x
            if (re.search(x + "$", i, re.IGNORECASE)):
                r = i
                break
    if (r is None):
        for i in y:                                                            # Element in y starts with x
            if (re.search("^" + x, i, re.IGNORECASE)):
                r = i
                break
    if (r is None):
        for i in y:                                                            # Element in y contains x
            if (re.search(x, i, re.IGNORECASE)):
                r = i
                break
    if (r is None):
        # Element in y contains all the characters in x in order
        for i in y:
            if (re.search(re.sub("(.)", ".*\\1", x) + ".*", i, re.IGNORECASE)):
                r = i
                break
    return r


# Check if the sender of message x has the Officers role
def is_officer(x):
    return any(role.name == "Officers" for role in x.author.roles)


def man(cmd):
    match cmd:
        case "add":
            r = "`a/add <p ...> <n>`: **Add** *n* points to *p*articipants."
        case "chat":
            r = "`c/chat <...>`: Send a **chat** message in the #points channel without Pointinator interpreting it as a command."
        case "delete":
            r = "`del/delete <p ...>`: **Delete** *p*articipants."
        case "edit":
            r = "`edit <row> <column> <value>`: **Edit** the sheet at *row* and *column* to *value*. *column* must be one of `Participant`, `Type`, or `Value`."
        case "edit value":
            r = "`edit <row> Participant <value>`: **Edit** the *row*th *Value* in the sheet to *value*. *value* must be a number."
        case "edit type":
            r = "`edit <row> Type <value>`: **Edit** the *row*th *Type* to *value*. *value* must be one of `point` or `tier`."
        case "help":
            r = "`h/help`: Show **help** on Pointinator syntax."
        case "info":
            r = "`i/info`: Show **info** on Pointinator."
        case "get":
            r = "`get <param>`: **Get** a Pointinator *param*eter."
        case "new":
            r = "`n/new <p ...>`: Add **new** *p*articipants."
        case "offset":
            r = "`o/offset <p ...> <n>`: **Offset** *n* tiers to *p*articipants."
        case "payout":
            r = "`p/payout`: Summarise current payout per participant in lexicographical order."
        case "points":
            r = "`points`: Show **point** values."
        case "rename":
            r = "`ren/rename <p1> <p2>`: **Rename** all instances of *p*articipant1 to *p*articipant2."
        case "reset":
            r = "`r/reset`: **Reset** the sheet."
        case "set":
            r = "`set <param> <value>`: **Set** a Pointinator *param*eter to *value*."
        case "show":
            r = "`show`: **Show** the current sheet."
        case "split":
            r = "`s/split <p ...> <n>`: **Split** *n* points between *p*articipants."
        case "tail":
            r = "`t/tail <n>`: **Tail** the last *n* sheet actions."
        case "tiers":
            r = "`tiers`: Show the current point requirements per **tier**."
        case "undo":
            r = "`z`: **Undo** the last change."
        case "whois":
            r = "`whois <nickname>`: See if I can convert a *nickname* to a participant already on the board."
        case "queue":
            r = "`q`: Show the **queue**."
        case "queue approve":
            r = "`q a`: **Approve** the request at the top of the queue."
        case "queue deny":
            r = "`q d`: **Deny** the request at the top of the queue."
        case "queue queue":
            r = "`q q <requestor> <request>`: Manually add an entry to the **queue** with *requestor* and *request*."
        case "queue undo":
            r = "`q z`: **Undo** the last change to the queue."
    return r


def rng(x):
    r = x[int(np.floor(np.random.uniform(low=0, high=len(x))))]
    return r


def command_echo(x):
    r = "*Your command:  *`" + re.sub("[*`]", "", x.content) + "`" + "\n"
    return r


# %% Control commands


def control_command(message, parsed):
    keyword = parsed[0].lower()

    match keyword:
        case "op" | "makeadmin":
            send = make_admin(message, parsed)
        case "deop" | "removeadmin":
            send = remove_admin(message, parsed)

    return send


def add_admin_to_db(user_id):
    with open(admin_db_file_path, "r") as ifile:
        lines = ifile.readlines()

    admins = [line.strip() for line in lines]

    if str(user_id) in admins:
        return  # nothing to do

    admins.append(str(user_id))

    with open(admin_db_file_path, "w") as ofile:
        ofile.write('\n'.join(admins))


def remove_admin_from_db(user_id):
    with open(admin_db_file_path, "r") as ifile:
        lines = ifile.readlines()

    admins = [line.strip() for line in lines]

    if str(user_id) not in admins:
        return  # nothing to do

    while str(user_id) in admins:
        admins.remove(str(user_id))

    with open(admin_db_file_path, "w") as ofile:
        ofile.write('\n'.join(admins))


def is_admin(user_id):
    with open(admin_db_file_path, "r") as ifile:
        lines = ifile.readlines()

    admins = [line.strip() for line in lines]

    return str(user_id) in admins


def extract_user_information(message):
    if not isinstance(message.author, discord.User):
        return None, None

    user = message.author

    user_name = user.global_name
    user_id = user.id

    # sanity check
    if len(user_name) == 0 or user_id is None:
        return None, None

    return user_name, user_id


def make_admin(message, parsed):
    user_name, user_id = extract_user_information(message)

    if user_name is None or user_id is None:
        return

    if is_admin(user_id):
        return message.reply("You are already an admin.")

    if len(parsed) != 2:
        return message.reply("You are expected to submit an admin token.")

    admin_token = parsed[1]

    if admin_token != admin_key:
        return message.reply("You submitted an invalid admin token.")

    add_admin_to_db(user_id)
    return message.reply(f"Congratulations {user_name}, you are now an admin [user id {user_id}]")


def remove_admin(message, parsed):
    user_name, user_id = extract_user_information(message)

    if user_name is None or user_id is None:
        return

    if not is_admin(user_id):
        return message.reply("You are currently not an admin.")

    remove_admin_from_db(user_id)
    return message.reply(f"You are no longer an admin {user_name} [user id {user_id}]. Goodbye.")


# %% Curve shapes
def logarithmic(x):  # use log shape to calculate tier from points
    params = io_params_load()
    sheet = io_points_load()
    points = sheet.loc[sheet['Type'] == 'point'].groupby(
        'Participant').sum('Value')
    highscore = max(points['Value']) * 0.9
    tcap = params['tcap']  # apex of curve
    cap = np.minimum(highscore, params['cap']) + 1  # curve anchor
    k = (tcap - 1) / np.log(cap)
    x = x + 1  # add pseudocount
    y = k * np.log(x)
    y = np.floor(y + 1)  # to integer, round up
    y = np.minimum(y, tcap)  # not exceed tcap
    return y


def logarithmic_inverse(y):  # use log shape to calculate points from tier
    params = io_params_load()
    sheet = io_points_load()
    points = sheet.loc[sheet['Type'] == 'point'].groupby(
        'Participant').sum('Value')
    highscore = max(points['Value']) * 0.9
    tcap = params['tcap']  # apex of curve
    cap = np.minimum(highscore, params['cap']) + 1  # curve anchor
    k = (tcap - 1) / np.log(cap)
    y = y - 1  # find bottom of tier
    x = np.power(e, y / k)
    x = np.ceil(x - 1)  # to integer, remove pseudocount
    return x


def logistic(x):  # use logistic shape to calculate tier from points
    params = io_params_load()
    sheet = io_points_load()
    points = sheet.loc[sheet['Type'] == 'point'].groupby(
        'Participant').sum('Value')
    shape = -params['difficulty']
    highscore = max(points['Value']) * 0.9
    tcap = params['tcap']  # apex of curve
    cap = np.minimum(highscore, params['cap']) + 1  # curve anchor
    x0 = (cap + 1 - shape) / 2
    k = np.log(tcap) / (x0 + shape)
    x = x - 1
    y = tcap / (1 + np.power(np.e, -k * (x - x0)))
    y = np.floor(y + 1)  # to integer, round up
    y = np.minimum(y, tcap)  # not exceed tcap
    return y


def logistic_inverse(y):  # use logistic shape to calculate points from tier
    params = io_params_load()
    sheet = io_points_load()
    points = sheet.loc[sheet['Type'] == 'point'].groupby(
        'Participant').sum('Value')
    shape = -params['difficulty']
    highscore = max(points['Value']) * 0.9
    tcap = params['tcap']  # apex of curve
    cap = np.minimum(highscore, params['cap']) + 1  # curve anchor
    x0 = (cap + 1 - shape) / 2
    k = np.log(tcap) / (x0 + shape)
    y = y - 1  # find bottom of tier
    if y == 0:  # deal at lower asymptote
        x = 0
    else:
        x = x0 - (np.log(tcap / y - 1) / k)
        x = np.ceil(x + 1)  # to integer, add pseudocount
        x = np.maximum(x, 0)
    return x


# %% Actions: points
def act_points_add(participant, value, kind, sheet):
    if kind == "point":
        # delete the initialising entry for new sheets if it is there
        sheet = sheet.loc[sheet['Participant'] != "No-one yet"]
    # get the current date and time
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    sheet = pd.concat([sheet, pd.DataFrame({'Participant': [participant], 'Value': [
                      value], 'Type': [str(kind)], 'Date': [date]})])  # add an entry to the sheet
    return sheet


def act_points_delete(participant, sheet):
    sheet = sheet.loc[sheet['Participant'] != participant]
    return sheet


def act_points_edit(row, col, newvalue):
    sheet = io_points_load()
    row = int(row)
    sheet.at[row, col] = newvalue
    io_points_save(sheet)
    return


def act_points_new(participant, sheet):
    # delete the initialising entry for new sheets if it is there
    sheet = sheet.loc[sheet['Participant'] != "No-one yet"]
    # get the current date and time
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    sheet = pd.concat([sheet, pd.DataFrame({'Participant': [participant], 'Value': [
                      0], 'Type': ["point"], 'Date': [date]})])  # add an entry to the sheet
    return sheet


def act_points_rename(participant1, participant2, sheet):
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    # Copy sheet rows belonging to participant1 and update to participant2
    sheet2 = sheet.loc[sheet['Participant'] == participant1]
    sheet2['Participant'] = participant2
    sheet2['Date'] = date
    # Remove sheet rows belonging to participant1 and bind rows
    sheet = sheet.loc[sheet['Participant'] != participant1]
    sheet = pd.concat([sheet, sheet2])
    return sheet


def act_points_reset():
    sheet = pd.DataFrame([], columns=['Participant', 'Value', 'Type', 'Date'])
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    sheet = pd.concat([sheet, pd.DataFrame(
        {'Participant': ["No-one yet"], 'Value': [0], 'Type': ["point"], 'Date': [date]})])
    io_points_save(sheet)
    return


def act_points_show(col="Tier", filter=None):
    sheet = io_points_load()
    params = io_params_load()
    # Tiers awarded by points
    points = sheet.loc[sheet['Type'] == 'point'].groupby(
        'Participant').sum('Value')
    method = params['method']
    if method == 1:
        points['Tier'] = logarithmic(points['Value'])
    elif method == 2:
        points['Tier'] = logistic(points['Value'])
    # Tiers awarded by offsets
    offsets = sheet.loc[sheet['Type'] == 'tier'].groupby(
        'Participant').sum('Value')['Value']  # pivot the sheet for tiers
    # Combined board
    board = points.join(
        offsets,
        on="Participant",
        how="outer",
        rsuffix=".tier")  # join tiers to point sheet
    # Edge cases
    if board.index.name is None:
        board = board.set_index('Participant')
    # set zero tiers for participants with no offsets
    board['Value.tier'][np.isnan(board['Value.tier'])] = 0
    # set zero points for participants with yes offsets but no points
    board['Value'][np.isnan(board['Value'])] = 0
    # set 1 tier for participants with yes offsets but no points
    board['Tier'][np.isnan(board['Tier'])] = 1
    board['Tier'] = np.minimum(
        np.minimum(
            board['Tier'],
            params['tcap']) +
        board['Value.tier'],
        params['thardcap'])  # don't let the tier exceed the max
    if filter is not None:
        board = board.filter(filter, axis=0)
    if col == "Tier":
        # sort the sheet by descending tiers and points
        board = board.sort_values(['Tier', 'Value'], ascending=[False, False])
    elif col == "Points":
        # sort the sheet by descending points
        board = board.sort_values('Value', ascending=False)
    elif col == "Participant":
        board = board.sort_values('Participant', ascending=True)
    board['Points'] = board['Value']
    cols = ['Points', 'Tier']
    board = board[cols]
    return board


def act_points_tiers():
    currenttiers = list()
    tierpoints = list()
    params = io_params_load()
    method = params['method']
    for i in range((int(params['tcap'])), 0, -1):
        currenttiers.append("T" + str(i))
        if method == 1:
            tierpoints.append(logarithmic_inverse(i))
        elif method == 2:
            tierpoints.append(logistic_inverse(i))
    tiers = pd.DataFrame({'Tier': currenttiers, 'Value': tierpoints})
    tiers = tiers.set_index('Tier')
    return tiers


def act_points_undo():
    # delete the current sheet
    os.remove(file_points)
    # reinstate backup 1 as the current sheet
    os.rename(bak1_points, file_points)
    if (os.path.exists(bak2_points)):
        # reinstate backup 2 as backup 1 if it exists
        os.rename(bak2_points, bak1_points)
        if (os.path.exists(bak3_points)):
            # reinstate backup 3 as backup 2 if it exists
            os.rename(bak3_points, bak2_points)
    return

# %% Actions: queue


def act_queue_add(requestor, request):
    queue = io_queue_load()
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    queue = pd.concat([queue, pd.DataFrame(
        {'Requestor': [requestor], 'Request': [request], 'Time': [date]})])
    io_queue_save(queue)
    return


def act_queue_delete(requestor, request):
    return


def act_queue_show():
    queue = io_queue_load()
    queue = queue[['Requestor', 'Request', 'Time']]
    return queue


def act_queue_approve(message):
    queue = io_queue_load()
    request = queue.iloc[0, 1]
    parsed = re.split(" ", request)
    message.content = str(request)
    content_queued = points_channel(message, parsed)
    queue = queue.iloc[1:]
    io_queue_save(queue)
    return content_queued


def act_queue_deny():
    queue = io_queue_load()
    queue = queue.iloc[1:]
    io_queue_save(queue)
    return


def act_queue_undo():
    # delete the current sheet
    os.remove(file_queue)
    # reinstate backup 1 as the current sheet
    os.rename(bak1_queue, file_queue)
    if (os.path.exists(bak2_queue)):
        # reinstate backup 2 as backup 1 if it exists
        os.rename(bak2_queue, bak1_queue)
        if (os.path.exists(bak3_queue)):
            # reinstate backup 3 as backup 2 if it exists
            os.rename(bak3_queue, bak2_queue)
    return

# %% Actions: role


def act_roles_give(message, roleid):
    send = message.author.add_roles(roleid)
    return send


def act_roles_remove(message, roleid):
    send = message.author.remove_roles(roleid)
    return send

# %% Common frontend functions


def channel_respond(message, colour, content):
    if not (hasattr(main, "__file__")) or passthrough:
        return content
    else:
        # Content length 2 or less means no sheet to show
        if len(content) == 1:
            send = message.channel.send(content[0])
        elif len(content) == 2:
            send = message.channel.send(content[0] + content[1])
        # Content length greater than 2 means sheet to show
        else:
            # Use plaintext if any contents are giga long (>1024)
            if any(len(c) > 1024 for c in content):
                content = ''.join(content)
                send = message.channel.send(content)
            # Use embeds if none are greater than 1024 characters
            else:
                embed = discord.Embed(title=content[0], color=colour)
                for i in list(range(1, len(content))):
                    embed.add_field(name="", value=content[i], inline=False)
                embed.set_footer(text="by Yidingbai :)")
                send = message.channel.send(embed=embed)
        return send

# %% Points functions


def points_add(message, parsed):
    # If officer
    if is_officer(message):
        colour = discord.Colour.teal()
        content1 = command_echo(message)
        # Check inputs
        sheet = io_points_load()
        value = parsed[-1]
        operands = len(parsed)
        if operands < 3:
            content2 = "Problem with `add`: expected 3 or more operands, got " + \
                str(operands) + ".\nUsage: " + man("add")
            content = [content1, content2]
        elif not re.search("^-*\\d+\\.*\\d*$", value):
            content2 = "Problem with `add`: expected a number for points, got `" + \
                value + "`.\nUsage: " + man("add")
            content = [content1, content2]
        elif re.search("^nan$", parsed[1], re.IGNORECASE) and interpret(parsed[1], sheet['Participant']) is None:
            content2 = "Problem with `add`: forbidden value passed, `nan`.\nUsage: " + \
                man("add")
            content = [content1, content2]
        # Execute
        elif operands == 3:
            string = parsed[1]
            value = float(value)
            warnNew = False
            participant = interpret(string, sheet['Participant'])
            if not participant:
                participant = string
                warnNew = True
            filter = [participant]
            sheet = act_points_add(participant, value, "point", sheet)
            io_points_save(sheet)
            content2 = rng(
                [
                    "Good stuff",
                    "Gerat",
                    "Superb",
                    "Well done",
                    "Much thank",
                    "Hekaru yeah",
                    "Noice"]) + ", " + str(value) + " points were given to " + participant + "."
            if warnNew:
                content2 = content2 + "\n\n⚠️ You added a new helmper!"
                warnNew = False
            content3 = "```" + \
                str(act_points_show(filter=list(dict.fromkeys(filter)))) + "```"
            content = [content1, content2, content3]
        else:
            participants = ""
            warnNew = False
            value = float(value)
            filter = []
            for s in list(range(1, operands - 1)):
                string = parsed[s]
                participant = interpret(string, sheet['Participant'])
                if not participant:
                    participant = string
                    warnNew = True
                filter = filter + [participant]
                sheet = act_points_add(participant, value, "point", sheet)
                if s != operands - 2:
                    if operands - 2 == 2:
                        participants = participants + participant + " "
                    else:
                        participants = participants + participant + ", "
                else:
                    participants = participants + "and " + participant
            io_points_save(sheet)
            content2 = rng(
                [
                    "Noice effort",
                    "Everyone is best",
                    "Good job, crew",
                    "Well done everyone",
                    "Guildies% much",
                    "Stonks",
                    "Such activity"]) + ", " + participants + " each got " + str(value) + " points."
            if warnNew:
                content2 = content2 + "\n\n⚠️ You added a new helmper!"
                warnNew = False
            content3 = "```" + \
                str(act_points_show(filter=list(dict.fromkeys(filter)))) + "```"
            content = [content1, content2, content3]
        send = channel_respond(message, colour, content)
        return send
    # If not officer
    else:
        send = queue_add(message, parsed)
        return send


def points_chat(message, parsed):
    return


def points_delete(message, parsed):
    # If officer
    if is_officer(message):
        colour = discord.Colour.teal()
        content1 = command_echo(message)
        # Check inputs
        operands = len(parsed)
        if operands < 2:
            content2 = "Problem with `delete`: not enough operands passed.\nUsage: " + \
                man("delete")
            content = [content1, content2]
        # Execute
        elif operands == 2:
            sheet = io_points_load()
            participant = interpret(parsed[1], sheet['Participant'])
            if participant:
                sheet = act_points_delete(participant, sheet)
                io_points_save(sheet)
                content2 = rng(["Removing from the board"]) + \
                    ", " + participant + "."
                content = [content1, content2]
            else:
                content2 = "Problem with `delete`: could not find participant " + \
                    parsed[1] + ".\nUsage: " + man("delete")
                content = [content1, content2]
        else:
            sheet = io_points_load()
            participants = []
            for p in list(range(1, operands)):
                participant = interpret(parsed[p], sheet['Participant'])
                if participant:
                    sheet = act_points_delete(participant, sheet)
                    participants = participants + [participant]
            if len(participants) > 0:
                io_points_save(sheet)
                participants = ", ".join(participants)
                content2 = rng(["Removing from the board"]) + \
                    ", " + participants + "."
                content = [content1, content2]
            else:
                content2 = "Problem with `delete`: could not find any of those participants.\nUsage: " + \
                    man("delete")
                content = [content1, content2]
        send = channel_respond(message, colour, content)
        return send
    # If not officer
    else:
        send = queue_add(message, parsed)
        return send


def points_edit(message, parsed):
    # If officer
    if is_officer(message):
        colour = discord.Colour.teal()
        content1 = command_echo(message)
        # Check inputs
        operands = len(parsed)
        if operands < 4:
            content2 = "Problem with `edit`: not enough operands passed.\nUsage: " + \
                man("edit")
            content = [content1, content2]
        elif not re.search("^\\d+$", parsed[1]):
            content2 = "Problem with `edit`: expected numeric, got `" + \
                str(parsed[1]) + "`.\nUsage: " + man("edit")
            content = [content1, content2]
        elif int(parsed[1]) > len(io_points_load()):
            content2 = "Problem with `edit`: row number `" + \
                str(parsed[1]) + "` cannot be greater than the number of rows in the sheet.\nUsage: " + man("edit")
            content = [content1, content2]
        elif parsed[2] not in ['Participant', 'Value', 'Type']:
            content2 = "Problem with `edit`: expected valid column name, got `" + \
                str(parsed[2]) + "`.\nUsage: " + man("edit")
            content = [content1, content2]
        elif parsed[2] == "Value" and not re.search("^-*\\d+.*\\d*$", parsed[3]):
            content2 = "Problem with `edit`: trying to edit a `Value`, expected a numeric, got `" + \
                str(parsed[2]) + "`.\nUsage: " + man("edit")
            content = [content1, content2]
        elif parsed[2] == "Type" and parsed[3] not in ['point', 'tier']:
            content2 = "Problem with `edit`: trying to edit a `Type`, expected one of `point`, `tier`, got `" + \
                str(parsed[3]) + "`.\nUsage: " + man("edit")
            content = [content1, content2]
        # Execute
        else:
            row = int(parsed[1])
            col = str(parsed[2])
            new = parsed[3]
            sheet = io_points_load()
            old = sheet.at[row, col]
            act_points_edit(row, col, new)
            sheet = io_points_load()
            sli = sheet.iloc[row:row + 1]
            content2 = "Changed the " + col + " at row " + \
                str(row) + " from " + str(old) + " to " + str(new)
            content3 = "```" + str(sli) + "```"
            content = [content1, content2, content3]
        send = channel_respond(message, colour, content)
        return send
    # If not officer
    else:
        send = queue_add(message, parsed)
        return send


def points_get(message, parsed):
    colour = discord.Colour.magenta()
    content1 = command_echo(message)
    # Execute
    operands = len(parsed)
    if operands == 2:
        params = io_params_load()
        string = parsed[1]
        param = interpret(string, list(params.keys()))
        if param is not None:
            value = params[param]
            content2 = "The value of " + str(param) + " is " + str(value) + "."
            content = [content1, content2]
        else:
            params = pd.DataFrame.from_dict(params, orient='index')
            content2 = "Here are the parameters."
            content3 = "```" + str(params) + "```"
            content = [content1, content2, content3]
    else:
        params = io_params_load()
        params = pd.DataFrame.from_dict(params, orient='index')
        content2 = "Here are the parameters."
        content3 = "```" + str(params) + "```"
        content = [content1, content2, content3]
    send = channel_respond(message, colour, content)
    return send


def points_man(message, parsed):
    colour = discord.Colour.teal()
    content1 = command_echo(message)

    content2 = "\nPoints commands:"
    content2 = content2 + "\n\t" + man("add")
    content2 = content2 + "\n\t" + man("split")
    content2 = content2 + "\n\t" + man("offset")
    content2 = content2 + "\n\t" + man("new")
    content2 = content2 + "\n\t" + man("show")
    content2 = content2 + "\n\t" + man("delete")
    content2 = content2 + "\n\t" + man("undo")
    content2 = content2 + "\n\t" + man("rename")
    content2 = content2 + "\n\t" + man("reset")
    content2 = content2 + "\n\t" + man("tail")
    content2 = content2 + "\n\t" + man("tiers")
    content2 = content2 + "\n\t" + man("whois")
    content2 = content2 + "\n\t" + man("set")
    content2 = content2 + "\n\t" + man("get")
    content2 = content2 + "\n\t" + man("edit")
    content2 = content2 + "\n\t" + man("points")
    content2 = content2 + "\n\t" + man("help")
    content2 = content2 + "\n\t" + man("info")
    content2 = content2 + "\n\t" + man("chat")

    content2 = content2 + "\n\nQueue commands:"
    content2 = content2 + "\n\t" + man("queue")
    content2 = content2 + "\n\t" + man("queue approve")
    content2 = content2 + "\n\t" + man("queue deny")
    content2 = content2 + "\n\t" + man("queue queue")
    content2 = content2 + "\n\t" + man("queue undo")
    content2 = content2 + "\n"

    content = [content1, content2]
    send = channel_respond(message, colour, content)
    return send

try:
    text_info = config["info"]["info"]
    text_info = re.sub("\n", "\n\n\t", text_info)
except:
    text_info = """
\n\t*About*: Send commands by chatting in this channel. Send a command every time someone does something that earns points. Issue `points` to see qualifying activities.
\n\t*Usage*: Add points with `a <participant> <points>`. The *participant* can be a nickname if they're already on the board. For a full list of commands, issue `help`. For detailed usage, see the guide at <https://goodluck.servegame.com/index.php/how-to-pointinate/>.
\n\t*Privileges*: Officers' commands will be executed by the bot immediately. Please type deliberately. If you're not an officer, then your command will be put in the queue for an officer to approve.
\n\t*Support*: Pointinator goes down for nightly maint around 4:00 GMT/BST. If it's down outside of those times, contact Aisi Yidingbai. Pointinator is open-source software available at <https://github.com/AisiYidingbai/pointinator>.
"""

def points_info(message, parsed):
    colour = discord.Colour.teal()
    content1 = command_echo(message)
    content2 = "\n\tWelcome to **Pointinator**, a Discord bot that keeps track of points. This version " + ver + ", last updated " + updated + "." + text_info
    content = [content1, content2]
    send = channel_respond(message, colour, content)
    return send


def points_new(message, parsed):
    # If officer
    if is_officer(message):
        colour = discord.Colour.teal()
        content1 = command_echo(message)
        # Check inputs
        operands = len(parsed)
        if operands < 2:
            content2 = "Problem with `new`: not enough operands passed.\nUsage: " + \
                man("new")
            content = [content1, content2]
        elif ("nan" in parsed[1:operands] or "NaN" in parsed[1:operands]):
            content2 = "Problem with `new`: forbidden value passed: `nan`.\nUsage: " + \
                man("new")
            content = [content1, content2]
        # Execute
        sheet = io_points_load()
        if operands == 2:
            participant = parsed[1]
            sheet = act_points_new(participant, sheet)
            io_points_save(sheet)
            content2 = rng(["Adding to the board"]) + " " + participant + "."
            content = [content1, content2]
        else:
            participants = ""
            for p in list(range(1, operands)):
                participant = parsed[p]
                sheet = act_points_new(participant, sheet)
                if p != operands - 1:
                    if operands - 1 == 2:
                        participants = participants + participant + " "
                    else:
                        participants = participants + participant + ", "
                else:
                    participants = participants + "and " + participant
            io_points_save(sheet)
            content2 = rng(["Adding to the board"]) + ", " + participants + "."
            content = [content1, content2]
        send = channel_respond(message, colour, content)
        return send
    # If not officer
    else:
        send = queue_add(message, parsed)
        return send


def points_offset(message, parsed):
    # If officer
    if is_officer(message):
        colour = discord.Colour.teal()
        content1 = command_echo(message)
        # Check inputs
        sheet = io_points_load()
        value = parsed[-1]
        operands = len(parsed)
        if operands < 3:
            content2 = "Problem with `offset`: expected 3 or more operands, got " + \
                str(operands) + ".\nUsage: " + man("offset")
            content = [content1, content2]
        elif not re.search("^-*\\d+$", value):
            content2 = "Problem with `offset`: expected a number for tiers, got `" + \
                value + "`.\nUsage: " + man("offset")
            content = [content1, content2]
        elif re.search("^nan$", parsed[1], re.IGNORECASE) and interpret(parsed[1], sheet['Participant']) is None:
            content2 = "Problem with `offset`: forbidden value passed, `nan`.\nUsage: " + \
                man("offset")
            content = [content1, content2]
        # Execute
        elif operands == 3:
            string = parsed[1]
            value = float(value)
            participant = interpret(string, sheet['Participant'])
            warnNew = False
            if not participant:
                participant = string
                warnNew = True
            filter = [participant]
            sheet = act_points_add(participant, value, "tier", sheet)
            io_points_save(sheet)
            content2 = rng(["Gotcha"]) + ", " + str(value) + \
                " tiers were given to " + participant + "."
            if warnNew:
                content2 = content2 + "\n\n⚠️ You added a new helmper!"
                warnNew = False
            content3 = "```" + \
                str(act_points_show(filter=list(dict.fromkeys(filter)))) + "```"
            content = [content1, content2, content3]
        else:
            participants = ""
            value = float(value)
            warnNew = False
            filter = []
            for s in list(range(1, operands - 1)):
                string = parsed[s]
                participant = interpret(string, sheet['Participant'])
                if not participant:
                    participant = string
                    warnNew = True
                filter = filter + [participant]
                sheet = act_points_add(participant, value, "tier", sheet)
                if s != operands - 2:
                    if operands - 2 == 2:
                        participants = participants + participant + " "
                    else:
                        participants = participants + participant + ", "
                else:
                    participants = participants + "and " + participant
            io_points_save(sheet)
            content2 = rng(["Nice"]) + ", " + participants + \
                " each got " + str(value) + " tiers."
            if warnNew:
                content2 = content2 + "\n\n⚠️ You added a new helmper!"
                warnNew = False
            content3 = "```" + \
                str(act_points_show(filter=list(dict.fromkeys(filter)))) + "```"
            content = [content1, content2, content3]
        send = channel_respond(message, colour, content)
        return send
    # If not officer
    else:
        send = queue_add(message, parsed)
        return send

try:
    text_points = config["info"]["points"]
    text_points = re.sub("\n", "\n\t", text_points)
except:
    text_points = """
\t**Guild missions**: 1 point per 20 mil silver reward
\t**Attending guildbosses**: 2 points
\t**Participating in Guild League**: 3 points
\t**Winning in Guild League**: 4 points
\t**Depositing a [Guild] Steel Candidum Shell**: 10 points
"""

def points_points(message, parsed):
    colour = discord.Colour.greyple()
    content1 = command_echo(message)
    content2 = "Point values:" + text_points
    content = [content1, content2]
    send = channel_respond(message, colour, content)
    return send


def points_queue(message, parsed):
    colour = discord.Colour.greyple()
    content1 = command_echo(message)
    if len(parsed) == 1:
        queue = act_queue_show()
        entries = len(queue)
        if entries != 0:
            content2 = "The queue has " + str(entries) + " entries in it."
            content3 = "```" + str(queue) + "```"
            content = [content1, content2, content3]
        else:
            content2 = "The queue is currently empty."
            content = [content1, content2]
    elif (parsed[1] == "a" or parsed[1] == "approve"):
        queue = act_queue_show()
        if len(queue) > 0:
            requestor = queue.iloc[0, 0]
            request = queue.iloc[0, 1]
            time = queue.iloc[0, 2]
            global passthrough
            passthrough = True
            content_queued = act_queue_approve(message)
            passthrough = False
            queue = act_queue_show()
            content2 = "Approved request `" + request + \
                "` by " + requestor + " at " + time + "."
            if len(queue) > 0:
                content3 = "```" + str(queue) + "```"
                content = [content1, content2, content3]
            else:
                content = [content1, content2]
            content = content + content_queued
        else:
            content2 = "The queue is currently empty."
            content = [content1, content2]
    elif (parsed[1] == "d" or parsed[1] == "deny"):
        queue = act_queue_show()
        if len(queue) > 0:
            requestor = queue.iloc[0, 0]
            request = queue.iloc[0, 1]
            time = queue.iloc[0, 2]
            act_queue_deny()
            content2 = "Denied request `" + request + \
                "` by " + requestor + " at " + time + "."
            queue = act_queue_show()
            if len(queue) > 0:
                content3 = "```" + str(queue) + "```"
                content = [content1 + content2 + content3]
            else:
                content = [content1 + content2]
        else:
            content2 = "The queue is currently empty."
            content = [content1, content2]
    elif (parsed[1] == "q" or parsed[1] == "queue"):
        if len(parsed) < 4:
            content2 = "Problem with `queue queue`: not enough operands passed.\nUsage: " + \
                man("queue queue")
            content = [content1, content2]
        else:
            requestor = parsed[2]
            request = " ".join(parsed[3:])
            if re.search("^q|^queue", request):
                content2 = "Problem with `queue queue`: `queue` commands not allowed in the queue.\nUsage: " + \
                    man("queue queue")
                content = [content1, content2]
            else:
                act_queue_add(requestor, request)
                queue = act_queue_show()
                content2 = "Manually adding " + \
                    str(requestor) + "'s request `" + str(request) + "` to the queue."
                content3 = "```" + str(queue) + "```"
                content = [content1, content2, content3]
    elif (parsed[1] == "z" or parsed[1] == "undo"):
        if not os.path.exists(bak1_queue):
            content2 = "Cannot `queue undo`: no undos remaining."
            content = [content1, content2]
        else:
            act_queue_undo()
            queue = io_queue_load()
            if len(queue) > 0:
                lastmodified = max(queue['Time'])
                content2 = "Rolling back to queue as of " + str(lastmodified)
                content3 = "```" + str(queue) + "```"
                content = [content1, content2, content3]
            else:
                content2 = "Undid the last queue entry. It's empty now."
                content = [content1, content2]
    else:
        queue = act_queue_show()
        entries = len(queue)
        if entries != 0:
            content2 = "The queue has " + str(entries) + " entries in it."
            content3 = "```" + str(queue) + "```"
            content = [content1, content2, content3]
        else:
            content2 = "The queue is currently empty."
            content = [content1, content2]
    send = channel_respond(message, colour, content)
    return send


def points_rename(message, parsed):
    # Check officer
    if is_officer(message):
        colour = discord.Colour.teal()
        content1 = command_echo(message)
        # Check operands
        operands = len(parsed)
        if operands == 1 or operands > 3:
            content2 = "Problem with `rename`: expected at least one or two operands, got " + \
                str(operands - 1) + ".\nUsage: " + man("rename")
            content = [content1, content2]
        else:
            sheet = io_points_load()
            participants = list(dict.fromkeys(sheet['Participant']))
            participant1 = interpret(parsed[1], participants)
            # Check that participant1 exists
            if participant1 is None:
                content2 = "Problem with `rename`: couldn't find " + \
                    parsed[1] + ".\nUsage: " + man("rename")
                content = [content1, content2]
            # Do
            else:
                if participant1 in participants:
                    participants.remove(participant1)
                if operands == 2:
                    parsed.append(parsed[1])
                participant2 = interpret(parsed[2], participants)
                if participant2 is None:
                    participant2 = parsed[2]
                sheet = act_points_rename(participant1, participant2, sheet)
                io_points_save(sheet)
                content2 = "Replaced " + participant1 + " with " + participant2 + "."
                content3 = "```" + \
                    str(act_points_show(filter=[participant2])) + "```"
                content = [content1, content2, content3]
        send = channel_respond(message, colour, content)
    else:
        send = queue_add(message, parsed)
    return send


def points_reset(message, parsed):
    if is_officer(message):
        colour = discord.Colour.teal()
        content1 = command_echo(message)
        operands = len(parsed)
        if operands == 1:
            content2 = "Are you sure? This will wipe the sheet. Type `reset confirm` to confirm you want to do this."
            content = [content1, content2]
        elif parsed[1] == "confirm":
            sheet = io_points_load()
            participants = set(sheet[sheet['Value'] > 0]['Participant'])
            act_points_reset()
            # Check who the participants were on the old sheet and copy them to
            # the new sheet
            sheet = io_points_load()
            if len(participants) > 0:
                for p in participants:
                    sheet = act_points_new(p, sheet)
                io_points_save(sheet)
            content2 = "Wiped the sheet."
            content = [content1, content2]
        else:
            content2 = "Are you sure? This will wipe the sheet. Type `reset confirm` to confirm you want to do this."
            content = [content1, content2]
        send = channel_respond(message, colour, content)
        return send
    else:
        send = queue_add(message, parsed)
        return send


def points_set(message, parsed):
    # If officer
    if is_officer(message):
        colour = discord.Colour.magenta()
        content1 = command_echo(message)
        # Execute
        operands = len(parsed)
        if operands < 3:
            content2 = "Problem with `set`: too few operands.\nUsage: " + \
                man("set")
            content = [content1, content2]
        else:
            params = io_params_load()
            string = str(parsed[1])
            newvalue = parsed[2]
            param = interpret(string, list(params.keys()))
            if not param:
                params = pd.DataFrame.from_dict(params, orient='index')
                content2 = "Couldn't find any parameter matching " + \
                    str(string) + " so here are all of them."
                content3 = "```" + str(params) + "```"
                content = [content1, content2, content3]
            elif not re.search("^-*\\d+.*\\d*$", newvalue):
                content2 = "Problem with `set`: expected a numeric for `value`, got `" + \
                    str(newvalue) + "`.\nUsage: " + man("set")
                content = [content1, content2]
            else:
                newvalue = float(newvalue)
                oldvalue = params[param]
                params[param] = newvalue
                io_params_save(params)
                content2 = "Changed " + \
                    str(param) + " from " + str(oldvalue) + " to " + str(newvalue) + "."
                content = [content1, content2]
        send = channel_respond(message, colour, content)
        return send
    # If not officer
    else:
        send = queue_add(message, parsed)
        return send


def points_split(message, parsed):
    # If officer
    if is_officer(message):
        colour = discord.Colour.teal()
        content1 = command_echo(message)
        # Check inputs
        sheet = io_points_load()
        value = parsed[-1]
        operands = len(parsed)
        if operands < 3:
            content2 = "Problem with `split`: expected 3 or more operands, got " + \
                str(operands) + ".\nUsage: " + man("split")
            content = [content1, content2]
        elif not re.search("^-*\\d+\\.*\\d*$", value):
            content2 = "Problem with `split`: expected a number for points, got `" + \
                value + "`.\nUsage: " + man("split")
            content = [content1, content2]
        elif re.search("^nan$", parsed[1], re.IGNORECASE) and interpret(parsed[1], sheet['Participant']) is None:
            content2 = "Problem with `add`: forbidden value passed, `nan`.\nUsage: " + \
                man("add")
            content = [content1, content2]
        # Execute
        elif operands == 3:
            string = parsed[1]
            value = float(value)
            participant = interpret(string, sheet['Participant'])
            warnNew = False
            if not participant:
                participant = string
                warnNew = True
            filter = [participant]
            sheet = act_points_add(participant, value, "point", sheet)
            io_points_save(sheet)
            content2 = rng(
                [
                    "Good stuff",
                    "Gerat",
                    "Superb",
                    "Well done",
                    "Much thank",
                    "Hekaru yeah",
                    "Noice"]) + ", " + str(value) + " points were given to " + participant + "."
            if warnNew:
                content2 = content2 + "\n\n⚠️ You added a new helmper!"
                warnNew = False
            content3 = "```" + \
                str(act_points_show(filter=list(dict.fromkeys(filter)))) + "```"
            content = [content1, content2, content3]
        else:
            participants = ""
            divvy = min(operands - 2, 3)
            value = np.around(float(value) / divvy, 1)
            warnNew = False
            filter = []
            for s in list(range(1, operands - 1)):
                string = parsed[s]
                participant = interpret(string, sheet['Participant'])
                if not participant:
                    participant = string
                    warnNew = True
                filter = filter + [participant]
                sheet = act_points_add(participant, value, "point", sheet)
                if s != operands - 2:
                    if operands - 2 == 2:
                        participants = participants + participant + " "
                    else:
                        participants = participants + participant + ", "
                else:
                    participants = participants + "and " + participant
            io_points_save(sheet)
            content2 = rng(
                [
                    "Noice effort",
                    "Everyone is best",
                    "Good job, crew",
                    "Well done everyone",
                    "Guildies% much",
                    "Stonks",
                    "Such activity"]) + ", " + participants + " each got " + str(value) + " points."
            if warnNew:
                content2 = content2 + "\n\n⚠️ You added a new helmper!"
                warnNew = False
            content3 = "```" + \
                str(act_points_show(filter=list(dict.fromkeys(filter)))) + "```"
            content = [content1, content2, content3]
        send = channel_respond(message, colour, content)
        return send
    # If not officer
    else:
        send = queue_add(message, parsed)
        return send


def points_tail(message, parsed):
    colour = discord.Colour.teal()
    content1 = command_echo(message)
    # Check inputs
    operands = len(parsed)
    if operands < 2:
        lines = 6
    elif re.search("^\\d+$", parsed[1]):
        lines = int(parsed[1])
    else:
        lines = 6
    # Execute
    rows = min(16, lines)
    sheet = io_points_load()
    sli = sheet.iloc[-int(rows):]
    cols = ['Participant', 'Value', 'Type', 'Date']
    sli = sli[cols]
    content2 = "Here are the last " + str(rows) + " lines of the sheet."
    content3 = "```" + str(sli) + "```"
    content = [content1, content2, content3]
    send = channel_respond(message, colour, content)
    return send


def points_tiers(message, parsed):
    colour = discord.Colour.teal()
    content1 = command_echo(message)
    tiers = act_points_tiers()
    content2 = "Here's how many points you need for each tier at the moment."
    content3 = "```" + str(tiers) + "```"
    content = [content1, content2, content3]
    send = channel_respond(message, colour, content)
    return send


def points_show(message, parsed):
    colour = discord.Colour.teal()
    operands = len(parsed)
    if operands > 1:
        if parsed[1] in ['Participant', 'Points', 'Tier']:
            col = parsed[1]
        else:
            col = "Tier"
    else:
        col = "Tier"
    content1 = command_echo(message)
    content2 = "Here's how things stand."
    content3 = "```" + str(act_points_show(col)) + "```"
    content = [content1, content2, content3]
    send = channel_respond(message, colour, content)
    return send


def points_payout(message, parsed):
    colour = discord.Colour.teal()
    content1 = command_echo(message)
    content2 = "Here's the board in alphabetical order. " + rng(
        [
            "Thankswali for stonksing us!",
            "Wali is great.",
            "Hope this helmps!",
            "Congratulations to everyone!",
            "Thanks for another successful board!",
            "Time to evade tax.",
            "Np enjoy!"])
    content3 = "```" + str(act_points_show("Participant")) + "```"
    content = [content1, content2, content3]
    send = channel_respond(message, colour, content)
    return send


def points_whois(message, parsed):
    colour = discord.Colour.teal()
    content1 = command_echo(message)
    # Check inputs
    operands = len(parsed)
    if operands < 2:
        string = message.author
        content2 = "You're " + str(string) + "."
        content = [content1, content2]
    else:
        string = parsed[1]
        sheet = io_points_load()
        participant = interpret(string, sheet['Participant'])
        if participant is not None:
            content2 = "I recognised " + \
                str(string) + " as " + str(participant) + "."
            content = [content1, content2]
        else:
            content2 = "I couldn't guess who " + str(string) + " is."
            content = [content1, content2]
    send = channel_respond(message, colour, content)
    return send


def points_undo(message, parsed):
    # If officer
    if is_officer(message):
        colour = discord.Colour.teal()
        content1 = command_echo(message)
        # Check state
        if not os.path.exists(bak1_points):
            content2 = "Problem with `undo`: No more undos available."
            content = [content1, content2]
        else:
            act_points_undo()
            sheet = io_points_load()
            lastmodified = max(sheet['Date'])
            content2 = "Rolling back to the sheet as of " + str(lastmodified)
            content3 = "```" + str(act_points_show()) + "```"
            content = [content1, content2, content3]
    # If not officer
    else:
        colour = discord.Colour.greyple()
        content1 = command_echo(message)
        if not os.path.exists(bak1_queue):
            content2 = "Cannot `undo`: no queue undos remaining."
            content = [content1, content2]
        else:
            act_queue_undo()
            queue = io_queue_load()
            if len(queue) > 0:
                lastmodified = max(queue['Time'])
                content2 = "Rolling back to queue as of " + str(lastmodified)
                content3 = "```" + str(queue) + "```"
                content = [content1, content2, content3]
            else:
                content2 = "Undid the last queue entry. It's empty now."
                content = [content1, content2]
    send = channel_respond(message, colour, content)
    return send


def points_uwu(message, parsed):
    colour = discord.Colour.red()
    content = """
    ```
⡆⣐⢕⢕⢕⢕⢕⢕⢕⢕⠅⢗⢕⢕⢕⢕⢕⢕⢕⠕⠕⢕⢕⢕⢕⢕⢕⢕⢕⢕
⢐⢕⢕⢕⢕⢕⣕⢕⢕⠕⠁⢕⢕⢕⢕⢕⢕⢕⢕⠅⡄⢕⢕⢕⢕⢕⢕⢕⢕⢕
⢕⢕⢕⢕⢕⠅⢗⢕⠕⣠⠄⣗⢕⢕⠕⢕⢕⢕⠕⢠⣿⠐⢕⢕⢕⠑⢕⢕⠵⢕
⢕⢕⢕⢕⠁⢜⠕⢁⣴⣿⡇⢓⢕⢵⢐⢕⢕⠕⢁⣾⢿⣧⠑⢕⢕⠄⢑⢕⠅⢕
⢕⢕⠵⢁⠔⢁⣤⣤⣶⣶⣶⡐⣕⢽⠐⢕⠕⣡⣾⣶⣶⣶⣤⡁⢓⢕⠄⢑⢅⢑
⠍⣧⠄⣶⣾⣿⣿⣿⣿⣿⣿⣷⣔⢕⢄⢡⣾⣿⣿⣿⣿⣿⣿⣿⣦⡑⢕⢤⠱⢐
⢠⢕⠅⣾⣿⠋⢿⣿⣿⣿⠉⣿⣿⣷⣦⣶⣽⣿⣿⠈⣿⣿⣿⣿⠏⢹⣷⣷⡅⢐
⣔⢕⢥⢻⣿⡀⠈⠛⠛⠁⢠⣿⣿⣿⣿⣿⣿⣿⣿⡀⠈⠛⠛⠁⠄⣼⣿⣿⡇⢔
⢕⢕⢽⢸⢟⢟⢖⢖⢤⣶⡟⢻⣿⡿⠻⣿⣿⡟⢀⣿⣦⢤⢤⢔⢞⢿⢿⣿⠁⢕
⢕⢕⠅⣐⢕⢕⢕⢕⢕⣿⣿⡄⠛⢀⣦⠈⠛⢁⣼⣿⢗⢕⢕⢕⢕⢕⢕⡏⣘⢕
⢕⢕⠅⢓⣕⣕⣕⣕⣵⣿⣿⣿⣾⣿⣿⣿⣿⣿⣿⣿⣷⣕⢕⢕⢕⢕⡵⢀⢕⢕
⢑⢕⠃⡈⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢃⢕⢕⢕
⣆⢕⠄⢱⣄⠛⢿⣿GOOD⣿⣿⣿⣿⣿⣿⣿LUCK⣿⣿⣿⠿⢁⢕⢕⠕⠅
⣿⣦⡀⣿⣿⣷⣶⣬⣍⣛⣛⣛⡛⠿⠿⠿⠛⠛⢛⣛⣉⣭⣤⣂⢜⠕⢑⣡⣴⣿
```
    """
    send = channel_respond(message, colour, [content])
    return send


def points_syntax(message, parsed):
    colour = discord.Colour.teal()
    content1 = command_echo(message)
    content2 = """
        Possible Pointinator commands:
        `add`, `split`, `offset`, `new`, `rename`, `delete`, `undo`, `show`, `payout`, `queue`, `reset`, `tail`, `tiers`, `whois`, `set`, `get`, `edit`, `points`, `help`, `info`, `chat`.\n
        Issue `help` for detailed usage instructions.
        """
    content = [content1, content2]
    send = channel_respond(message, colour, content)
    return send


# %% Queue function
def queue_add(message, parsed):
    colour = discord.Colour.greyple()
    content1 = command_echo(message)
    requestor = str(message.author)
    request = str(message.content)
    if re.search("^q|^queue", request):
        content2 = "Problem with `queue`: `queue` commands not allowed in the queue."
        content = [content1, content2]
    else:
        act_queue_add(requestor, request)
        content2 = rng(["Thanks", "Nice one", "Gotcha", "Understood", "Thanks for the helmp"]) + \
            ", your request `" + request + "` has been sent to officers for approval."
        content3 = "```" + str(act_queue_show()) + "```"
        content = [content1, content2, content3]
    send = channel_respond(message, colour, content)
    return send

# %% Roles functions


def roles_give(message, parsed):
    colour = discord.Colour.greyple()
    # Check inputs
    operands = len(parsed)
    sends = []

    if operands < 2:
        content1 = "Possible commands: `give`, `remove`. Possible roles: " + \
            ", ".join(roles) + ". "
        content = [content1]
    else:
        content = []
        uniqueCommands = list(set(parsed[1:operands]))
        uniqueRoles = len(
            list(set([interpret(string, roles) for string in uniqueCommands])))
        parsedRoles = []

        if (uniqueRoles > 1):
            content = ["Multiple roles"]

        for i in range(0, len(uniqueCommands)):
            string = uniqueCommands[i]
            role = interpret(string, roles)

            if role:
                if (role in parsedRoles):
                    continue

                parsedRoles.append(role)
                roleid = discord.utils.get(message.guild.roles, name=role)
                if roleid:
                    send = [act_roles_give(message, roleid)]
                    sends = sends + send
                    content1 = "Adding you to " + role + ". "
                    content.append(content1)
                else:
                    content1 = "Role " + string + \
                        " not found. Possible roles: " + ", ".join(roles) + ". "
                    content.append(content1)
            else:
                content1 = "Role " + string + \
                    " not found. Possible roles: " + ", ".join(roles) + ". "
                content.append(content1)

    send = [channel_respond(message, colour, content)]
    sends = sends + send
    return sends


def roles_remove(message, parsed):
    colour = discord.Colour.greyple()
    # Check inputs
    operands = len(parsed)
    sends = []

    if operands < 2:
        content1 = "Possible commands: `give`, `remove`. Possible roles: " + \
            ", ".join(roles) + ". "
        content = [content1]
    else:
        content = []
        uniqueCommands = list(set(parsed[1:operands]))
        uniqueRoles = len(
            list(set([interpret(string, roles) for string in uniqueCommands])))
        parsedRoles = []

        if (uniqueRoles > 1):
            content = ["Multiple roles"]

        for i in range(0, len(uniqueCommands)):
            string = uniqueCommands[i]
            role = interpret(string, roles)

            if role:
                if (role in parsedRoles):
                    continue

                parsedRoles.append(role)
                roleid = discord.utils.get(message.guild.roles, name=role)
                if roleid:
                    send = [act_roles_remove(message, roleid)]
                    sends = sends + send
                    content1 = "Removing you from " + role + ". "
                    content.append(content1)
                else:
                    content1 = "Role " + string + \
                        " not found. Possible roles: " + ", ".join(roles) + ". "
                    content.append(content1)
            else:
                content1 = "Role " + string + \
                    " not found. Possible roles: " + ", ".join(roles) + ". "
                content.append(content1)

    send = [channel_respond(message, colour, content)]
    sends = sends + send
    return sends


def roles_syntax(message, parsed):
    colour = discord.Colour.greyple()
    sends = []
    content1 = "Possible commands: `give`, `remove`. Possible roles: " + \
        ", ".join(roles)
    content = [content1]
    send = [channel_respond(message, colour, content)]
    sends = sends + send
    return sends

# %% #points channel function selector


def points_channel(message, parsed):
    keyword = parsed[0].lower()
    match keyword:
        case "a" | "add":
            send = points_add(message, parsed)
        case "c" | "chat":
            send = points_chat(message, parsed)
        case "del" | "delete":
            send = points_delete(message, parsed)
        case "edit":
            send = points_edit(message, parsed)
        case "get":
            send = points_get(message, parsed)
        case "h" | "help":
            send = points_man(message, parsed)
        case "i" | "info":
            send = points_info(message, parsed)
        case "n" | "new":
            send = points_new(message, parsed)
        case "o" | "offset":
            send = points_offset(message, parsed)
        case "points":
            send = points_points(message, parsed)
        case "p" | "payout":
            send = points_payout(message, parsed)
        case "q" | "queue":
            send = points_queue(message, parsed)
        case "ren" | "rename":
            send = points_rename(message, parsed)
        case "r" | "reset":
            send = points_reset(message, parsed)
        case "s" | "split":
            send = points_split(message, parsed)
        case "t" | "tail":
            send = points_tail(message, parsed)
        case "tiers":
            send = points_tiers(message, parsed)
        case "set":
            send = points_set(message, parsed)
        case "sh" | "show":
            send = points_show(message, parsed)
        case "whois":
            send = points_whois(message, parsed)
        case "z" | "undo":
            send = points_undo(message, parsed)
        case "uwu":
            send = points_uwu(message, parsed)
        case _:
            send = points_syntax(message, parsed)
    return send

# %% #roles channel function selector


def roles_channel(message, parsed):
    keyword = parsed[0].lower()
    if (keyword == "give"):
        send = roles_give(message, parsed)
    elif (keyword == "remove"):
        send = roles_remove(message, parsed)
    else:
        send = roles_syntax(message, parsed)
    return send

# %% Discord


intents = discord.Intents(
    # auto_moderation=True,
    # auto_moderation_configuration=True,
    # auto_moderation_execution=True,
    # bans=True,
    # dm_messages=True,
    # dm_reactions=True,
    # dm_typing=True,
    # emojis=True,
    # emojis_and_stickers=True,
    guild_messages=True,
    # guild_reactions=True,
    # guild_scheduled_events=True,
    # guild_typing=True,
    guilds=True,
    # integrations=True,
    # invites=True,
    # members=True,
    message_content=True,
    messages=True,
    # presences=True,
    # reactions=True,
    # typing=True,
    # voice_states=True,
    # webhooks=True,
)

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    # inform ready in console
    print('We have logged in as {0.user}'.format(client))


@client.event
# with embeds
async def on_message(message):
    # don't respond to self
    if (message.author.bot):
        return
    # don't respond to system messages
    if (message.content == ""):
        return

    # get the discord message and interpret it
    command = message.content
    parsed = re.split("\\s+", command)

    if isinstance(message.channel, discord.DMChannel):
        # DMs to the bot are interpreted as control commands
        await control_command(message, parsed)
        return

    # don't chat in the wrong channels
    if (str(message.channel) == channel_points):
        send = points_channel(message, parsed)
        await send
    elif (str(message.channel) == channel_roles):
        send = roles_channel(message, parsed)
        for s in send:
            await s

# %% Execution

parser = argparse.ArgumentParser()
parser.add_argument("-o", "--workdir", help="Path to working directory.")
parser.add_argument(
    "-d",
    "--dev",
    action='store_true',
    default=False,
    help="Run in developer mode.")
args = parser.parse_args()

workdir = Path(config["files"]["workdir"])

if not workdir.is_absolute():
    workdir = program_path / config["files"]["workdir"]

if args.workdir is not None:
    # override static configuration
    workdir = Path(args.workdir)

    if not workdir.is_absolute():
        workdir = program_path / args.workdir

# create working directory if it doesn't exist
workdir.mkdir(parents=True, exist_ok=True)

# Interactive mode
if not (hasattr(main, "__file__")):
    args.workdir = ""
    # Test vector
    message = discord.Message
    message.channel = ""
    member = discord.Member
    member.name = ""
    member.roles = ""
    member.bot = False
    message.author = member
    message.content = "show"

fconf = config["files"]

file_points = workdir / fconf["file_points"]
bak1_points = workdir / fconf["bak1_points"]
bak2_points = workdir / fconf["bak2_points"]
bak3_points = workdir / fconf["bak3_points"]
file_queue = workdir / fconf["file_queue"]
bak1_queue = workdir / fconf["bak1_queue"]
bak2_queue = workdir / fconf["bak2_queue"]
bak3_queue = workdir / fconf["bak3_queue"]
file_params = workdir / fconf["file_params"]
file_log = workdir / fconf["file_log"]

channel_points = config["channels"]["points"]
channel_roles = config["channels"]["roles"]

if (args.dev):
    channel_points = channel_points + "-dev"
    channel_roles = channel_roles + "-dev"

# set this flag when you want commands to be processed silently
passthrough = False

roleset = config["roles"]["roleset"]
roles = config["roles"][roleset]

roles = [role.strip() for role in roles.split('\n') if role.strip()]

if (os.path.exists(file_params)):
    params = io_params_load()
else:
    params = {
        # number of points to guarantee a max tier payout
        'cap': 150,
        # maximum tier attainable by scoring points only
        'tcap': 10,
        # maximum tier attainable after accounting for offsets
        'thardcap': 10,
        # 1: "logarithmic" or 2: "logistic"
        'method': 1,
        # shape of the logistic curve, bigger values mean steeper
        'difficulty': 0,
    }
    io_params_save(params)

if (os.path.exists(file_queue)):
    queue = io_queue_load()
else:
    queue = {
        'Requestor': [],
        'Request': [],
        'Time': []
    }
    queue = pd.DataFrame(queue)
    io_queue_save(queue)


# make a new sheet if it doesn't exist
if (not os.path.exists(file_points)):
    act_points_reset()

# logging
handler = logging.FileHandler(filename=file_log, encoding='utf-8', mode='w')

# run bot
client.run(secret_key, reconnect=True, log_handler=handler)
