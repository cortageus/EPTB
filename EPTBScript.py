#   _____                               _______             _             ____        _
#  |  __ \                             |__   __|           | |           |  _ \      | |
#  | |__) |_ _ _ __   __ _ _ __ ___   __ _| |_ __ __ _  ___| | _____ _ __| |_) | ___ | |_
#  |  ___/ _` | '_ \ / _` | '_ ` _ \ / _` | | '__/ _` |/ __| |/ / _ \ '__|  _ < / _ \| __|
#  | |  | (_| | | | | (_| | | | | | | (_| | | | | (_| | (__|   <  __/ |  | |_) | (_) | |_
#  |_|   \__,_|_| |_|\__,_|_| |_| |_|\__,_|_|_|  \__,_|\___|_|\_\___|_|  |____/ \___/ \__|

import disnake
from disnake.ext import commands, tasks
import requests
import json
import aiohttp
import datetime
import re
import pytz
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

panamaDirectory = requests.get("https://api.earthmc.net/v2/aurora/nations/panama").json()

intents = disnake.Intents.all()
intents.message_content = True
intents.members = True

currentEmbed = None
VerificationCache = {}
beamWeek = False

version = "V2.2"

timezone = pytz.timezone("US/Eastern")

bot = commands.Bot(
    command_prefix='/',
    intents=intents
)

def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def UpdateServer(passContext, notificationsChannel=None, notificationsStatus="False", embedMessage=None, embedChannelDomain=None, adminRole=None, citizenRole=None):

    with open("Configurations/storage.json", "r") as storage:
        pullStorage = json.load(storage)

    if str(passContext.guild.id) not in pullStorage:
        appendData = {
            "guildName": passContext.guild.name,
            "notificationsChannel": notificationsChannel,
            "notificationsStatus": notificationsStatus,
            "embedMessage": embedMessage,
            "embedChannelDomain": embedChannelDomain,
            "adminRole": adminRole,
            "citizenRole": citizenRole
        }
        fullAppendData = {str(passContext.guild.id): appendData}
        pullStorage.update(fullAppendData)
    else:
        for key, value in locals().items():
            if key not in ['passContext', 'pullStorage', 'storage'] and value is not None:
                pullStorage[str(passContext.guild.id)][key] = value

    with open("Configurations/storage.json", "w") as storage:
        dumpstuff = json.dumps(pullStorage, indent=4)
        storage.write(dumpstuff)


############################ LIST FORMATTING ############################

def formatlist(list, start=-1, end=-1):
    lookupList = panamaDirectory[list]
    if start == -1:
        return '\n'.join('{}: {}'.format(i + 1, item.replace("_", " ")) for i, item in enumerate(lookupList))
    else:
        return '\n'.join('{}: {}'.format(i + 1, item.replace("_", " ")) for i, item in enumerate(lookupList[start:end]))


############################## MISC COMMANDS #############################

@bot.slash_command(name="changelog", description="See recent changes to the bot")
async def changelog(inter):
    sendEmbed = disnake.Embed(title=f"Changelog for Version {version}", description="")

@bot.slash_command(name="panama", description="Commands related to Panama")
async def panama(inter):
    pass

@panama.sub_command(name="relations", description="Shows Panama's relationships with other nations")
async def relations(inter):
    embedVar = disnake.Embed(
        title="Panama Relations | 🇵🇦",
        description="",
        color=0xffffff)

    embedVar.add_field(name="Alliances", value=f"```{formatlist('allies')}```", inline=True)
    embedVar.add_field(name="Enemies", value=f"```{formatlist('enemies')}```", inline=True)

    embedVar.set_footer(
        text=f"{version} Programmed by CreVolve",
        icon_url="https://data2.nssmag.com/images/galleries/8352/ccj4kiow0aav5gi-20150410004412.png"
    )

    await inter.send(embed=embedVar)

cotwRole = None

############################## SET COMMANDS #############################

@bot.slash_command(name="set", description="Set a citizen of the week, Notifications Channel or Notifications Status")
async def set(inter):
    pass

############################# COTW SETTINGS #############################

@set.sub_command(name="cotw", description="Set the citizen of the week", moderate_members=True)
async def citizenoftheweek(inter, citizen: disnake.Member):
    global cotwRole
    if cotwRole is not None:
        members_with_role = [member for member in inter.guild.members if cotwRole in member.roles]
        for member in members_with_role:
            await member.remove_roles(cotwRole)
        await citizen.add_roles(cotwRole)
        await inter.send(f"Citizen of the week set to {citizen.mention}")
    else:
        await inter.send(f"Citizen of the week role not set, please use /set cotw-role")


@set.sub_command(name="cotw-role", description="Set the citizen of the week role", moderate_members=True)
async def citizenoftheweekrole(inter, role: disnake.Role):
    global cotwRole
    cotwRole = role.id
    await inter.send(f"Citizen of the week role set to {role.mention}")

############################### ROLE SETUP ###############################
@set.sub_command(name="admin-role", description="Set the admin role for special commands")
async def moderatorrole(inter, role: disnake.Role):
    UpdateServer(inter, adminRole=int(role.id))
    await inter.send(f"Admin role set to {role.mention}")
@set.sub_command(name="citizen-role", description="Set the citizen role for verification")
async def citizenrole(inter, role: disnake.Role):
    UpdateServer(inter, citizenRole=int(role.id))
    await inter.send(f"Citizen role set to {role.mention}")
    
############################# NOTIF SETTINGS #############################

@set.sub_command(name="channel", description="Set the notifications channel")
async def notificationschannel(inter, sendchannel: disnake.TextChannel):
    await inter.send(f"Notifications channel set to {sendchannel.mention}")
    print(f"{inter.guild.name} has set their notifications channel to {sendchannel.name}")

    channelID = int(sendchannel.id)
    UpdateServer(inter, notificationsChannel=channelID)


STATUS = ["True", "False"]

async def autocomp_langs(inter: disnake.ApplicationCommandInteraction, user_input: str):
    return [lang for lang in STATUS if user_input.lower() in lang]

@set.sub_command(name="notify", description="Set the notifications status")
async def notificationsstatus(inter, status: str = commands.param(autocomplete=autocomp_langs)):
    global STATUS
    if status not in STATUS:
        await inter.send(f"Please use either True or False")


    if status == "True":
        await inter.send("Notifications enabled")
        print(f"Notifications have been enabled for guild: {inter.guild}")

    else:
        print(f"Notifications disabled for guild: {inter.guild}")
        await inter.send("Notifications have been disabled")

    UpdateServer(inter, notificationsStatus=status)

@bot.slash_command(name="setup", description="Quick setup for Notifications")
async def setup(inter):

    await inter.send("Quick Setup Complete")

############################## VERIFICATION ##############################

@bot.slash_command(name="verify", description="Link a Discord user to a Minecraft User")
async def verify(inter, member: disnake.Member, username):
    import os
    verifications_path = "Configurations/verifications.json"
    storage_path = "Configurations/storage.json"

    # Load verifications and storage data
    with open(verifications_path, "r") as storage:
        try:
            registered = json.load(storage)
        except json.JSONDecodeError:
            registered = {}  # Default to an empty dictionary if the file is corrupted

    with open(storage_path, "r") as storage:
        pullStorage = json.load(storage)

    try:
        adminRole = pullStorage[str(inter.guild.id)]["adminRole"]
        if adminRole is None:
            await inter.send("Admin role not set, please use /set admin-role")
        else:
            adminRole = inter.guild.get_role(int(adminRole))
            if adminRole in inter.author.roles:
                # Check if Minecraft username is already registered (case-insensitive)
                if any(username.lower() == registered_username.lower() for registered_username in registered.values()):
                    await inter.send(f"Minecraft username {username} is already registered to a Discord user.")
                    return
                if str(member.id) in registered:
                    await inter.send(f"Discord user {member.mention} is already registered to a Minecraft user.")
                    return

                # Request the player's data
                response = requests.get(f"https://api.earthmc.net/v2/aurora/residents/{username}")
                try:
                    playerDirectory = response.json()

                    # Check if the player is part of Panama
                    if playerDirectory.get("nation") == "Panama":
                        await inter.send(f"{member.mention} successfully linked to {username}")

                        # Update the member's nickname
                        await member.edit(nick=f"{playerDirectory['name']} | {playerDirectory['town']}")
                        await member.add_roles(inter.guild.get_role(int(pullStorage[str(inter.guild.id)]["citizenRole"])))

                        # Update the verifications dictionary
                        registered[str(member.id)] = playerDirectory['name']

                        # Write the updated data to the file
                        with open(verifications_path, "w") as storage:
                            json.dump(registered, storage, indent=4)

                        print(f"Updated verifications: {registered}")
                    else:
                        await inter.send(f"{username} is not part of the Panama nation.")

                except (KeyError, json.JSONDecodeError):
                    await inter.send(f"{username} is not registered in EarthMC or does not exist.")

            else:
                await inter.response.send_message(f"You lack the permissions to use this", ephemeral=True)
    except KeyError:
        await inter.send("Admin role not set, please use /set admin-role")


############################## ONLINE EMBED ##############################

@set.sub_command(name="online-embed", description="Set the online embed channel")
async def onlineembed(inter, embedchannel: disnake.TextChannel):
    global currentEmbed
    if currentEmbed is None:
        messageToAppend = await embedchannel.send("There is no current embed avaible; this will be a placeholder for when there is one!")
        print(f"Online list created in {inter.guild} with message id: {messageToAppend.id}")
    else:
        messageToAppend = await embedchannel.send(embed=currentEmbed)
        print(f"Online list created in {inter.guild} with message id: {messageToAppend.id}")

    UpdateServer(inter, embedMessage=messageToAppend.id, embedChannelDomain=embedchannel.id)

    await inter.response.send_message(f"Embed Creation Successful", ephemeral=True)

@bot.slash_command(name="delete", description="Remove Something")
async def delete(inter):
    pass

@delete.sub_command(name="online-embed", description="Delete the current online list embed")
async def delonlineembed(inter):

    UpdateServer(inter, embedMessage=None, embedChannelDomain=None)

############################## EMBED LOOP ##############################

@tasks.loop(seconds=30)
async def online():
    newpanamaDirectory = requests.get("https://api.earthmc.net/v2/aurora/nations/panama").json()
    global currentEmbed
    OnlinePlayers = []
    numRes = 0
    async with aiohttp.ClientSession() as session:
        estimatedTime = round(len(newpanamaDirectory["residents"]) / 60 * 2) / 2
        print(f"Estimated time to update: {estimatedTime} minutes")
        for player in newpanamaDirectory["residents"]:
            try:
                async with session.get(f"https://api.earthmc.net/v2/aurora/residents/{player}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        numRes += 1
                        if data["status"]["isOnline"] == True:
                            if "title" in data and data["title"]:  # Check if 'title' exists and is not empty
                                title = re.sub(r"<#[0-9a-fA-F]{6}>", "", data["title"])
                                OnlinePlayers.append(f"{title} {player}")
                            else:
                                OnlinePlayers.append(player)
                            print(f"Player {player} is online {numRes}/{len(newpanamaDirectory['residents'])}")
                        else:
                            print(f"Player {player} is offline {numRes}/{len(newpanamaDirectory['residents'])}")
                    else:
                        print(
                            f"Failed to fetch data for {player} (HTTP {resp.status}) {numRes}/{len(newpanamaDirectory['residents'])}")
            except Exception as e:
                print(f"We encountered an error while fetching {player}: {e}")
            await asyncio.sleep(1)
    now = datetime.datetime.now(timezone)
    print(OnlinePlayers)
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")

    SendEmbed = disnake.Embed(
        title="Online Panama Players",
        description=f"Will update in roughly {estimatedTime} min - Last updated: {formatted_time} EST",
        color=0x00ff00
    )
    formattedOnlinePlayers = '\n'.join(
        '{}: {}'.format(i + 1, item.replace("_", " ")) for i, item in enumerate(OnlinePlayers))
    SendEmbed.add_field(name=f"Online Players [{len(OnlinePlayers)}]", value=f"```{formattedOnlinePlayers}```")

    SendEmbed.set_footer(
        text=f"{version} Programmed by CreVolve",
        icon_url="https://data2.nssmag.com/images/galleries/8352/ccj4kiow0aav5gi-20150410004412.png"
    )
    with open("Configurations/storage.json", "r") as f:
        data = json.load(f)
    for entry in data.values():
        # Check if "embedMessage" exists in entry and is not None or the string "None"
        if entry.get("embedMessage") and entry.get("embedChannelDomain") not in [None, "None"]:
            messageID = entry.get("embedMessage")
            channelID = entry.get("embedChannelDomain")
            try:
                embedChannel = bot.get_channel(int(channelID))

                if embedChannel is not None:
                    messageToSend = await embedChannel.fetch_message(int(messageID))

                    if messageToSend is not None:
                        await messageToSend.edit(embed=SendEmbed)
                else:
                    print(f"Message with ID {messageID} could not be found.")
            except (ValueError, disnake.HTTPException) as e:
                print(
                    f"Unable to fetch message with ID {messageID}. Error: {e}")
        else:
            print("No notifications channel set or 'embedMessage' is None for this guild.")

    currentEmbed = SendEmbed


############################## NOTIFY LOOP ##############################

checks = [
    ("residents", "residents.json"),
    ("towns", "towns.json"),
    ("enemies", "enemies.json"),
    ("allies", "allies.json")
]

@tasks.loop(minutes=2)
async def FileCheck():
    print("FileCheck loop started.")
    newpanamaDirectory = requests.get("https://api.earthmc.net/v2/aurora/nations/panama").json()

    positiveResidentsDifferences = []
    positiveTownsDifferences = []
    positiveEnemiesDifferences = []
    positiveAlliesDifferences = []
    negativeResidentsDifferences = []
    negativeTownsDifferences = []
    negativeEnemiesDifferences = []
    negativeAlliesDifferences = []


    try:
        for i, j in checks:
            differences = []
            with open(f"DataStorage/{j}") as f:
                currentMemory = json.load(f)
            for element in currentMemory:
                if element not in newpanamaDirectory[i]:
                    differences.append(element)

            if len(differences) == 0:
                for element in newpanamaDirectory[i]:
                    if element not in currentMemory:
                        differences.append(element)

                if len(differences) == 0:
                    print(f"No differences found in {j}")
                else:
                    print(f"Differences found in {j}")
                    if i == "residents":
                        positiveResidentsDifferences.extend(differences)
                    elif i == "towns":
                        positiveTownsDifferences.extend(differences)
                    elif i == "enemies":
                        positiveEnemiesDifferences.extend(differences)
                    else:
                        positiveAlliesDifferences.extend(differences)
            else:
                print(f"Differences found in {j}")
                if i == "residents":
                    negativeResidentsDifferences.extend(differences)
                elif i == "towns":
                    negativeTownsDifferences.extend(differences)
                elif i == "enemies":
                    negativeEnemiesDifferences.extend(differences)
                else:
                    negativeAlliesDifferences.extend(differences)
            with open(f"DataStorage/{j}", "w") as f:
                print("Updating JSON")
                json.dump(newpanamaDirectory[i], f, indent=4)
    except disnake.HTTPException as e:
        print(f"Failed to send message: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    with open("Configurations/storage.json", "r") as f:
        data = json.load(f)
    for entry in data.values():
        print(entry)
        if entry["notificationsChannel"] != None and entry["notificationsStatus"] == "True":
            channel_id = entry.get("notificationsChannel")
            if channel_id and channel_id != "None":
                try:
                    channel = await bot.fetch_channel(int(channel_id))
                except disnake.HTTPException:
                    print(
                        f"Unable to fetch channel with ID {channel_id}. It might not exist or the bot lacks permissions.")
                    continue  # Move to the next guild if the channel isn't accessible
            else:
                print("No notifications channel set or channel is None for this guild.")
                continue

            if len(positiveResidentsDifferences) != 0:
                refinedlist = ", ".join(map(str, positiveResidentsDifferences))
                await channel.send(f"**{refinedlist}** has/have joined panama")
            if len(positiveTownsDifferences) != 0:
                refinedlist = ", ".join(map(str, positiveTownsDifferences))
                await channel.send(f"The town(s) **{refinedlist}** has/have been established within panama")
            if len(positiveEnemiesDifferences) != 0:
                refinedlist = ", ".join(map(str, positiveEnemiesDifferences))
                await channel.send(f"The nation(s) **{refinedlist}** has/have been declared enemies of panama")
            if len(positiveAlliesDifferences) != 0:
                refinedlist = ", ".join(map(str, positiveAlliesDifferences))
                await channel.send(f"The nation(s) **{refinedlist}** has/have been declared allies of panama")

            if len(negativeResidentsDifferences) != 0:
                refinedlist = ", ".join(map(str, negativeResidentsDifferences))
                await channel.send(f"**{refinedlist}** has/have left panama")
            if len(negativeTownsDifferences) != 0:
                refinedlist = ", ".join(map(str, negativeTownsDifferences))
                await channel.send(f"The town(s) **{refinedlist}** has/have been disbanded")
            if len(negativeEnemiesDifferences) != 0:
                refinedlist = ", ".join(map(str, negativeEnemiesDifferences))
                await channel.send(f"The nation(s) **{refinedlist}** is/are no longer enemies of panama")
            if len(negativeAlliesDifferences) != 0:
                refinedlist = ", ".join(map(str, negativeAlliesDifferences))
                await channel.send(f"The nation(s) **{refinedlist}** is/are no longer allies of panama")




configFileChecks = ["guildNotifStatus", "guildNotifChannels", "guildEmbedChannel"]


############################## INITIALIZATION ##############################

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

    ensure_directory("DataStorage")
    ensure_directory("Configurations")


    for name, file in checks:
        file_path = f"DataStorage/{file}"
        if not os.path.exists(file_path):
            print(f"File '{file_path}' not found, creating it.")
            with open(file_path, "w") as f:
                json.dump(panamaDirectory[name], f, indent=4)

    if os.path.exists("Configurations/storage.json"):
        print("Storage file found.")
    else:
        with open("Configurations/storage.json", "w") as f:
            print("Configuration File not found, creating it.")
            json.dump({}, f)

    if os.path.exists("Configurations/verifications.json"):
        print("Verifications file found.")
        with open(f"Configurations/verifications.json", "r") as storage:
            VerificationCache = json.load(storage)
        print(VerificationCache)
    else:
        with open("Configurations/verifications.json", "w") as f:
            print("Verifications File not found, creating it.")
            json.dump({}, f)
            VerificationCache = {}

    

    FileCheck.start()
    online.start()


bot.run(os.getenv('BOT-TOKEN'))

