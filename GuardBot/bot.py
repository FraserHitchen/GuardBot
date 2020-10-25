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

bannedWords = []
file = open("Banned-Words.txt", "r")
for word in file:
    word = word.strip()
    bannedWords.append(word)
file.close()

responseChannel = None
punishMode = "ban"

def is_admin():
    def predicate(ctx):
        channel = ctx.channel
        return ctx.author.permissions_in(channel).administrator
    return commands.check(predicate)

def is_dm(message):
    def predicate(ctx):
        return str(ctx.channel.type) == "private"

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
        
    sent = await user.send(embed=discord.Embed(title="Banned", description=("You have been {punishment} from {guild} due to the message \"{message}\". If you think this was a mistake reply to this message with your explaination within 5 minutes.".format(punishment=punishment, guild=message.channel.guild.name, message = message.content))))
    
    def check(message):
        return message.channel == sent.channel
    
    response = await bot.wait_for('message', check=check, timeout=300)
    await responseChannel.send(embed=discord.Embed(title="Banned User Response", description = "{punishCap} user {user} has given this explaination for why their ban/kick was invalid: {response}".format(punishCap=punishment.capitalize(), user=user, response=response.content)))
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

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

# Set Response Channel    
@bot.command(name='responsechannel')
@is_admin()
async def response_channel(ctx, *, newChannel):  
    global responseChannel
    await ctx.message.delete()
    try: 
        newChannel = int(newChannel[2:-1]) 
        responseChannel = bot.get_channel(newChannel)
    except:
        await ctx.send(embed=discord.Embed(title="Response Channel Change Unsuccessful", description=("The given channel was not valid.")))
    else:
        await ctx.send(embed=discord.Embed(title="Response Channel Changed", description=("The response channel was successfully changed.")))

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
    await ctx.send(embed=discord.Embed(title="Command List", description="While online the bot will automatically remove banned words and ban the users who write them. Make sure to run g!responsechannel first! \n **g!addword:** Add a word to the list of banned words.\n **g!removeword:** Remove a word from the list of banned words.\n **g!responsechannel:** Set the channel for ban responses.\n **g!listwords:** List the banned words.\n **g!prefix:** Change the bot prefix.\n **g!togglepunish:** Toggles punishment between ban and kick (defualt ban)")) 

# Toggle punishment                
@bot.command(name='togglepunish')
@is_admin()
async def toggle_punish(ctx):
    await ctx.message.delete() 
    global punishMode
    if punishMode == "ban":
        punishMode = "kick"
        await ctx.send(embed=discord.Embed(title="Punishment Toggled", description="Users who say a banned word will now be kicked."))
    elif punishMode == "kick":
        punishMode = "ban"
        await ctx.send(embed=discord.Embed(title="Punishment Toggled", description="Users who say a banned word will now be banned."))
   
bot.run(TOKEN)