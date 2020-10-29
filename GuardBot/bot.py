'''
Created on 24 Oct 2020

An auto-moderation bot.

@author: Fraser
'''
from discord.ext import commands
import discord
import numpy as np
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents(messages=True, guilds=True, members=True)
bot = commands.Bot(command_prefix='g!', intents=intents)
bot.remove_command('help')

# Get banned words into a list
bannedWords = []
file = open("Banned-Words.txt", "r")
for word in file:
    word = word.strip()
    bannedWords.append(word)
file.close()

outChannel = None
punishMode = "ban"

# check if user using command is an admin
def is_admin():
    def predicate(ctx):
        channel = ctx.channel
        return ctx.author.permissions_in(channel).administrator
    return commands.check(predicate)

# check if message is in a private chat
def is_dm(message):
    def predicate(ctx):
        return str(ctx.channel.type) == "private"

# ban user for a specified message
async def banUserForMessage(message):
    user = message.author
    guild = message.channel.guild
    
    punishment = "banned"
    if punishMode == "ban":
        punishment = "banned"
        #await guild.ban(user, reason="Offensive Language")      
    elif punishMode == "kick":
        punishment = "kicked"
        #await guild.kick(user, reason="Offensive Language")
    elif punishMode == "warn":
        punishment = "warned"
    await outChannel.send(embed=discord.Embed(title="User {punishCap}".format(punishCap=punishment.capitalize()), description = "User {user} has been {punishment} for the following message: {content}".format(user=user, punishment=punishment, content=message.content)))
    sent = await user.send(embed=discord.Embed(title="{punishCap}".format(punishCap=punishment.capitalize()), description=("You have been {punishment} from {guild} due to the message \"{message}\". If you think this was a mistake reply to this message with your explanation within 5 minutes.".format(punishment=punishment, guild=message.channel.guild.name, message = message.content))))
    
    def check(message):
        return message.channel == sent.channel
    
    response = await bot.wait_for('message', check=check, timeout=300)
    await outChannel.send(embed=discord.Embed(title="Banned User Response", description = "{punishCap} user {user} has given this explaination for why their ban/kick was invalid: {response}".format(punishCap=punishment.capitalize(), user=user, response=response.content)))

# Code to run on bot startup
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the streets of Erilea"))

# Check for banned words
@bot.event
async def on_message(message):
    
    if message.author != bot.user and message.content[:2] != "g!" and str(message.channel.type) != "private" :
        channel = message.channel
        contentStr = message.content
        contentStr.replace(" ", "")
        for word in bannedWords:
            if word in contentStr and word != "\n":
                await message.delete()
                await channel.send(embed=discord.Embed(title="Stop Right There, Criminal Scum!", description=("{user}'s message contained a banned word and has been deleted.".format(user=message.author.name))))              
                await banUserForMessage(message)
    await bot.process_commands(message)  

# Add word to banned list          
@bot.command(name='addword')
@is_admin()
async def add_word(ctx, *, newWord):
    
    await ctx.message.delete()
    
    newWord = newWord.strip()
    for word in bannedWords:
        if newWord == word:    
            await ctx.send(embed=discord.Embed(title="Invalid Word", description=("This word is already on the list of banned words.")))
            return
        
    try:
        bannedWords.append(newWord)
    except:
        await ctx.send(embed=discord.Embed(title="Invalid Word", description=("This word could not be added to the list of banned words, please try again.")))
    else:
        file = open("Banned-Words.txt", "a")
        file.write(newWord+"\n")
        file.close()
        await ctx.send(embed=discord.Embed(title="Word Added", description=("The word was successfully added to the list of banned words.")))
        

# Remove word from banned list        
@bot.command(name='removeword')
@is_admin()
async def remove_word(ctx, *, newWord):
    
    await ctx.message.delete()
    
    newWord = newWord.strip()
    for word in bannedWords:
        if newWord == word: 
            bannedWords.remove(word) 
             
            file = open("Banned-Words.txt", "r")
            lines = file.readlines()
            file.close() 
            
            file = open("Banned-Words.txt", "w")
            for line in lines:
                print(line)
                if line.strip("\n") != newWord:
                    file.write(line.strip("\n")+"\n")
            file.close()
            
            await ctx.send(embed=discord.Embed(title="Word Removed", description=("The word was successfully removed from the list of banned word.")))
            return
        
    await ctx.send(embed=discord.Embed(title="Cannot Find Word", description=("This word could not be found in the list of banned words.")))

# Set Output Channel    
@bot.command(name='outputchannel')
@is_admin()
async def output_channel(ctx, *, newChannel):  
    global outChannel
    await ctx.message.delete()
    try: 
        newChannel = int(newChannel[2:-1]) 
        outChannel = bot.get_channel(newChannel)
    except:
        await ctx.send(embed=discord.Embed(title="Output Channel Change Unsuccessful", description=("The given channel was not valid.")))
    else:
        await ctx.send(embed=discord.Embed(title="Output Channel Changed", description=("The output channel was successfully changed.")))

# List banned words        
@bot.command(name='listwords')
@is_admin()
async def list_words(ctx): 
    await ctx.message.delete() 
    
    def check(user):
        return user == ctx.message.author
    
    botMsg = await ctx.send(embed=discord.Embed(title="Warning", description=("The list of banned words is explicit, are you sure you want to post it here? (yes/no).")))
    reply = await bot.wait_for('message', check=check, timeout=180)
    if reply.content == "yes":     
        await botMsg.delete()
        await reply.delete()
        words = ""
        for word in bannedWords:
            words += word + ", "
        words = words[:-2]
        await ctx.send(embed=discord.Embed(title="Banned Words", description=words))
    elif reply.content == "no":
        await botMsg.delete()
        await reply.delete()   
    
# Change prefix                
@bot.command(name='prefix')
@is_admin()
async def change_prefix(ctx, *, newPrefix):  
    await ctx.message.delete() 
    newPrefix = newPrefix.strip()
    if newPrefix != "":
        try:
            bot.command_prefix = newPrefix
        except:        
            await ctx.send(embed=discord.Embed(title="Invalid Prefix", description=("Prefix could not be changed.")))
        else:
            await ctx.send(embed=discord.Embed(title="Prefix Changed", description=("The prefix has successfully been changed to {prefix}".format(prefix=newPrefix))))
            
# Change prefix                
@bot.command(name='help')
async def help(ctx):  
    await ctx.send(embed=discord.Embed(title="Command List", description="While online the bot will automatically remove banned words and ban the users who write them. Make sure to run g!responsechannel first! \n **g!addword:** Add a word to the list of banned words.\n **g!removeword:** Remove a word from the list of banned words.\n **g!outputchannel:** Set the channel for bot outputs.\n **g!listwords:** List the banned words.\n **g!prefix:** Change the bot prefix.\n **g!punishment:** Set the punishment (ban, kick or warn).")) 

# Toggle punishment                
@bot.command(name='punishment')
@is_admin()
async def set_punishment(ctx, *, newPunish):
    await ctx.message.delete() 
    global punishMode
    if newPunish == "ban":
        punishMode = "ban"
        await ctx.send(embed=discord.Embed(title="Punishment Changed", description="Users who say a banned word will now be banned."))
    elif newPunish == "kick":
        punishMode = "kick"
        await ctx.send(embed=discord.Embed(title="Punishment Changed", description="Users who say a banned word will now be kicked."))
    elif newPunish == "warn":
        punishMode = "warn"
        await ctx.send(embed=discord.Embed(title="Punishment Changed", description="Users who say a banned word will now be warned."))
    else:
        await ctx.send(embed=discord.Embed(title="Input Not Recognised", description="That input didn't match one of the punishment options. Please recall the command with either ban, kick or warn."))
   
bot.run(TOKEN)