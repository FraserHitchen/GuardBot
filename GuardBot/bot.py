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


intents = discord.Intents(messages=True, guilds=True, members=True)

TOKEN = os.getenv('DISCORD_TOKEN')


bot = commands.Bot(command_prefix='g!', intents=intents)

bannedWords = []
file = open("Banned-Words.txt", "r")
for word in file:
    word = word.strip()
    bannedWords.append(word)
file.close()

responseChannel = None

def check(author):
    def predicate(ctx): 
        if ctx.author != author:
            return False
        try: 
            int(ctx.content) 
            return True 
        except ValueError: 
            return False
    return predicate

def is_admin():
    def predicate(ctx):
        channel = ctx.channel
        return ctx.author.permissions_in(channel).administrator
    return commands.check(predicate)

async def banUserForMessage(message):
    user = message.author
    guild = message.channel.guild
    #await guild.ban(user, reason="Offensive Language")
    await user.send(embed=discord.Embed(title="Banned", description=("You have been banned from {guild} due to the message \"{message}\". If you think this was a mistake reply to this message with your explaination within 5 minutes.".format(guild=message.channel.guild.name, message = message.content))))
    response = await bot.wait_for('message', check=check, timeout=300)
    await responseChannel.send(embed=discord.Embed(title="Banned User Response", description = "Banned user {user} has given this explaination for why their ban was invalid: {response}".format(user=user, response=response.content)))
    
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
            if word in contentStr:
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
        await ctx.send(embed=discord.Embed(title="Word Added", description=("The word was successfully added to the list of banned word.")))

# Remove word from banned list        
@bot.command(name='removeword')
@is_admin()
async def remove_word(ctx, *, newWord):
    
    await ctx.message.delete()
    
    newWord = newWord.strip()
    for word in bannedWords:
        if newWord == word: 
            bannedWords.remove(word)   
            await ctx.send(embed=discord.Embed(title="Word Removed", description=("The word was successfully removed to the list of banned word.")))
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

    
bot.run(TOKEN)