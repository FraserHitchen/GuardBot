'''
Created on 24 Oct 2020

An auto-moderation bot.

@author: Fraser
'''
from discord.ext import commands
import traceback
import sys
import discord
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
    
async def banUserForMessage(message):
    '''Punish user for a specified message'''
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
    punishCap = punishment.capitalize()
    await outChannel.send(embed=discord.Embed(title=f"User {punishCap}", description = f"User {user} has been {punishment} for the following message: {message.content}"))
    sent = await user.send(embed=discord.Embed(title=f"{punishCap}", description=(f"You have been {punishment} from {guild} due to the message \"{message.content}\". If you think this was a mistake reply to this message with your explanation within 5 minutes.")))
    
    def check(message):
        return message.channel == sent.channel
    
    response = await bot.wait_for('message', check=check, timeout=300)
    await outChannel.send(embed=discord.Embed(title="Banned User Response", description = f"{punishCap} user {user} has given this explanation for why their ban/kick was invalid: {response.content}"))

@bot.event
async def on_ready():
    '''Code to run on bot startup'''
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the streets of Erilea"))

@bot.event
async def on_message(message):
    '''Check for banned words'''
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
@commands.check_any(commands.has_permissions(administrator=True), commands.is_owner(), commands.has_role("Bot Team"))
async def add_word(ctx, *, newWord):
    '''Add a word to the list of banned words.'''
    
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
        

     
@bot.command(name='removeword')
@commands.check_any(commands.has_permissions(administrator=True), commands.is_owner(), commands.has_role("Bot Team"))
async def remove_word(ctx, *, newWord):
    '''Remove a word from the list of banned words.'''
    
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
                if line.strip("\n") != newWord:
                    file.write(line.strip("\n")+"\n")
            file.close()
            
            await ctx.send(embed=discord.Embed(title="Word Removed", description=("The word was successfully removed from the list of banned word.")))
            return
        
    await ctx.send(embed=discord.Embed(title="Cannot Find Word", description=("This word could not be found in the list of banned words.")))
  
@bot.command(name='outputchannel')
@commands.check_any(commands.has_permissions(administrator=True), commands.is_owner(), commands.has_role("Bot Team"))
async def output_channel(ctx, *, newChannel: discord.TextChannel):  
    '''Set the channel for bot output.'''
    
    global outChannel
    await ctx.message.delete()
    
    outChannel = newChannel
    await ctx.send(embed=discord.Embed(title="Output Channel Changed", description=("The output channel was successfully changed.")))
        
@bot.command(name='listwords')
@commands.check_any(commands.has_permissions(administrator=True), commands.is_owner(), commands.has_role("Bot Team"))
async def list_words(ctx): 
    '''List the banned words.'''
    
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
                  
@bot.command(name='prefix')
@commands.check_any(commands.has_permissions(administrator=True), commands.is_owner(), commands.has_role("Bot Team"))
async def change_prefix(ctx, *, newPrefix):  
    '''Change the bot prefix.'''
    
    
    await ctx.message.delete() 
    newPrefix = newPrefix.strip()
    if newPrefix != "":
        try:
            bot.command_prefix = newPrefix
        except:        
            await ctx.send(embed=discord.Embed(title="Invalid Prefix", description=("Prefix could not be changed.")))
        else:
            await ctx.send(embed=discord.Embed(title="Prefix Changed", description=("The prefix has successfully been changed to {prefix}".format(prefix=newPrefix))))
                         
@bot.command(name='punishment')
@commands.check_any(commands.has_permissions(administrator=True), commands.is_owner(), commands.has_role("Bot Team"))
async def set_punishment(ctx, *, newPunish):   
    '''Set the punishment (ban, kick or warn). Default is ban.'''
      
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
 

@bot.command(name="help", hidden=True)
async def help(ctx, commandName=""):
    '''Returns all commands available'''
    helptext = ""
    if commandName == "":
        helptext += "While online the bot will automatically remove banned words and ban the users who write them. Make sure to run g!outputchannel first! \n\n"
        for command in bot.commands:
            helptext += f"**`{command}`:** {command.help}\n" 
        
    else:
        for command in bot.commands:
            print(command.name)
            if command.name == commandName:
                print("made it")
                helptext += f"**`{command}`:** {command.help}\n"
                print(helptext)
    await ctx.send(embed=discord.Embed(title="Help", description= f"{helptext}"))
                
    
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(embed=discord.Embed(title="Error: Missing Argument", description="You seem to be missing the required argument for this command."))
    elif isinstance(error, commands.errors.CheckAnyFailure):
        await ctx.send(embed=discord.Embed(title="Error: No Permission", description="You do not have the required permissions to run this command."))
    elif isinstance(error, commands.errors.ChannelNotFound):
        await ctx.send(embed=discord.Embed(title="Error: Invalid Channel", description=("The given channel could not be found.")))
        
bot.run(TOKEN)