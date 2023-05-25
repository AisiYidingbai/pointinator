# -*- coding: utf-8 -*-
"""
Created on Mon Jan 31 15:42:10 2022

@author: AisiYidingbai
"""

# init
import os
import re
import json
import logging
from math import e
import numpy as np
import pandas as pd
from datetime import datetime
import argparse

#%% I/O Functions

# load the sheet
def loadsheet():
    data = pd.read_csv(file)
    data = data[['Participant', 'Value', 'Type', 'Date']]
    return data

# save the sheet
def savesheet(data):
    if(os.path.exists(bak3)):
        os.remove(bak3)                                                         # remove backup 3 if it exists
    if(os.path.exists(bak2)):
        os.rename(bak2, bak3)                                                   # make backup 2 to backup 3 if it exists
    if(os.path.exists(bak1)):
        os.rename(bak1, bak2)                                                   # make backup 1 to backup 2 if it exists
    if(os.path.exists(file)):
        os.rename(file, bak1)                                                   # make the previous sheet to backup 1
    data.to_csv(file)                                                           # save the current sheet

# undo the last change
def undosheet():
    if(os.path.exists(bak1)):
        os.remove(file)                                                         # delete the current sheet
        os.rename(bak1, file)                                                   # reinstate backup 1 as the current sheet
        if(os.path.exists(bak2)):
            os.rename(bak2, bak1)                                               # reinstate backup 2 as backup 1 if it exists
            if(os.path.exists(bak3)):
                    os.rename(bak3, bak2)                                       # reinstate backup 3 as backup 2 if it exists
        data = loadsheet()
        lastmodified = max(data['Date'])
        res1 = "OK, reverting to sheet last saved on " + str(lastmodified)
        res2 = gettierlist(data)
        return [res1, res2]
    else:
        res1 = "Cannot undo. No more undos available."                          # if there are no more backups, refuse to undo
        res2 = gettierlist(data)
        return [res1, res2]

# load the queue
def loadqueue():
    queue = pd.read_csv(queuefile)
    queue = queue[['Requestor', 'Request', 'Time']]
    return queue

#%% Sheet Functions

# get user from regex
def getuser(string, data):                                                      # collect a string to match to the sheet
    userlist = getuserlist(data)                                                # get the list of participants already in the sheet
    founduser = None
    for user in userlist:
        if(string == user):                                                     # first look for a direct match
            founduser = user
            break
    if(founduser is None):
        for user in userlist:
            if(re.search("^" + string, user, re.IGNORECASE)):                   # then look for a wildcard* match
                founduser = user
                break
    if(founduser is None):
        for user in userlist:
            if(re.search(string + "$", user, re.IGNORECASE)):                   # then look for a *wildcard match
                founduser = user
                break
    if(founduser is None):
        for user in userlist:
            if(re.search(re.sub("(.)", ".*\\1", string) + ".*", user, re.IGNORECASE)): # then look for an abbreviated match
                 founduser = user
                 break            
    return founduser

# add points
def addpoints(string, points, datatype, data):
    data = data.loc[data['Participant'] != "No-one yet"]                        # delete the initialising entry for new sheets if it is there
    founduser = getuser(string, data)                                           # call getuser()
    if(founduser):
        user = founduser                                                        # if a participant was found, use it
        res2 = False                                                            # return the flag res2, True if a new participant was added when adding points
    else:
        user = string                                                           # if not, add a new participant
        res2 = True
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")                         # get the current date and time
    res1 = pd.concat([data, pd.DataFrame({'Participant':[user], 'Value':[points], 'Type':[str(datatype)], 'Date':[date]})]) # add an entry to the sheet
    return [res1, res2]

# add new user
def new(string, data):
    data = data.loc[data['Participant'] != "No-one yet"]                        # delete the initialising entry for new sheets if it is there
    user = string
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")                         # get the current date and time
    res = pd.concat([data, pd.DataFrame({'Participant':[user], 'Value':[0], 'Type':["point"], 'Date':[date]})]) # add an entry to the sheet
    return res

# delete user
def delete(string, data):
    user = getuser(string, data)
    data = data.loc[data['Participant'] != user]
    res = data
    return res

# reset the sheet
def reset():
    data = pd.DataFrame([], columns = ['Participant', 'Value', 'Type', 'Date'])
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    data = pd.concat([data, pd.DataFrame({'Participant':["No-one yet"], 'Value':[0], 'Type':["point"], 'Date':[date]})])
    savesheet(data)

# get userlist
def getuserlist(data):
    userlist = list(set(data["Participant"]))                                   # find all participants currently in the list
    return userlist

# pivot sheet
def pivotsheet(data, datatype):
    tierlist = data.loc[data['Type'] == str(datatype)]
    tierlist = tierlist.groupby('Participant').sum('Value')                     # pivot the sheet to get points per participant
    tierlist['LogPoints'] = np.log(1 + tierlist['Value'])                       # calculate log(points + 1)
    return tierlist

# get logcurrentmax
def getlogcurrentmax(tierlist):
    loghighscore = max(tierlist['LogPoints'])                                   # determine max tier requirement by calculating log(highscore + 1) and log(pseudomax)
    pseudomax = np.power(int(params['cap']), (int(params['tcap'])-1)/(int(params['tcap'])-2))  # calculate the pseudomax from the cap (think upper end of T10, a.k.a. T11)
    logpseudomax = np.log(pseudomax)
    logcurrentmax = min(loghighscore, logpseudomax)                             # use the minimum of the two values. max tier requirement rises with the highscore until it reaches the cap
    return logcurrentmax

# get tierlist
def gettierlist(data):
    tierlist = pivotsheet(data, "point")                                        # pivot the sheet for points
    logcurrentmax = getlogcurrentmax(tierlist)                                  # calculate the log current max ("T11")
    tierlist['Tier'] = np.ceil(tierlist['LogPoints'] / logcurrentmax * (params['tcap']-1) + 1)   # calculate the current tiers
    offsets = pivotsheet(data, "tier")['Value']                                 # pivot the sheet for tiers
    tierlist = tierlist.join(offsets, on = "Participant", how = "left", rsuffix = ".tier")  # join tiers to point sheet
    tierlist['Value.tier'][np.isnan(tierlist['Value.tier'])] = 0
    tierlist['Tier'] = np.minimum(np.minimum(tierlist['Tier'], params['tcap']) + tierlist['Value.tier'], params['thardcap']) # don't let the tier exceed the max
    tierlist = tierlist.sort_values(['Value'], ascending = False)               # sort the sheet by descending points
    cols = ['Value', 'Tier']
    tierlist = tierlist[cols]
    return tierlist

# calculate tiers
def calculatetiers(data):
    tierlist = pivotsheet(data, "point")                                        # pivot the sheet
    logcurrentmax = getlogcurrentmax(tierlist)                                  # calculate the log current max ("T11")
    currenttiers = list()
    tierpoints = list()
    for i in range((int(params['tcap'])-2), -2, -1):
        currenttiers.append("T" + str(i+2))
        #tierpoints.append(np.ceil(np.power(np.power(e,logcurrentmax),(i/(params['tcap']-1)))))  # use meth to determine the T1-10 requirements
        tierpoints.append(np.around(np.power(np.power(e,logcurrentmax),(i/(params['tcap']-1))),1))  # use meth to determine the T1-10 requirements
    tiers = pd.DataFrame({'Tier':currenttiers, 'Value':tierpoints})
    tiers = tiers.set_index('Tier')
    return tiers

def findparam(key):
    found = None
    paramlist = list(params.keys())
    for p in paramlist:
        if(key == p):                                                           # first look for a direct match
            found = p
            break
    if(found is None):
        for p in paramlist:
            if(re.search("^" + key, p, re.IGNORECASE)):                         # then look for a wildcard* match
                found = p
                break
    if(found is None):
        for p in paramlist:
            if(re.search(key + "$", p, re.IGNORECASE)):                         # then look for a *wildcard match
                found = p
                break
    if(found is None):
        for p in paramlist:
            if(re.search(re.sub("(.)", ".*\\1", key) + ".*", p, re.IGNORECASE)): # then look for an abbreviated match
                 found = p
                 break
    return(found)



#%% Message Functions

def msg_add(participant, points):                                               # routine to add points
    data = loadsheet()
    points = np.round(points, 1)                                                # round the number of points to 1 d.p.
    if(isinstance(participant, str)):                                           # routine to deal with a single participant
        ret = addpoints(participant, points, "point", data)
        data = ret[0]
        if(ret[1]):
            res1 = "Added " + str(points) + " points for " + str(participant) + "."
        else:
            res1 = "Added " + str(points) + " points for " + str(getuser(participant, data)) + "."
        res2 = gettierlist(data)
        savesheet(data)
        return [res1, res2]
    else:                                                                       # routine to deal with multiple participants at once
        u = ""
        for p in participant:
            data = addpoints(p, points, "point", data)[0]
            u = u + ", " + str(getuser(str(p), data))
        res1 = "Added " + str(points) + " points each for: " + re.sub("^, ", "", u)
        res2 = gettierlist(data)
        savesheet(data)
        return [res1, res2]
    
def msg_delete(participant):
    data = loadsheet()
    user = getuser(participant, data)
    if user is not None:
        res1 = "Removed " + user + " from the board."
        data = delete(participant, data)
        savesheet(data)
        res2 = gettierlist(data)
        return [res1, res2]
    else:
        res = "Couldn't delete: I couldn't find anyone called " + participant + "."
        return res

def msg_offset(participant, tiers):                                             # routine to add tiers
    data = loadsheet()
    tiers = np.round(tiers, 0)                                                  # round the number of tiers to whole tiers
    ret = addpoints(participant, tiers, "tier", data)
    data = ret[0]
    if(ret[1]):
        res1 = "Added " + str(tiers) + " tiers for " + str(participant) + "."
    else:
        res1 = "Added " + str(tiers) + " tiers for " + str(getuser(participant, data)) + "."
    res2 = gettierlist(data)
    savesheet(data)
    return [res1, res2]  

def msg_distribute(participant, points):                                        # routine to divide points among multiple participants
    if(isinstance(participant, str)):
        res = msg_add(participant, points)                                      # call regular add routine if only one participant
    else:
        pointseach = points / len(participant)                                  # calculate points each and then call add routine if more than one participant
        res = msg_add(participant, pointseach)
        res[0] = res[0] + "; total " + str(points) + " points."
    return [res[0], res[1]]

def msg_distribute_new(participant, points):                                    # routine to divide points among multiple participants
    if(isinstance(participant, str)):
        res = msg_add(participant, points)                                      # call regular add routine if only one participant
    else:
        pointseach = points / 2                                                 # each participant gets half the activity value
        res = msg_add(participant, pointseach)
        res[0] = res[0] + "; original points value was " + str(points) + "."
    return [res[0], res[1]]

def msg_show():                                                                 # routine to show the current sheet
    data = loadsheet()
    tierlist = gettierlist(data)
    res1 = "Here is the current sheet:"
    res2 = tierlist
    return [res1, res2]

def msg_new(participant):                                                       # routine to add a new participant
    data = loadsheet()
    data = new(participant, data)
    res1 = "Added " + str(participant) + " as a new participant."
    res2 = gettierlist(data)
    savesheet(data)
    return [res1, res2]

def msg_tiers():                                                                # routine to show the current point requirements per tier
    data = loadsheet()
    tiers = calculatetiers(data)
    res1 = "Here are the current point requirements per tier:"
    res2 = tiers
    return [res1, res2]

def msg_whois(participant):                                                     # routine to test participant abbreviations
    data = loadsheet()
    founduser = getuser(participant, data)
    if(founduser is not None):
        res = "I recognised \"" + participant + "\" as " + getuser(participant, data) + "."
    else:
        res = "I could not recognise anyone by \"" + participant + "\"."
    return res

def msg_getcap():                                                               # routine to show the cap
    res = "The cap is " + str(params['cap']) + ". Participants scoring higher than this are guaranteed a T" + str(params['tcap']) + " payout."
    return res

def msg_setcap(value):                                                          # routine to change the cap
    params['cap'] = value
    res = "OK, changing the cap to " + str(params['cap']) + ". Participants scoring higher than this are guaranteed a T" + str(params['tcap']) + " payout."
    with open(paramsfile, 'w') as f:                                            # save to file
        json.dump(params, f, indent = 4)
    return res

def msg_setparam(key, value):                                                   # routine to change parameters
    found = findparam(key)
    if(found is not None):
        old = params[found]
        params[found] = value
        res = "OK, changing the value of " + str(found) + " from " + str(old) + " to " + str(value) + "."
        with open(paramsfile, 'w') as f:                                            # save to file
            json.dump(params, f, indent = 4)
    else:
        res = "I couldn't find any parameter called " + str(key) + "."
    return res

def msg_getparam(key):                                                            # routine to view parameters
    found = findparam(key)
    if(found is not None):
        res = "The value of " + str(found) + " is " + str(params[found]) + "."
    else:
        res = "I couldn't find any parameter called " + str(key) + "."
    return res

def msg_audit(lines):
    data = loadsheet()
    sli = data.iloc[-int(lines):]
    cols = ['Participant', 'Value', 'Type', 'Date']
    res1 = "Here are the last " + str(lines) + " lines of the sheet:"
    res2 = sli[cols]
    return [res1, res2]

def msg_edit(row, col, newvalue):
    data = loadsheet()
    row = int(row)
    if(row > len(data)-1):
        res = "Error point-editing the sheet. Row number out of bounds"
        return res
    elif(col != "Participant" and col != "Date" and col != "Value" and col != "Type"):
        res = "Error point-editing the sheet. Column name must be one of: Participant, Date, Value, Type"
        return res
    else:
        old = data.at[row,col]
        data.at[row,col] = newvalue
        savesheet(data)
        sli = data.iloc[row:row+1]
        res1 = "OK, successfully point-edited the " + col + " at line " + str(row) + " from " + str(old) + " to " + str(newvalue) + "."
        res2 = sli
        return [res1, res2]

def msg_reset(confirm):                                                         # routine to wipe the sheet. use reset confirm to confirm
    if(confirm == "confirm"):
        reset()
        res = "OK, I've wiped the sheet."
    else:
        res = "Are you sure? This will wipe the sheet. Type `reset confirm` to confirm you want to do this."
    return res

def msg_params():
    res1 = "Here are the current Pointinator parameters:"
    res2 = pd.DataFrame.from_dict(params, orient='index')
    return [res1, res2]

def msg_help():
    res = """
    Possible Pointinator commands:
    `add`, `split`, `offset`, `new`, `show`, `delete`, `undo`, `queue`, `reset`, `audit`, `tiers`, `whois`, `set`, `params`, `edit`, `points`, `help`, `info`, `chat`, `drill`.\n
    Issue `help` for detailed usage instructions.
    """
    return res

def msg_man():
    res = """
    Usage:
    \t`a <p ...> <n>`: Award *n* points each to one or more participants *p*
    \t`s <p ...> <n>`: Divide *n* points between participants *p*
    \t`o <p> <n>`: Add *n* tiers to a participant *p*
    \t`n <p>`: Add a new participant *p*
    \t`show`: Show the current sheet
    \t`del <p>`: Delete a participant *p*
    \t`z`: Undo the last change
    \t`q`: Show the queue
    \t`q a`: Approve the request at the top of the queue
    \t`q d`: Decline the request at the top of the queue
    \t`q q <requestor> <request>`: Manually add an entry to the queue with *requestor* and *request*
    \t`r`: Wipe the sheet
    \t`audit <n>`: Show the last *n* sheet actions
    \t`tiers`: Show the current point requirements per tier
    \t`whois <name>`: See if I can recognise a participant *name*
    \t`set <param> <value>`: Change a Pointinator *param*eter to *value*
    \t`params`: Show all Pointinator parameters
    \t`edit <field> <line> <value>`: Change a sheet entry in *field* at *line* to *value*.
    \t`points`: Show point values
    \t`help`: Show this help
    \t`info`: Show info on Pointinator\n
    \t`c`: Send a chat message in this channel without Pointinator interpreting it as a command
    Drill commands:
    \t`dr a <p> <n> <mat>`: Record *n* drill *mat*erials for a participant *p* 
    \t`dr show`: Show a comprehensive report of drill materials
    \t`dr summary`: Show a summary of drill materials
    \t`dr progress`: Show a summary of drill progress
    \t`dr z`: Undo the last change to the drill sheet
    \t`dr audit <n>`: Show the last *n* sheet actions
    \t`dr r`: Wipe the drill sheet
    """
    return res

def msg_points():
    res = """
    Point values:
    \t**S guild missions**: 1 point
    \t**M guild missions**: 2 points
    \t**L guild missions**: 3 points
    \t**XL guild missions**: 4 points
    \t**S [Boss Subjugation] missions**: 1 point
    \t**M [Boss Subjugation] missions**: 2 points
    \t**L [Boss Subjugation] missions**: 3 points
    \t**XL [Boss Subjugation] missions**: 4 points
    \t**Attending guild events**: 2 points
    \t**Depositing a [Guild] Steel Candidum Shell**: 16 points
    \t**Depositing [Guild] Drill materials**: see `drill` commands
    """
    return res

def msg_info():
    res = """
        Welcome to **Pointinator**, a Discord bot that keeps track of points.
        
        *About*: Send commands by chatting in this channel. Send a command every time someone does something that earns points. Issue `points` to see qualifying activities.
        
        *Usage*: Add points with `a <participant> <points>`. The *participant* can be a nickname if they're already on the board. For a full list of commands, issue `help`.
        
        *Privileges*: Officers' commands will be executed by the bot immediately. Please type deliberately. If you're not an officer, then your command will be put in the queue for an officer to approve.
        
        *Support*: Pointinator goes down for nightly maint around 4:00 GMT/BST. If it's down outside of those times, contact Aisi Yidingbai. Pointinator is open-source software available at <https://github.com/AisiYidingbai/pointinator>. 
        """
    return res

def msg_queue_add(requestor, request):
    queue = loadqueue()
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    queue = pd.concat([queue, pd.DataFrame({'Requestor':[requestor], 'Request':[request], 'Time':[date]})])
    queue.to_csv(queuefile)
    res1 = "Added your request `" + request + "` to the queue for approval."
    res2 = queue
    return [res1, res2]

def msg_queue_show():
    queue = loadqueue()
    res1 = "There are " + str(len(queue)) + " items in the queue:"
    res2 = queue
    if(len(queue) == 0):
        return res1
    else:
        return [res1, res2]
    return [res1, res2]

def msg_queue_approve():
    queue = loadqueue()
    command = queue.iloc[0,1]
    on_command(command)
    res1 = "Approved request `" + queue.iloc[0,1] + "` by " + queue.iloc[0,0] + " made at " + queue.iloc[0,2] + "."
    queue = queue.iloc[1:]
    queue.to_csv(queuefile)
    data = loadsheet()
    tierlist = gettierlist(data)
    res2 = tierlist
    return [res1, res2]
    
def msg_queue_deny():
    queue = loadqueue()
    res1 = "Denied request `" + queue.iloc[0,1] + "` by " + queue.iloc[0,0] + " made at " + queue.iloc[0,2] + "."
    queue = queue.iloc[1:]
    queue.to_csv(queuefile)
    res2 = queue
    if(len(queue) == 0):
        return res1
    else:
        return [res1, res2]


#%% Main Routine

def on_command(command):                                                        # check the contents of the command
    parsed = re.split(" ", command)
    keyword = parsed[0].lower()
    if(keyword == "a" or keyword == "add" or keyword == "give"):                                  # add command:
        if(len(parsed) < 3):                                                    # fail if less than 2 arguments
            ret = msg_help()
        elif(not re.search("^-*\d*[\.,]*\d*$", parsed[-1])):                      # fail if points arg is not a number
            ret = msg_help()
        elif(len(parsed) == 3):                                                 # accept if one participant
            ret = msg_add(parsed[1], float(parsed[2]))
        else:                                                                   # accept if more than one participant
            ret = msg_add(parsed[1:len(parsed)-1], float(re.sub(",", ".", parsed[-1])))
    elif(keyword == "o" or keyword == "offset"):
        if(len(parsed) < 3):
            ret = msg_help()
        elif(not re.search("^-*\d*[\.,]*\d*$", parsed[2])):                     # fail if points arg is not a number
            ret = msg_help()
        else:
            ret = msg_offset(parsed[1], float(parsed[2]))
    elif(keyword == "d" or keyword == "s" or keyword == "distribute" or keyword == "split"):                        # distribute command:
        if(len(parsed) < 3):                                                    # fail if less than 2 arguments
            ret = msg_help()
        elif(not re.search("^-*\d*[\.,]*\d*$", parsed[-1])):                      # fail if points arg is not a number
            ret = msg_help()
        elif(len(parsed) == 3):                                                 # if only one participant, call add instead
            ret = msg_add(parsed[1], float(parsed[2]))
        else:                                                                   # call distribute if more than one participant
            ret = msg_distribute_new(parsed[1:len(parsed)-1], float(re.sub(",", ".", parsed[-1])))
    elif(keyword == "olddistribute" or keyword == "oldsplit"):                        # distribute command:
        if(len(parsed) < 3):                                                    # fail if less than 2 arguments
            ret = msg_help()
        elif(len(parsed) == 3):                                                 # if only one participant, call add instead
            ret = msg_add(parsed[1], float(parsed[2]))
        else:                                                                   # call distribute if more than one participant
            ret = msg_distribute(parsed[1:len(parsed)-1], float(re.sub(",", ".", parsed[-1])))
    elif(keyword == "u" or keyword == "z" or keyword == "undo"):
        ret = undosheet()
    elif(keyword == "sh" or keyword == "show"):
        ret = msg_show()
    elif(keyword == "n" or keyword == "new"):
        ret = msg_new(parsed[1])
    elif(keyword == "del" or keyword == "delete"):
        ret = msg_delete(parsed[1])        
    elif(keyword == "t" or keyword == "tiers"):
        ret = msg_tiers()
    elif(keyword == "w" or keyword == "whois"):
        if(len(parsed) < 2):
            ret = msg_help()
        else:
            ret = msg_whois(parsed[1])
    elif(keyword == "getcap"):
        ret = msg_getcap()
    elif(keyword == "setcap"):
        if(len(parsed) < 2):
            ret = msg_help()
        elif(not parsed[1].isnumeric()):
            ret = msg_help()
        else:
            ret = msg_setcap(int(parsed[1]))
    elif(keyword == "setparam" or keyword == "set"):
        if(len(parsed) < 3):
            ret = msg_help()
        elif(not re.search("^-*\d*[\.,]*\d*$", parsed[2])):                     # fail if points arg is not a number
            ret = msg_help()
        else:
            ret = msg_setparam(' '.join(parsed[1:len(parsed)-1]), float(re.sub(",", ".", parsed[-1])))
    elif(keyword == "getparam"):
        if(len(parsed) < 2):
            ret = msg_help()
        else:
            ret = msg_getparam(' '.join(parsed[1:]))
    elif(keyword == "params"):
        ret = msg_params()
    elif(keyword == "a" or keyword == "audit"):
        if(len(parsed) < 2):
            ret = msg_help()
        elif(not re.search("^\d+$", parsed[1])):                                # fail if points arg is not a number
            ret = msg_help()
        else:
            ret = msg_audit(parsed[1])
    elif(keyword == "e" or keyword == "edit"):
        if(len(parsed) < 4):
            ret = msg_help()
        elif(not re.search("^\d+$", parsed[1])):
            ret = msg_help()
        else:
            ret = msg_edit(parsed[1], parsed[2], parsed[3])
    elif(keyword == "r" or keyword == "reset"):
        if(len(parsed) < 2):
            ret = msg_reset(False)
        else:
            ret = msg_reset(parsed[1])
    elif(keyword == "points"):
        ret = msg_points()
    elif(keyword == "q" or keyword == "queue"):
        if(len(parsed) < 2):
            ret = msg_queue_show()
        elif(parsed[1] == "a" or parsed[1] == "approve"):
            ret = msg_queue_approve()
        elif(parsed[1] == "d" or parsed[1] == "deny"):
            ret = msg_queue_deny()
        elif(len(parsed) > 2 and parsed[1] == "q" or len(parsed) > 2 and parsed[1] == "queue"):
            ret = msg_queue_add(parsed[2], ' '.join(parsed[3:]))
        else:
            ret = msg_queue_show()
    elif(keyword == "h" or keyword == "help"):
        ret = msg_man()
    elif(keyword == "i" or keyword == "info"):
        ret = msg_info()
    elif(keyword == "dr" or keyword == "drill"):
        if(len(parsed) < 2):
            ret = msg_help()
        else:
            ret = drill_on_command(command) # send to drill functions
    elif(keyword == "c" or keyword == "chat"):
        return None
    else:
        ret = msg_help()
    return(ret)



#%% Drill Functions

# load the sheet
def drill_loadsheet():
    drill_data = pd.read_csv(drill_file)
    drill_data = drill_data[['Participant', 'Item', 'Amount', 'Date']]
    return drill_data

# save the sheet
def drill_savesheet(drill_data):
    if(os.path.exists(drill_bak3)):
        os.remove(drill_bak3)                                                   # remove backup 3 if it exists
    if(os.path.exists(drill_bak2)):
        os.rename(drill_bak2, drill_bak3)                                       # make backup 2 to backup 3 if it exists
    if(os.path.exists(drill_bak1)):
        os.rename(drill_bak1, drill_bak2)                                       # make backup 1 to backup 2 if it exists
    if(os.path.exists(drill_file)):
        os.rename(drill_file, drill_bak1)                                       # make the previous sheet to backup 1
    drill_data.to_csv(drill_file)                                               # save the current sheet

# undo the last change
def drill_undosheet():
    if(os.path.exists(drill_bak1)):
        os.remove(drill_file)                                                   # delete the current sheet
        os.rename(drill_bak1, drill_file)                                       # reinstate backup 1 as the current sheet
        if(os.path.exists(drill_bak2)):
            os.rename(drill_bak2, drill_bak1)                                   # reinstate backup 2 as backup 1 if it exists
            if(os.path.exists(drill_bak3)):
                    os.rename(drill_bak3, drill_bak2)                           # reinstate backup 3 as backup 2 if it exists
        drill_data = drill_loadsheet()
        lastmodified = max(drill_data['Date'])
        res1 = "OK, reverting to sheet last saved on " + str(lastmodified)
        res2 = drill_summary()
        return [res1, res2]
    else:
        res1 = "Cannot undo. No more undos available."                          # if there are no more backups, refuse to undo
        res2 = drill_summary()
        return [res1, res2]

# reset the sheet
def drill_reset():                                                              # reset the sheet
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    data = {'Participant':["dummy"] * 16,
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
    drill_data = pd.DataFrame(data)
    drill_data = pd.concat([drill_data, pd.DataFrame({'Participant':["No-one yet"], 'Item':["Nothing"], 'Amount':[0], 'Date':[date]})])
    drill_savesheet(drill_data)

# get the list of participants or materials
def drill_getlist(drill_data, datatype):
    userlist = list(set(drill_data[datatype]))                                  # datatype can either be Participant or Item
    userlist = sorted(userlist, key = len)
    return userlist

# get user or mat from regex
def drill_getname(string, drill_data, datatype):                                # collect a string to match to the sheet
    userlist = drill_getlist(drill_data, datatype)                              # get the list of participants already in the sheet
    founduser = None
    for user in userlist:
        if(string == user):                                                     # first look for a direct match
            founduser = user
            break
    if(founduser is None):
        for user in userlist:
            if(re.search("^" + string, user, re.IGNORECASE)):                   # then look for a wildcard* match
                founduser = user
                break
    if(founduser is None):
        for user in userlist:
            if(re.search(string + "$", user, re.IGNORECASE)):                   # then look for a *wildcard match
                founduser = user
                break
    if(founduser is None):
        for user in userlist:
            if(re.search(re.sub("(.)", ".*\\1", string) + ".*", user, re.IGNORECASE)): # then look for an abbreviated match
                 founduser = user
                 break            
    return founduser

# add mat
def drill_addpoints(string, amount, material, drill_data):
    drill_data = drill_data.loc[drill_data['Participant'] != "No-one yet"]      # delete the initialising entry for new sheets if it is there
    founduser = drill_getname(string, drill_data, "Participant")                # call getuser()
    if(founduser):
        user = founduser                                                        # if a participant was found, use it
        res2 = False                                                            # return the flag res2, True if a new participant was added when adding points
    else:
        user = string                                                           # if not, add a new participant
        res2 = True
    foundmat = drill_getname(material, drill_data, "Item")
    if(foundmat):
        mat = foundmat
    else:
        foundmat = material
    date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")                         # get the current date and time
    res1 = pd.concat([drill_data, pd.DataFrame({'Participant':[user], 'Amount':[amount], 'Item':[mat], 'Date':[date]})]) # add an entry to the sheet
    return [res1, res2]

# show summary
def drill_summary():
    drill_data = drill_show()
    drill_data = drill_data.reset_index()
    drill_data['Points'] = drill_data['Silver (M)'] / 2
    drill_data['Points'] = drill_data['Silver (M)'] / 2
    drill_data['Points'] = np.round(drill_data['Points'], 1)
    drill_data = drill_data.groupby('Participant').sum(['Silver', 'Points'])
    drill_data = drill_data.sort_values('Silver (M)', ascending = False)
    return drill_data

# show full sheet
def drill_show():
    drill_data = drill_loadsheet()
    drill_data = drill_data.loc[drill_data['Participant'] != "dummy"]           # data has dummy rows with all mats but zero amount and assigned to no-one. remove
    drill_data = drill_data.groupby(['Participant', 'Item']).sum('Amount')      # group by participant and item, show a sum of the amount
    drill_data = drill_data.reset_index()
    silver = []                                                                 # calculate silver
    for i in range(len(drill_data)):
        item = drill_data.iloc[i,1]
        amount = drill_data.iloc[i,2]
        silver.append(amount * params[item] / 1000000)                          # using the parameters file, and then calculate millions of silver
    drill_data['Silver (M)'] = silver
    drill_data['Silver (M)'] = np.round(drill_data['Silver (M)'], 1)            # round to 1 d.p.
    drill_data = drill_data.groupby(['Participant', 'Item']).sum(['Silver'])
    return drill_data

# show totals
def drill_totals():
    drill_data = drill_loadsheet()
    drill_pivoted = drill_data.groupby(['Item']).sum('Amount')                  # group by item only, show a sum of the total amount contributed so far
    drill_pivoted = drill_pivoted.reset_index()
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
    drill_pivoted = drill_pivoted.merge(drill_totals, on = "Item", how = "outer")# merge arrays
    drill_pivoted = drill_pivoted.sort_values("Part")
    drill_pivoted['Amount'] = drill_pivoted['Amount'].fillna(0)
    drill_pivoted = drill_pivoted.set_index(['Part','Item'])
    return drill_pivoted



#%% Drill Message Functions

# routine to add items
def msg_drill_add(participant, amount, material):                               # routine to add mats to the sheet
    drill_data = drill_loadsheet()
    ret = drill_addpoints(participant, amount, material, drill_data)
    drill_data = ret[0]
    if(ret[1]):
        res1 = "Added " + str(amount) + " " + str(drill_getname(material, drill_data, "Item")) + " for the new participant " + str(participant) + "."
    else:
        res1 = "Added " + str(amount) + " " + str(drill_getname(material, drill_data, "Item")) + " for " + str(drill_getname(participant, drill_data, "Participant")) + "."
    drill_savesheet(drill_data)
    res2 = drill_summary()
    return [res1, res2]

def msg_drill_summary():                                                        # routine to show per participant summary
    drill_data = drill_summary()
    res1 = "Here is the current sheet:"
    res2 = drill_data
    return [res1, res2]

def msg_drill_show():                                                           # routine to show the a comprehensive report
    drill_report = drill_show()
    res1 = "Here is the current sheet:"
    res2 = drill_report
    return [res1, res2]

def msg_drill_totals():                                                         # routine to show a per mat summary
    totals = drill_totals()
    res1 = "Here's the drill progress:"
    res2 = totals
    return [res1, res2]

def msg_drill_audit(lines):
    drill_data = drill_loadsheet()
    drill_data = drill_data.iloc[-int(lines):]
    cols = ['Participant', 'Amount', 'Item', 'Date']
    res1 = "Here are the last " + str(lines) + " lines of the sheet:"
    res2 = drill_data[cols]
    return [res1, res2]

def msg_drill_reset(confirm):                                                   # routine to wipe the sheet. use reset confirm to confirm
    if(confirm == "confirm"):
        drill_reset()
        res = "OK, I've wiped the drill sheet."
    else:
        res = "Are you sure? This will wipe the drill sheet. Type `drill reset confirm` to confirm you want to do this."
    return res



#%% Drill Main Routine

# main drill routine
def drill_on_command(command):
    parsed = re.split(" ", command)
    keyword = parsed[1].lower()
    if(keyword == "a" or keyword == "add"):                                                       # detect add
        if(len(parsed) < 5):                                                    # fail if fewer than 3 args
            ret = msg_help()
        elif(not re.search("^-*\d+$", parsed[3])):                              # fail if points arg is not a number
            ret = msg_help()
        elif(drill_getname(' '.join(parsed[4:]), drill_loadsheet(), "Item") is None):# fail if no item of that name (arg 3) can be found
            ret = msg_help()
        else:
            ret = msg_drill_add(parsed[2], int(parsed[3]), ' '.join(parsed[4:]))# accept multi-word argument in arg 3
    elif(keyword == "sh" or keyword == "show"):                                                    # detect show
        ret = msg_drill_show()
    elif(keyword == "summary"):                                                 # detect summary
        ret = msg_drill_summary()
    elif(keyword == "progress"):                                                # detect progress
        ret = msg_drill_totals()
    elif(keyword == "z" or keyword == "u" or keyword == "undo"):                                                    # detect undo
        ret = drill_undosheet()
    elif(keyword == "a" or keyword == "audit"):
        if(len(parsed) < 3):
            ret = msg_help()
        elif(not re.search("^\d+$", parsed[2])):                                # fail if arg is not a number
            ret = msg_help()
        else:
            ret = msg_drill_audit(parsed[2])
    elif(keyword == "r" or keyword == "reset"):                                                   # detect reset
        if(len(parsed) < 3):
            ret = msg_drill_reset(False)
        else:
            ret = msg_drill_reset(parsed[2])
    else:
        ret = msg_help()
    return ret



#%% Discord

import discord
from discord.utils import get

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

#@client.event                                                                   # deprecated text-only messaging
#async def on_message(message):
#    if(message.author.bot):
#        return                                                                  # don't respond to self
#    elif(str(message.channel) != "points"):
#        return                                                                  # don't chat in the wrong channels
#    else:
#        command = message.content                                               # get the discord message and interpret it
#        ret = on_command(command)
#        await message.channel.send(ret)

@client.event
async def on_message(message):                                                  # with embeds
    if(message.author.bot):
        return                                                                  # don't respond to self
    if(message.content == ""):
        return
    if(str(message.channel) == "points"):                                       # don't chat in the wrong channels
        command = message.content                                               # get the discord message and interpret it
        print(command)
        isOfficer = "Officers" in str(message.author.roles)
        if(isOfficer):
            ret = on_command(command)
            commandecho = "*Your command: *`" + re.sub("[*`]", "", command) + "`" + "\n"
            if(isinstance(re.match("^dr", command), re.Match)):
                colour = discord.Colour.dark_gold()
            else:
                colour = discord.Colour.teal()
            if(isinstance(ret, str)):
                ret = commandecho + ret
                await message.channel.send(ret)
            elif(isinstance(ret, list)):
                embed = discord.Embed(title = commandecho,
                                      #description = "```" + str(ret[1]) + "```",
                                      color = colour)            
                embed.add_field(name = "", value = ret[0], inline=False)
                embed.add_field(name = "", value = "```" + str(ret[1]) + "```", inline=False)
                embed.set_footer(text = "by Yidingbai :)")
                await message.channel.send(embed = embed)
            else:
                return None
        else:
            commandecho = "*Your command: *`" + re.sub("[*`]", "", command) + "`" + "\n"
            colour = discord.Colour.teal()
            ret = msg_queue_add(message.author, message.content)
            embed = discord.Embed(title = commandecho,
                                  color = colour)            
            embed.add_field(name = "", value = ret[0], inline=False)
            embed.add_field(name = "", value = "```" + str(ret[1]) + "```", inline=False)
            embed.set_footer(text = "by Yidingbai :)")
            await message.channel.send(embed = embed)

#%% Role selector        
    elif(str(message.channel) == "roles"):
        possible_roles = ["Vell", "Sailies", "Guildbosses", "Khan", "Leeching", "Atoraxxion", "Othergaming"]
        t = re.match("^give\s(.+)$", message.content, re.IGNORECASE)
        r = re.match("^remove\s(.+)$", message.content, re.IGNORECASE)
        if t:                                                                   # to add a role
            role = get(message.guild.roles, name = t.group(1))
            if role is not None:                                                    # role valid
                if str(role) in possible_roles:                                              # role found in selectable list
                    await message.author.add_roles(role)
                    await message.channel.send("Gotcha, giving you the " + str(role) + " role.")
                else:                                                                   # role not found in selectable list
                    await message.channel.send("Sorry, you can't change the " + str(role) + " role.")
            else:
                await message.channel.send("I couldn't find the " + t.group(1) + " role.")
        elif r:                                                                  # to remove a role
            role = get(message.guild.roles, name = r.group(1))
            if role is not None:
                if str(role) in possible_roles:                                              # role found in selectable list
                    await message.author.remove_roles(role)
                    await message.channel.send("Gotcha, removing you from the " + str(role) + " role.")
                else:                                                                   # role not found in selectable list
                    await message.channel.send("Sorry, you can't change the " + str(role) + " role.")
            else:
                await message.channel.send("I couldn't find the " + r.group(1) + " role.")
        else:
            await(message.channel.send("Possible commands: `give [role]`, `remove [role]`. \nPossible roles: " + str(possible_roles) + "."))
    else:
        return


#%% Execution

parser = argparse.ArgumentParser()
parser.add_argument("-k", "--keyfile", help = "Path to Discord bot secret key.")
parser.add_argument("-o", "--workdir", help = "Path to working directory.")
args = parser.parse_args()
keyfile = args.keyfile

file = args.workdir + "/pointinator.txt"
bak1 = args.workdir + "/pointinator.bak1.txt"
bak2 = args.workdir + "/pointinator.bak2.txt"
bak3 = args.workdir + "/pointinator.bak3.txt"
drill_file = args.workdir + "/drill.txt"
drill_bak1 = args.workdir + "/drill.bak1.txt"
drill_bak2 = args.workdir + "/drill.bak2.txt"
drill_bak3 = args.workdir + "/drill.bak3.txt"
paramsfile = args.workdir + "/params.txt"
queuefile = args.workdir + "/queue.txt"
handlerfile = args.workdir + "/discord.log"

if(os.path.exists(paramsfile)):
    with open(paramsfile) as r:                                                 # parameters are stored as json. load it on run
        params = json.load(r)
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
    with open(paramsfile, 'w') as f:
        json.dump(params, f, indent = 4)

if(os.path.exists(queuefile)):
    with open(queuefile) as r:
        queue = loadqueue()
else:
    queue = {
        'Requestor':[],
        'Request':[],
        'Time':[]
        }
    queue = pd.DataFrame(queue)
    queue.to_csv(queuefile)


if(not os.path.exists(file)):                                                   # make a new sheet if it doesn't exist
    reset()

if(not os.path.exists(drill_file)):                                             # make a new drill sheet if it doesn't exist
    drill_reset()

# logging
handler = logging.FileHandler(filename=handlerfile, encoding='utf-8', mode='w')

# run bot
key = open(keyfile, mode='r', encoding='utf-8').read()
client.run(key, reconnect=True, log_handler=handler)


