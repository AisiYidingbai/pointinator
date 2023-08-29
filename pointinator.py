#!/bin/env python

# -*- coding: utf-8 -*-

"""
Created on Mon Jan 31 15:42:10 2022

@author: AisiYidingbai
"""

ver = "2.1"
updated = "29-Aug-2023"

# Import packages
import os                         # File I/O
import re                         # Text matching
import json                       # File I/O
import logging                    # Logging
from math import e                # Constant e
import numpy as np                # Math
import pandas as pd               # Dataframes
from datetime import datetime     # Date and time
import argparse                   # Commandline interface
import discord                    # Discord
import __main__ as main

#%% Common I/O functions
def io_points_load():
    x = pd.read_csv(file_points)
    x = x[['Participant', 'Value', 'Type', 'Date']]
    return x

def io_queue_load():
    x = pd.read_csv(file_queue)
    x = x[['Requestor', 'Request', 'Time']]
    return x

def io_drill_load():
    x = pd.read_csv(file_drill)
    x = x[['Participant', 'Item', 'Amount', 'Date']]
    return x

def io_params_load():
    with open(file_params) as f:
        x = json.load(f)
    return x

def io_points_save(x):
    if(os.path.exists(bak3_points)): os.remove(bak3_points)                    # Rotate existing backups
    if(os.path.exists(bak2_points)): os.rename(bak2_points, bak3_points)
    if(os.path.exists(bak1_points)): os.rename(bak1_points, bak2_points)
    if(os.path.exists(file_points)): os.rename(file_points, bak1_points)
    x.to_csv(file_points)                                                      # Write to file
    
def io_queue_save(x):
    if(os.path.exists(bak3_queue)): os.remove(bak3_queue)                      # Rotate existing backups
    if(os.path.exists(bak2_queue)): os.rename(bak2_queue, bak3_queue)
    if(os.path.exists(bak1_queue)): os.rename(bak1_queue, bak2_queue)
    if(os.path.exists(file_queue)): os.rename(file_queue, bak1_queue)
    x.to_csv(file_queue)                                                       # Write to file
    
def io_drill_save(x):
    if(os.path.exists(bak3_drill)): os.remove(bak3_drill)                      # Rotate existing backups
    if(os.path.exists(bak2_drill)): os.rename(bak2_drill, bak3_drill)
    if(os.path.exists(bak1_drill)): os.rename(bak1_drill, bak2_drill)
    if(os.path.exists(file_drill)): os.rename(file_drill, bak1_drill)
    x.to_csv(file_drill)                                                       # Write to file
    
def io_params_save(x):
    with open(file_params, 'w') as f:
        json.dump(x, f, indent = 4)
    

#%% Common helper functions
def interpret(x, y):                                                           # Find an exact or partial match for string x within list y. Return None if not found.
    r = None
    y = set(y)
    if (r is None):
        for i in y:                                                            # x exists in y
            if(x == i): r = i; break
    if (r is None):
        for i in y:                                                            # Element in y starts with x
            if(re.search("^" + x, i, re.IGNORECASE)): r = i; break
    if (r is None):
        for i in y:                                                            # Element in y ends with x
            if(re.search(x + "$", i, re.IGNORECASE)): r = i; break
    if (r is None):
        for i in y:                                                            # Element in y contains x
            if(re.search(x, i, re.IGNORECASE)): r = i; break
    if (r is None):
        for i in y:                                                            # Element in y contains all the characters in x in order
            if(re.search(re.sub("(.)", ".*\\1", x) + ".*", i, re.IGNORECASE)): r = i; break
    return r

def is_officer(x):                                                             # Check if the sender of message x has the Officers role
    r = "Officers" in str(x.author.roles)
    return r

def man(x):
    if (x == "add"):              r = "`a <p ...> <n>`: **Add** *n* points to *p*articipants."
    if (x == "chat"):             r = "`c <...>`: Send a **chat** message in the #points channel without Pointinator interpreting it as a command."
    if (x == "delete"):           r = "`del <p ...>`: **Delete** *p*articipants."
    if (x == "edit"):             r = "`edit <row> <column> <value>`: **Edit** the sheet at *row* and *column* to *value*. *column* must be one of `Participant`, `Type`, or `Value`."
    if (x == "edit value"):       r = "`edit <row> Participant <value>`: **Edit** the *row*th *Value* in the sheet to *value*. *value* must be a number."
    if (x == "edit type"):        r = "`edit <row> Type <value>`: **Edit** the *row*th *Type* to *value*. *value* must be one of `point` or `tier`."
    if (x == "help"):             r = "`help`: Show **help** on Pointinator syntax."
    if (x == "info"):             r = "`info`: Show **info** on Pointinator."
    if (x == "get"):              r = "`get <param>`: **Get** a Pointinator *param*eter."
    if (x == "new"):              r = "`n <p ...>`: Add **new** *p*articipants."
    if (x == "offset"):           r = "`o <p ...> <n>`: **Offset** *n* tiers to *p*articipants."
    if (x == "points"):           r = "`points`: Show **point** values."
    if (x == "reset"):            r = "`r`: **Reset** the sheet."
    if (x == "set"):              r = "`set <param> <value>`: **Set** a Pointinator *param*eter to *value*."
    if (x == "show"):             r = "`show`: **Show** the current sheet."
    if (x == "split"):            r = "`s <p ...> <n>`: **Split** *n* points between *p*articipants."
    if (x == "tail"):             r = "`tail <n>`: **Tail** the last *n* sheet actions."
    if (x == "tiers"):            r = "`tiers`: Show the current point requirements per **tier**."
    if (x == "undo"):             r = "`z`: **Undo** the last change."
    if (x == "whois"):            r = "`whois <nickname>`: See if I can convert a *nickname* to a participant already on the board."
    
    if (x == "drill add"):        r = "`dr a <p> <n> <mat>`: **Add** *n* drill *mat*erials for participant *p*."
    if (x == "drill show"):       r = "`dr show`: **Show** a comprehensive report of drill materials."
    if (x == "drill summary"):    r = "`dr summary`: Show a **summary** of drill materials."
    if (x == "drill progress"):   r = "`dr progress`: Show a summary of drill **progress**."
    if (x == "drill undo"):       r = "`dr z`: **Undo** the last change to the drill sheet."
    if (x == "drill tail"):       r = "`dr tail <n>`: **Tail** the last *n* actions of the drill sheet."
    if (x == "drill reset"):      r = "`dr r`: **Reset** the drill sheet."
    if (x == "drill edit"):       r = "`dr edit <row> <column> <value>`: **Edit** the drill sheet at *row* and *column* to *value*. *column* must be one of `Item`, `Participant`, or `Amount`."
    
    if (x == "queue"):            r = "`q`: Show the **queue**."
    if (x == "queue approve"):    r = "`q a`: **Approve** the request at the top of the queue."
    if (x == "queue deny"):       r = "`q d`: **Deny** the request at the top of the queue."
    if (x == "queue queue"):      r = "`q q <requestor> <request>`: Manually add an entry to the **queue** with *requestor* and *request*."
    if (x == "queue undo"):       r = "`q z`: **Undo** the last change to the queue."
    return r

def rng(x):
    r = x[int(np.floor(np.random.uniform(low = 0, high = len(x))))]
    return r

def command_echo(x):
    r = "*Your command:  *`" + re.sub("[*`]", "", x.content) + "`" + "\n"
    return r

#%% Actions: points
def act_points_add(participant, value, kind, sheet):
    sheet = sheet.loc[sheet['Participant'] != "No-one yet"]                        # delete the initialising entry for new sheets if it is there
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")                         # get the current date and time
    sheet = pd.concat([sheet, pd.DataFrame({'Participant':[participant], 'Value':[value], 'Type':[str(kind)], 'Date':[date]})]) # add an entry to the sheet
    return sheet

def act_points_delete(participant, sheet):
    sheet = sheet.loc[sheet['Participant'] != participant]
    return sheet

def act_points_edit(row, col, newvalue):
    sheet = io_points_load()
    row = int(row)
    sheet.at[row,col] = newvalue
    io_points_save(sheet)
    return

def act_points_new(participant, sheet):
    sheet = sheet.loc[sheet['Participant'] != "No-one yet"]                        # delete the initialising entry for new sheets if it is there
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")                         # get the current date and time
    sheet = pd.concat([sheet, pd.DataFrame({'Participant':[participant], 'Value':[0], 'Type':["point"], 'Date':[date]})]) # add an entry to the sheet
    return sheet

def act_points_reset():
    sheet = pd.DataFrame([], columns = ['Participant', 'Value', 'Type', 'Date'])
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    sheet = pd.concat([sheet, pd.DataFrame({'Participant':["No-one yet"], 'Value':[0], 'Type':["point"], 'Date':[date]})])
    io_points_save(sheet)
    return

def act_points_show():
    sheet = io_points_load()
    points = sheet.loc[sheet['Type'] == 'point'].groupby('Participant').sum('Value')
    points['LogPoints'] = np.log(1 + points['Value'])
    highscore = max(points['Value']) # the current highscore on the board
    cap = int(params['cap']) # the cap
    logt11 = min(np.log(highscore + 1), np.log(cap + 1) * 10/9) # select a logT11 to use for tier calculation based on the highscore and cap
    interval = logt11 / int(params['tcap']) # calculate the interval between tiers measured in log points
    points['Tier'] = np.ceil(points['LogPoints'] / interval) + 1 # calculate log points
    #logcurrentmax = max(points['LogPoints'])                                               # 1. log(high score)
    #logcap = np.power(int(params['cap']), (int(params['tcap'])-1)/(int(params['tcap'])-2)) # 2. Calculated from cap
    #logt11 = min(logcurrentmax, logcap)
    #points['Tier'] = np.ceil(points['LogPoints'] / logt11 * (params['tcap']-1)) + 1   # calculate the current tiers
    offsets = sheet.loc[sheet['Type'] == 'tier'].groupby('Participant').sum('Value')['Value']                                 # pivot the sheet for tiers
    board = points.join(offsets, on = "Participant", how = "outer", rsuffix = ".tier")  # join tiers to point sheet
    if board.index.name is None: board = board.set_index('Participant')
    board['Value.tier'][np.isnan(board['Value.tier'])] = 0 # set zero tiers for participants with no offsets
    board['Value'][np.isnan(board['Value'])] = 0 # set zero points for participants with yes offsets but no points
    board['Tier'][np.isnan(board['Tier'])] = 1 # set 1 tier for participants with yes offsets but no points
    board['Tier'] = np.minimum(np.minimum(board['Tier'], params['tcap']) + board['Value.tier'], params['thardcap']) # don't let the tier exceed the max
    board = board.sort_values(['Value'], ascending = False)             # sort the sheet by descending points
    board = board.sort_values(['Tier'], ascending = False)               # sort the sheet by descending tiers
    board['Points'] = board['Value']
    cols = ['Points', 'Tier']
    board = board[cols]
    return board

def act_points_tiers():
    sheet = io_points_load()
    points = sheet.loc[sheet['Type'] == 'point'].groupby('Participant').sum('Value')
    points['LogPoints'] = np.log(1 + points['Value'])
    #logcurrentmax = max(points['LogPoints'])
    highscore = max(points['Value']) # the current highscore on the board
    cap = int(params['cap']) # the cap
    logt11 = min(np.log(highscore + 1), np.log(cap + 1) * 10/9) # select a logT11 to use for tier calculation based on the highscore and cap
    interval = logt11 / int(params['tcap']) # calculate the interval between tiers measured in log points
    currenttiers = list()
    tierpoints = list()
    for i in range((int(params['tcap'])), 0, -1):
        currenttiers.append("T" + str(i))
        tierpoints.append(np.ceil(np.power(e, (i - 1) * interval) - 1))
        #tierpoints.append(np.around(np.power(np.power(e,logcurrentmax),(i/(params['tcap']-1))),1))  # use meth to determine the T1-10 requirements
    tiers = pd.DataFrame({'Tier':currenttiers, 'Value':tierpoints})
    tiers = tiers.set_index('Tier')
    return tiers

def act_points_undo():
    os.remove(file_points)                                                         # delete the current sheet
    os.rename(bak1_points, file_points)                                                   # reinstate backup 1 as the current sheet
    if(os.path.exists(bak2_points)):
        os.rename(bak2_points, bak1_points)                                               # reinstate backup 2 as backup 1 if it exists
        if(os.path.exists(bak3_points)):
                os.rename(bak3_points, bak2_points)                                       # reinstate backup 3 as backup 2 if it exists
    return

#%% Actions: drill
def act_drill_add(participant, amount, material):
    drill = io_drill_load()
    drill = drill.loc[drill['Participant'] != "No-one yet"]      # delete the initialising entry for new sheets if it is there
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")                         # get the current date and time
    drill = pd.concat([drill, pd.DataFrame({'Participant':[participant], 'Amount':[amount], 'Item':[material], 'Date':[date]})]) # add an entry to the sheet
    io_drill_save(drill)
    return

def act_drill_reset():
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    drill = {'Participant':["dummy"] * 16,
                                    'Item':['Old Tree\'s Tear',
                                            'Elder Tree Plywood',
                                            'Palm Plywood',
                                            'Standardized Timber Square',
                                            'Black Stone Powder',
                                            'Earth\'s Tear',
                                            'Steel',
                                            'Vanadium Ingot',
                                            'Log',
                                            'Bronze Ingot',
                                            'Titanium Ingot',
                                            'Black Stone (Weapon)',
                                            'Black Stone (Armor)',
                                            'Powder of Flame',
                                            'Fire Horn',
                                            'Coal'],
                                    'Amount':[0] * 16,
                                    'Date':[date] * 16}
    drill = pd.DataFrame(drill)
    drill = pd.concat([drill, pd.DataFrame({'Participant':["No-one yet"], 'Item':["Nothing"], 'Amount':[0], 'Date':[date]})])
    io_drill_save(drill)
    return

def act_drill_show():
    drill = io_drill_load()
    params = io_params_load()
    drill = drill.loc[drill['Participant'] != "dummy"]           # data has dummy rows with all mats but zero amount and assigned to no-one. remove
    drill = drill.groupby(['Participant', 'Item']).sum('Amount')      # group by participant and item, show a sum of the amount
    drill = drill.reset_index()
    silver = []                                                                 # calculate silver
    for i in range(len(drill)):
        item = drill.iloc[i,1]
        amount = drill.iloc[i,2]
        silver.append(amount * params[item] / 1000000)                          # using the parameters file, and then calculate millions of silver
    drill['Silver (M)'] = silver
    drill['Silver (M)'] = np.round(drill['Silver (M)'], 1)            # round to 1 d.p.
    drill = drill.groupby(['Participant', 'Item']).sum(['Silver'])
    return drill

def act_drill_summary():
    drill = act_drill_show()
    drill = drill.reset_index()
    drill['Points'] = drill['Silver (M)'] / 2
    drill['Points'] = drill['Silver (M)'] / 2
    drill['Points'] = np.round(drill['Points'], 1)
    drill = drill.groupby('Participant').sum(['Silver', 'Points'])
    drill = drill.sort_values('Silver (M)', ascending = False)
    return drill

def act_drill_progress():
    drill = act_drill_show()
    drill = drill.groupby(['Item']).sum('Amount')                  # group by item only, show a sum of the total amount contributed so far
    drill = drill.reset_index()
    drill_totals = [                                                            # make an array of mats and requirements
        ['(multiple)','Old Tree\'s Tear',200],
        ['Support','Elder Tree Plywood',100],
        ['Support','Palm Plywood',100],
        ['Support','Standardized Timber Square',100],
        ['(multiple)','Black Stone Powder',4000],
        ['(multiple)','Earth\'s Tear',200],
        ['(multiple)','Steel',200],
        ['Shaft','Vanadium Ingot',100],
        ['Grip','Log',100],
        ['Grip','Bronze Ingot',100],
        ['Pin','Titanium Ingot',100],
        ['Fuel','Black Stone (Weapon)',5000],
        ['Fuel','Black Stone (Armor)',5000],
        ['Fuel','Powder of Flame',5000],
        ['Fuel','Fire Horn',5000],
        ['Fuel','Coal',5000]
        ]
    drill_totals = pd.DataFrame(drill_totals, columns = ['Part', 'Item', 'Required'])
    drill = drill.merge(drill_totals, on = "Item", how = "outer")# merge arrays
    drill = drill.sort_values("Part")
    drill['Amount'] = drill['Amount'].fillna(0)
    drill = drill.set_index(['Part','Item'])
    return drill

def act_drill_undo():
    os.remove(file_drill)                                                         # delete the current sheet
    os.rename(bak1_drill, file_drill)                                                   # reinstate backup 1 as the current sheet
    if(os.path.exists(bak2_drill)):
        os.rename(bak2_drill, bak1_drill)                                               # reinstate backup 2 as backup 1 if it exists
        if(os.path.exists(bak3_drill)):
                os.rename(bak3_drill, bak2_drill)                                       # reinstate backup 3 as backup 2 if it exists
    return

#%% Actions: queue
def act_queue_add(requestor, request):
    queue = io_queue_load()
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    queue = pd.concat([queue, pd.DataFrame({'Requestor':[requestor], 'Request':[request], 'Time':[date]})])
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
    request = queue.iloc[0,1]
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
    os.remove(file_queue)                                                         # delete the current sheet
    os.rename(bak1_queue, file_queue)                                                   # reinstate backup 1 as the current sheet
    if(os.path.exists(bak2_queue)):
        os.rename(bak2_queue, bak1_queue)                                               # reinstate backup 2 as backup 1 if it exists
        if(os.path.exists(bak3_queue)):
                os.rename(bak3_queue, bak2_queue)                                       # reinstate backup 3 as backup 2 if it exists
    return

#%% Actions: role

def act_roles_give(message, roleid):
    send = message.author.add_roles(roleid)
    return send

def act_roles_remove(message, roleid):
    send = message.author.remove_roles(roleid)
    return send

#%% Common frontend functions
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
                embed = discord.Embed(title = content[0], color = colour)
                for i in list(range(1, len(content))): embed.add_field(name = "", value = content[i], inline=False)
                embed.set_footer(text = "by Yidingbai :)")
                send = message.channel.send(embed = embed)
        return send

#%% Points functions
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
            content2 = "Error in `add`: expected 3 or more operands, got " + str(operands) + ".\nUsage: " + man("add")
            content = [content1, content2]
        elif not re.search("^-*\d+\.*\d*$", value):
            content2 = "Error in `add`: expected a number for points, got `" + value + "`.\nUsage: " + man("add")
            content = [content1, content2]
        elif re.search("^nan$", parsed[1], re.IGNORECASE) and interpret(parsed[1], sheet['Participant']) is None:
            content2 = "Error in `add`: forbidden value passed, `nan`.\nUsage: " + man("add")
            content = [content1, content2]
        # Execute
        elif operands == 3:
            string = parsed[1]
            value = float(value)
            participant = interpret(string, sheet['Participant'])
            if not participant: participant = string
            sheet = act_points_add(participant, value, "point", sheet)
            io_points_save(sheet)
            content2 = rng(["Good stuff", "Gerat", "Superb", "Well done", "Much thank", "Hekaru yeah", "Noice"]) + ", " + str(value) + " points were given to " + participant + "."
            content3 = "```" + str(act_points_show()) + "```"
            content = [content1, content2, content3]
        else:
            participants = ""
            value = float(value)
            for s in list(range(1, operands-1)):
                string = parsed[s]
                participant = interpret(string, sheet['Participant'])
                if not participant: participant = string
                sheet = act_points_add(participant, value, "point", sheet)
                if s != operands-2:
                    if operands-2 == 2: participants = participants + participant + " "
                    else: participants = participants + participant + ", "
                else:                  participants = participants + "and " + participant
            io_points_save(sheet)
            content2 = rng(["Noice effort", "Everyone is best", "Good job, crew", "Well done everyone", "Guildies% much", "Stonks", "Such activity"]) + ", " + participants + " each got " + str(value) + " points."
            content3 = "```" + str(act_points_show()) + "```"
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
            content2 = "Error in `delete`: not enough operands passed.\nUsage: " + man("delete")
            content = [content1, content2]
        # Execute
        elif operands == 2:
            sheet = io_points_load()
            participant = interpret(parsed[1], sheet['Participant'])
            if participant:
                sheet = act_points_delete(participant, sheet)
                io_points_save(sheet)
                content2 = rng(["Removing from the board"]) + ", " + participant + "."
                content3 = "```" + str(act_points_show()) + "```"
                content = [content1, content2, content3]
            else:
                content2 = "Error in `delete`: could not find participant " + parsed[1] + ".\nUsage: " + man("delete")
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
                content2 = rng(["Removing from the board"]) + ", " + participants + "."
                content3 = "```" + str(act_points_show()) + "```"
                content = [content1, content2, content3]
            else:
                content2 = "Error in `delete`: could not find any of those participants.\nUsage: " + man("delete")
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
            content2 = "Error in `edit`: not enough operands passed.\nUsage: " + man("edit")
            content = [content1, content2]
        elif not re.search("^\d+$", parsed[1]):
            content2 = "Error in `edit`: expected numeric, got `" + str(parsed[1]) + "`.\nUsage: " + man("edit")
            content = [content1, content2]
        elif int(parsed[1]) > len(io_points_load()):
            content2 = "Error in `edit`: row number `" + str(parsed[1]) + "` cannot be greater than the number of rows in the sheet.\nUsage: " + man("edit")
            content = [content1, content2]
        elif parsed[2] not in ['Participant', 'Value', 'Type']:
            content2 = "Error in `edit`: expected valid column name, got `" + str(parsed[2]) + "`.\nUsage: " + man("edit")
            content = [content1, content2]
        elif parsed[2] == "Value" and not re.search("^-*\d+.*\d*$", parsed[3]):
            content2 = "Error in `edit`: trying to edit a `Value`, expected a numeric, got `" + str(parsed[2]) + "`.\nUsage: " + man("edit")
            content = [content1, content2]
        elif parsed[2] == "Type" and parsed[3] not in ['point', 'tier']:
            content2 = "Error in `edit`: trying to edit a `Type`, expected one of `point`, `tier`, got `" + str(parsed[3]) + "`.\nUsage: " + man("edit")
            content = [content1, content2]
        # Execute
        else:
            row = int(parsed[1])
            col = str(parsed[2])
            new = parsed[3]
            sheet = io_points_load()
            old = sheet.at[row,col]
            act_points_edit(row, col, new)
            sheet = io_points_load()
            sli = sheet.iloc[row:row+1]
            content2 = "Changed the " + col + " at row " + str(row) + " from " + str(old) + " to " + str(new)
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
    
    content2 = content2 + "\n\nDrill commands:"
    content2 = content2 + "\n\t" + man("drill add")
    content2 = content2 + "\n\t" + man("drill show")
    content2 = content2 + "\n\t" + man("drill summary")
    content2 = content2 + "\n\t" + man("drill progress")
    content2 = content2 + "\n\t" + man("drill undo")
    content2 = content2 + "\n\t" + man("drill tail")
    content2 = content2 + "\n\t" + man("drill reset")
    content2 = content2 + "\n\t" + man("drill edit")
    
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

def points_info(message, parsed):
    colour = discord.Colour.teal()
    content1 = command_echo(message)
    content2 = """
\tWelcome to **Pointinator**, a Discord bot that keeps track of points. This version """ + ver + """, last updated """ + updated + """.
\n\t*About*: Send commands by chatting in this channel. Send a command every time someone does something that earns points. Issue `points` to see qualifying activities.
\n\t*Usage*: Add points with `a <participant> <points>`. The *participant* can be a nickname if they're already on the board. For a full list of commands, issue `help`. For detailed usage, see the guide at <https://havefun.servegame.com/index.php/how-to-pointinate/>.
\n\t*Privileges*: Officers' commands will be executed by the bot immediately. Please type deliberately. If you're not an officer, then your command will be put in the queue for an officer to approve.
\n\t*Support*: Pointinator goes down for nightly maint around 4:00 GMT/BST. If it's down outside of those times, contact Aisi Yidingbai. Pointinator is open-source software available at <https://github.com/AisiYidingbai/pointinator>. 
"""
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
            content2 = "Error in `new`: not enough operands passed.\nUsage: " + man("new")
            content = [content1, content2]
        elif ("nan" in parsed[1:operands] or "NaN" in parsed[1:operands]):
            content2 = "Error in `new`: forbidden value passed: `nan`.\nUsage: " + man("new")
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
                if p != operands-1:
                    if operands-1 == 2: participants = participants + participant + " "
                    else: participants = participants + participant + ", "
                else:                  participants = participants + "and " + participant
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
            content2 = "Error in `offset`: expected 3 or more operands, got " + str(operands) + ".\nUsage: " + man("offset")
            content = [content1, content2]
        elif not re.search("^-*\d+$", value):
            content2 = "Error in `offset`: expected a number for tiers, got `" + value + "`.\nUsage: " + man("offset")
            content = [content1, content2]
        elif re.search("^nan$", parsed[1], re.IGNORECASE) and interpret(parsed[1], sheet['Participant']) is None:
            content2 = "Error in `offset`: forbidden value passed, `nan`.\nUsage: " + man("offset")
            content = [content1, content2]
        # Execute
        elif operands == 3:
            string = parsed[1]
            value = float(value)
            participant = interpret(string, sheet['Participant'])
            if not participant: participant = string
            sheet = act_points_add(participant, value, "tier", sheet)
            io_points_save(sheet)
            content2 = rng(["Gotcha"]) + ", " + str(value) + " tiers were given to " + participant + "."
            content3 = "```" + str(act_points_show()) + "```"
            content = [content1, content2, content3]
        else:
            participants = ""
            value = float(value)
            for s in list(range(1, operands-1)):
                string = parsed[s]
                participant = interpret(string, sheet['Participant'])
                if not participant: participant = string
                sheet = act_points_add(participant, value, "tier", sheet)
                if s != operands-2:
                    if operands-2 == 2: participants = participants + participant + " "
                    else: participants = participants + participant + ", "
                else:                  participants = participants + "and " + participant
            io_points_save(sheet)
            content2 = rng(["Nice"]) + ", " + participants + " each got " + str(value) + " tiers."
            content3 = "```" + str(act_points_show()) + "```"
            content = [content1, content2, content3]
        send = channel_respond(message, colour, content)
        return send
    # If not officer
    else:
        send = queue_add(message, parsed)
        return send

def points_points(message, parsed):
    colour = discord.Colour.greyple()
    content1 = command_echo(message)
    content2 = """
Point values:
\t**S guild missions**: 1 point
\t**M guild missions**: 2 points
\t**L guild missions**: 3 points
\t**XL guild missions**: 4 points
\t**Attending guild events**: 2 points
\t**Depositing a [Guild] Steel Candidum Shell**: 16 points
\t**Depositing [Guild] Drill materials**: see `drill` commands
"""
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
            requestor = queue.iloc[0,0]
            request = queue.iloc[0,1]
            time = queue.iloc[0,2]
            global passthrough
            passthrough = True
            content_queued = act_queue_approve(message)
            passthrough = False
            queue = act_queue_show()
            content2 = "Approved request `" + request + "` by " + requestor + " at " + time + "."
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
            requestor = queue.iloc[0,0]
            request = queue.iloc[0,1]
            time = queue.iloc[0,2]
            act_queue_deny()
            content2 = "Denied request `" + request + "` by " + requestor + " at " + time + "."
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
            content2 = "Error in `queue queue`: not enough operands passed.\nUsage: " + man("queue queue")
            content = [content1, content2]
        else:
            requestor = parsed[2]
            request = " ".join(parsed[3:])
            if re.search("^q|^queue", request):
                content2 = "Error in `queue queue`: `queue` commands not allowed in the queue.\nUsage: " + man("queue queue")
                content = [content1, content2]
            else:
                act_queue_add(requestor, request)
                queue = act_queue_show()
                content2 = "Manually adding " + str(requestor) + "'s request `" + str(request) + "` to the queue."
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

def points_reset(message, parsed):
    if is_officer(message):
        colour = discord.Colour.teal()
        content1 = command_echo(message)
        operands = len(parsed)
        if operands == 1:
            content2 = "Are you sure? This will wipe the sheet. Type `reset confirm` to confirm you want to do this."
            content = [content1, content2]
        elif parsed[1] == "confirm":
            act_points_reset()
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
            content2 = "Error in `set`: too few operands.\nUsage: " + man("set")
            content = [content1, content2]
        else:
            params = io_params_load()
            string = str(parsed[1])
            newvalue = parsed[2]
            param = interpret(string, list(params.keys()))
            if not param:
                params = pd.DataFrame.from_dict(params, orient='index')
                content2 = "Couldn't find any parameter matching " + str(string) + " so here are all of them."
                content3 = "```" + str(params) + "```"
                content = [content1, content2, content3]
            elif not re.search("^-*\d+.*\d*$", newvalue):
                content2 = "Error in `set`: expected a numeric for `value`, got `" + str(newvalue) + "`.\nUsage: " + man("set")
                content = [content1, content2]
            else:
                newvalue = float(newvalue)
                oldvalue = params[param]
                params[param] = newvalue
                io_params_save(params)
                content2 = "Changed " + str(param) + " from " + str(oldvalue) + " to " + str(newvalue) + "."
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
            content2 = "Error in `split`: expected 3 or more operands, got " + str(operands) + ".\nUsage: " + man("split")
            content = [content1, content2]
        elif not re.search("^-*\d+\.*\d*$", value):
            content2 = "Error in `split`: expected a number for points, got `" + value + "`.\nUsage: " + man("split")
            content = [content1, content2]
        elif re.search("^nan$", parsed[1], re.IGNORECASE)  and interpret(parsed[1], sheet['Participant']) is None:
            content2 = "Error in `add`: forbidden value passed, `nan`.\nUsage: " + man("add")
            content = [content1, content2]
        # Execute
        elif operands == 3:
            string = parsed[1]
            value = float(value)
            participant = interpret(string, sheet['Participant'])
            if not participant: participant = string
            sheet = act_points_add(participant, value, "point", sheet)
            io_points_save(sheet)
            content2 = rng(["Good stuff", "Gerat", "Superb", "Well done", "Much thank", "Hekaru yeah", "Noice"]) + ", " + str(value) + " points were given to " + participant + "."
            content3 = "```" + str(act_points_show()) + "```"
            content = [content1, content2, content3]
        else:
            participants = ""
            value = float(value) / 2
            for s in list(range(1, operands-1)):
                string = parsed[s]
                participant = interpret(string, sheet['Participant'])
                if not participant: participant = string
                sheet = act_points_add(participant, value, "point", sheet)
                if s != operands-2:
                    if operands-2 == 2: participants = participants + participant + " "
                    else: participants = participants + participant + ", "
                else:                  participants = participants + "and " + participant
            io_points_save(sheet)
            content2 = rng(["Noice effort", "Everyone is best", "Good job, crew", "Well done everyone", "Guildies% much", "Stonks", "Such activity"]) + ", " + participants + " each got " + str(value) + " points."
            content3 = "```" + str(act_points_show()) + "```"
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
    elif re.search("^\d+$", parsed[1]):
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
    content1 = command_echo(message)
    content2 = "Here's how things stand."
    content3 = "```" + str(act_points_show()) + "```"
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
            content2 = "I recognised " + str(string) + " as " + str(participant) + "."
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
            content2 = "Error in `undo`: No more undos available."
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
    
def points_syntax(message, parsed):
    colour = discord.Colour.teal()
    content1 = command_echo(message)
    content2 = """
        Possible Pointinator commands:
        `add`, `split`, `offset`, `new`, `show`, `delete`, `undo`, `queue`, `reset`, `tail`, `tiers`, `whois`, `set`, `edit`, `points`, `help`, `info`, `chat`, `drill`.\n
        Issue `help` for detailed usage instructions.
        """
    content = [content1, content2]
    send = channel_respond(message, colour, content)
    return send


#%% Drill functions
def drill_add(message, parsed):
    # If officer
    if is_officer(message):
        colour = discord.Colour.gold()
        content1 = command_echo(message)
        # Check inputs
        drill = io_drill_load()
        value = parsed[3]
        operands = len(parsed)
        if operands < 5:
            content2 = "Error in `drill add`: expected 5 or more operands, got " + str(operands) + ".\nUsage: " + man("drill add")
            content = [content1, content2]
        elif not re.search("^-*\d+$", value):
            content2 = "Error in `drill add`: expected a number for amount, got `" + value + "`.\nUsage: " + man("drill add")
            content = [content1, content2]
        elif re.search("^nan$", parsed[1], re.IGNORECASE)  and interpret(parsed[1], drill['Participant']) is None:
            content2 = "Error in `drill add`: forbidden value passed, `nan`.\nUsage: " + man("drill add")
            content = [content1, content2]
        # Execute
        else:
            string1 = parsed[2]
            value = float(value)
            string2 = " ".join(parsed[4:])
            participant = interpret(string1, drill['Participant'])
            material = interpret(string2, drill['Item'])
            if not participant: participant = string1
            if not material:
                content2 = "Error in `drill add`: material not found, ", string2, ".\nUsage: " + man("drill add")
            act_drill_add(participant, value, material)
            content2 = rng(["Great"]) + ", added " + str(value) + " " + material + " to " + participant + "."
            content3 = "```" + str(act_drill_summary()) + "```"
            content = [content1, content2, content3]
        send = channel_respond(message, colour, content)
        return send
    # If not officer
    else:
        send = queue_add(message, parsed)
        return send
    return

def drill_progress(message, parsed):
    colour = discord.Colour.gold()
    progress = act_drill_progress()
    content1 = command_echo(message)
    content2 = "Here's the current drill progress."
    content3 = "```" + str(progress) + "```"
    content = [content1, content2, content3]
    send = channel_respond(message, colour, content)
    return send

def drill_reset(message, parsed):
    if is_officer(message):
        colour = discord.Colour.gold()
        content1 = command_echo(message)
        operands = len(parsed)
        if operands == 2:
            content2 = "Are you sure? This will wipe the drill sheet. Type `drill reset confirm` to confirm you want to do this."
            content = [content1, content2]
        elif parsed[2] == "confirm":
            act_drill_reset()
            content2 = "Wiped the drill sheet."
            content = [content1, content2]
        else:
            content2 = "Are you sure? This will wipe the drill sheet. Type `drill reset confirm` to confirm you want to do this."
            content = [content1, content2]
        send = channel_respond(message, colour, content)
        return send
    else:
        send = queue_add(message, parsed)
        return send

def drill_show(message, parsed):
    colour = discord.Colour.gold()
    drill = act_drill_show()
    content1 = command_echo(message)
    content2 = "Here's the drill sheet."
    content3 = "```" + str(drill) + "```"
    content = [content1, content2, content3]
    send = channel_respond(message, colour, content)
    return send

def drill_summary(message, parsed):
    colour = discord.Colour.gold()
    content1 = command_echo(message)
    content2 = "Here's the current drill report."
    content3 = "```" + str(act_drill_summary()) + "```"
    content = [content1, content2, content3]
    send = channel_respond(message, colour, content)
    return send

def drill_tail(message, parsed):
    colour = discord.Colour.gold()
    content1 = command_echo(message)
    # Check inputs
    operands = len(parsed)
    if operands < 2:
        lines = 6
    elif re.search("^\d+$", parsed[2]):
        lines = int(parsed[2])
    else:
        lines = 6
    # Execute
    lines = min(10, lines)
    drill = io_drill_load()
    sli = drill.iloc[-int(lines):]
    cols = ['Participant', 'Item', 'Amount', 'Date']
    sli = sli[cols]
    content2 = "Here are the last " + str(lines) + " lines of the drill sheet."
    content3 = "```" + str(sli) + "```"
    content = [content1, content2, content3]
    send = channel_respond(message, colour, content)
    return send

def drill_undo(message, parsed):
    # If officer
    if is_officer(message):
        colour = discord.Colour.gold()
        content1 = command_echo(message)
        # Check state
        if not os.path.exists(bak1_drill):
            content2 = "Error in `drill undo`: No more undos available."
            content = [content1, content2]
        else:
            act_drill_undo()
            drill = io_drill_load()
            lastmodified = max(drill['Date'])
            content2 = "Rolling back to the drill sheet as of " + str(lastmodified)
            content3 = "```" + str(act_drill_summary()) + "```"
            content = [content1, content2, content3]
        send = channel_respond(message, colour, content)
        return send
    # If not officer
    else:
        colour = discord.Colour.greyple()
        content1 = command_echo(message)
        act_queue_undo()
        queue = io_queue_load()
        if len(queue) > 0:
            lastmodified = max(queue['Date'])
            content2 = "Rolling back to queue as of " + str(lastmodified)
            content3 = "```" + str(queue) + "```"
            content = [content1, content2, content3]
        else:
            content2 = "Undid the last queue entry. It's empty now."
            content = [content1, content2]
        send = channel_respond(message, colour, content)
        return send
    
def drill_syntax(message, parsed):
    colour = discord.Colour.gold()
    content1 = command_echo(message)
    content2 = """
        Possible Pointinator drill commands:
        `drill add`, `drill show`, `drill progress`, `drill summary`, `drill tail`, `drill undo`, `drill reset`.\n
        Issue `help` for detailed usage instructions.
        """
    content = [content1, content2]
    send = channel_respond(message, colour, content)
    return send

#%% Queue function
def queue_add(message, parsed):
    colour = discord.Colour.greyple()
    content1 = command_echo(message)
    requestor = str(message.author)
    request = str(message.content)
    if re.search("^q|^queue", request):
        content2 = "Error in `queue`: `queue` commands not allowed in the queue."
        content = [content1, content2]
    else:
        act_queue_add(requestor, request)
        content2 = rng(["Thanks", "Nice one", "Gotcha", "Understood", "Thanks for the helmp"]) + ", your request `" + request + "` has been sent to officers for approval."
        content3 = "```" + str(act_queue_show()) + "```"
        content = [content1, content2, content3]
    send = channel_respond(message, colour, content)
    return send

#%% Roles functions
def roles_give(message, parsed):
    colour = discord.Colour.greyple()
    # Check inputs
    operands = len(parsed)
    sends = []
    if operands < 2:
        content1 = "Possible commands: `give`, `remove`. Possible roles: " + ", ".join(roles)
        content = [content1]
    else:
        string = parsed[1]
        role = interpret(string, roles)
        if role:
            roleid = discord.utils.get(message.guild.roles, name = role)
            send = [act_roles_give(message, roleid)]
            sends = sends + send
            content1 = "Adding you to " + role + "."
            content = [content1]
        else:
            content1 = "Possible commands: `give`, `remove`. Possible roles: " + ", ".join(roles)
            content = [content1]
    send = [channel_respond(message, colour, content)]
    sends = sends + send
    return sends

def roles_remove(message, parsed):
    colour = discord.Colour.greyple()
    # Check inputs
    operands = len(parsed)
    sends = []
    if operands < 2:
        content1 = "Possible commands: `give`, `remove`. Possible roles: " + ", ".join(roles)
        content = [content1]
    else:
        string = parsed[1]
        role = interpret(string, roles)
        if role:
            roleid = discord.utils.get(message.guild.roles, name = role)
            send = [act_roles_remove(message, roleid)]
            sends = sends + send
            content1 = "Removing you from " + role + "."
            content = [content1]
        else:
            content1 = "Possible commands: `give`, `remove`. Possible roles: " + ", ".join(roles)
            content = [content1]
    send = [channel_respond(message, colour, content)]
    sends = sends + send
    return sends

def roles_syntax(message, parsed):
    colour = discord.Colour.greyple()
    sends = []
    content1 = "Possible commands: `give`, `remove`. Possible roles: " + ", ".join(roles)
    content = [content1]
    send = [channel_respond(message, colour, content)]
    sends = sends + send
    return sends

#%% #points channel function selector
def points_channel(message, parsed):
    keyword = parsed[0].lower()
    if(keyword == "a"   or keyword == "add"):      send = points_add(message, parsed)
    elif(keyword == "c"   or keyword == "chat"):   send = points_chat(message, parsed)
    elif(keyword == "del" or keyword == "delete"): send = points_delete(message, parsed)
    elif(keyword == "dr"  or keyword == "drill"):  send = points_drill(message, parsed)
    elif(keyword == "edit"):                       send = points_edit(message, parsed)
    elif(keyword == "get"):                        send = points_get(message, parsed)
    elif(keyword == "help"):                       send = points_man(message, parsed)
    elif(keyword == "info"):                       send = points_info(message, parsed)
    elif(keyword == "n"   or keyword == "new"):    send = points_new(message, parsed)
    elif(keyword == "o"   or keyword == "offset"): send = points_offset(message, parsed)
    elif(keyword == "points"):                     send = points_points(message, parsed)
    elif(keyword == "q"   or keyword == "queue"):  send = points_queue(message, parsed)
    elif(keyword == "r"   or keyword == "reset"):  send = points_reset(message, parsed)
    elif(keyword == "s"   or keyword == "split"):  send = points_split(message, parsed)
    elif(keyword == "t"   or keyword == "tail"):   send = points_tail(message, parsed)
    elif(keyword == "tiers"):                      send = points_tiers(message, parsed)
    elif(keyword == "set"):                        send = points_set(message, parsed)
    elif(keyword == "sh"  or keyword == "show"):   send = points_show(message, parsed)
    elif(keyword == "whois"):                      send = points_whois(message, parsed)
    elif(keyword == "z"   or keyword == "undo"):   send = points_undo(message, parsed)
    else:                                          send = points_syntax(message, parsed)
    return send

#%% drill function selector
def points_drill(message, parsed):
    if len(parsed) > 1:
        keyword = parsed[1].lower()
        if(keyword == "a"   or keyword == "add"):      send = drill_add(message, parsed)
        elif(keyword == "progress"):                   send = drill_progress(message, parsed)
        elif(keyword == "r"   or keyword == "reset"):  send = drill_reset(message, parsed)
        elif(keyword == "sh"  or keyword == "show"):   send = drill_show(message, parsed)
        elif(keyword == "summary"):                    send = drill_summary(message, parsed)
        elif(keyword == "t"   or keyword == "tail"):   send = drill_tail(message, parsed)
        elif(keyword == "z"   or keyword == "undo"):   send = drill_undo(message, parsed)
        else:                                          send = drill_syntax(message, parsed)
    else:                                              send = drill_syntax(message, parsed)
    return send

#%% #roles channel function selector
def roles_channel(message, parsed):
    keyword = parsed[0].lower()
    if(keyword == "give"):                         send = roles_give(message, parsed)    
    elif(keyword == "remove"):                     send = roles_remove(message, parsed)
    else:                                          send = roles_syntax(message, parsed)
    return send

#%% Discord

intents = discord.Intents(auto_moderation = True,
                          auto_moderation_configuration = True,
                          auto_moderation_execution = True,
                          bans = True,
                          dm_messages = True,
                          dm_reactions = True,
                          dm_typing = True,
                          emojis = True,
                          emojis_and_stickers = True,
                          guild_messages = True,
                          guild_reactions = True,
                          guild_scheduled_events = True,
                          guild_typing = True,
                          guilds = True,
                          integrations = True,
                          invites = True,
                          members = True,
                          message_content = True,
                          messages = True,
                          presences = True,
                          reactions = True,
                          typing = True,
                          voice_states = True,
                          webhooks = True)

client = discord.Client(intents = intents)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))                       # inform ready in console
    
@client.event
async def on_message(message):                                                  # with embeds
    if(message.author.bot):                                                     # don't respond to self
        return
    if(message.content == ""):                                                  # don't respond to system messages
        return
    command = message.content                                                   # get the discord message and interpret it
    parsed = re.split(" ", command)
    if(str(message.channel) == "points"):                                       # don't chat in the wrong channels
        send = points_channel(message, parsed)
        await send
    elif(str(message.channel) == "roles"):
        send = roles_channel(message, parsed)
        for s in send: await s
        
#%% Execution

parser = argparse.ArgumentParser()
parser.add_argument("-k", "--keyfile", help = "Path to Discord bot secret key.")
parser.add_argument("-o", "--workdir", help = "Path to working directory.")
args = parser.parse_args()

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

file_points = args.workdir + "/pointinator.txt"
bak1_points = args.workdir + "/pointinator.bak1.txt"
bak2_points = args.workdir + "/pointinator.bak2.txt"
bak3_points = args.workdir + "/pointinator.bak3.txt"
file_drill = args.workdir + "/drill.txt"
bak1_drill = args.workdir + "/drill.bak1.txt"
bak2_drill = args.workdir + "/drill.bak2.txt"
bak3_drill = args.workdir + "/drill.bak3.txt"
file_queue = args.workdir + "/queue.txt"
bak1_queue = args.workdir + "/queue.bak1.txt"
bak2_queue = args.workdir + "/queue.bak2.txt"
bak3_queue = args.workdir + "/queue.bak3.txt"
file_params = args.workdir + "/params.txt"
file_log = args.workdir + "/discord.log"

passthrough = False                                                             # set this flag when you want commands to be processed silently

roles = ["Vell", "Sailies", "Guildbosses", "Khan", "Leeching", "Atoraxxion", "Othergaming"]

if(os.path.exists(file_params)):
    params = io_params_load()
else:      
    params = {
        'cap':150,                                                              # number of points to guarantee a max tier payout
        'tcap':10,                                                              # maximum tier attainable by scoring points only
        'thardcap':10,                                                          # maximum tier attainable after accounting for offsets
        'Old Tree\'s Tear':0,
        'Elder Tree Plywood':0,
        'Palm Plywood':0,
        'Standardized Timber Square':0,
        'Black Stone Powder':0,
        'Earth\'s Tear':0,
        'Steel':0,
        'Vanadium Ingot':0,
        'Log':0,
        'Bronze Ingot':0,
        'Titanium Ingot':0,
        'Black Stone (Weapon)':0,
        'Black Stone (Armor)':0,
        'Powder of Flame':0,
        'Fire Horn':0,
        'Coal':0
        }
    io_params_save(params)

if(os.path.exists(file_queue)):
    queue = io_queue_load()
else:
    queue = {
        'Requestor':[],
        'Request':[],
        'Time':[]
        }
    queue = pd.DataFrame(queue)
    io_queue_save(queue)


if(not os.path.exists(file_points)):                                                   # make a new sheet if it doesn't exist
    points_reset()

if(not os.path.exists(file_drill)):                                             # make a new drill sheet if it doesn't exist
    drill_reset()

# logging
handler = logging.FileHandler(filename=file_log, encoding='utf-8', mode='w')

# run bot
key = open(args.keyfile, mode='r', encoding='utf-8').read()
client.run(key, reconnect=True, log_handler=handler)

# 
