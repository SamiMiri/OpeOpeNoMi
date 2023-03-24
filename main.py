import os, discord
from discord.ext import commands
import mimetypes
import requests
from io import BytesIO
from caption import caption_image
from discord import Color
import re
import asyncio
from discord import Spotify
import time
from logging import INFO, basicConfig

basicConfig(level=INFO)





"""
link for invite : https://discord.com/oauth2/authorizeclient_id=1067255245790527649&scope=bot
"""
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SUPPORTED_MIMETYPES = ["image/jpeg", "image/png", "image/webp"]


intents = discord.Intents.all()


bot = commands.Bot(command_prefix='!ope ',intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="Deepwoken"))
    print([command.name for command in bot.commands])

@bot.command(name="caption", brief="Add a caption to an image.", captionhelp="""Add a caption to an attached image. Example:
             
!caption "Hello world!" <attached image>

Supported image types: PNG, JPEG, WebP
             """)
async def caption(ctx, caption_text):
    # Must have caption text
    if not caption_text:
        await ctx.message.reply("Please include some caption text after the `!caption` command. For example `!caption \"Hello world!\"")
        return
    
    # Must have a file attached
    if ctx.message.attachments:
        image_url = ctx.message.attachments[0].url
    else:
        await ctx.message.reply("Please attach an image for me to caption.")
        return

    # File must be an image
    if mimetypes.guess_type(image_url)[0] not in SUPPORTED_MIMETYPES:
        await ctx.message.reply("Sorry, the file you attached is not a supported image format. Please upload a PNG, JPEG or WebP image.")
        return

    # Fetch image file
    response = requests.get(image_url)

    # Store image file name
    image_filename = ctx.message.attachments[0].filename

    # Caption image
    final_image = caption_image(BytesIO(response.content), caption_text)

        # Send reply
    
    await ctx.message.reply(file=discord.File(BytesIO(final_image), filename=f"captioned-{image_filename}"))
    await ctx.message.delete()



# -------------------

# check if a role is not being used, and delete it
# this waits a bit before checking since discord
# likes to take some time before reporting changes
async def sleep_check_and_delete_role(role):
    await asyncio.sleep(10) # give time before checking
    return await check_and_delete_role(role)

# this is only called directly from the purge command
async def check_and_delete_role(role):
    if len(role.members) == 0:
        await role.delete()
        return True
    return False

# use requests to query the colourlovers API
async def color_lover_api(keywords):
    keywords = keywords.replace(" ", "+") # they use + instead of %20
    url = f"http://www.colourlovers.com/api/colors?keywords={keywords}&numResults=1&format=json"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    hexcode = "#" + requests.get(url, headers=headers).json()[0]["hex"] # fancy
    return hexcode

# remove colors, returns the number of 
# roles removed from the specified user
# (generally 1 but jic one gets stuck)
async def remove_colors(ctx, author):
    color_roles = []
    re_color = re.compile(r'^\#[0-9A-F]{6}$')
    for role in author.roles:
        # only remove color roles
        if re_color.match(role.name.upper()):
            color_roles.append(role)

    # once all the roles are collected,
    # remove them from the user
    for role in color_roles:
        await author.remove_roles(role)
        # if the role is no longer being used,
        # delete it. run it async as there's 
        # a 10 second (or so) wait in the check
        asyncio.create_task(sleep_check_and_delete_role(role))

    return len(color_roles)

# simple source command
@bot.command()
async def source(ctx):
    await ctx.send("Color function:     https://github.com/Savestate2A03/SimpleDiscordColorBot>")
    await ctx.send("Caption function:   https://replit.com/@ritza/ImageCaptionBot#main.py")
    await ctx.send("The ABA, Genshin, and lil children option were made by yours truly(WIP) ")
    await ctx.send("Ping Function       https://github.com/TheMingus/Cat_Bot/blob/main/main.py")
    await ctx.send("Spotify Function    https://github.com/wardoflores/Python-Discord-bot/blob/main/main.py (improvement coming soon)")
    await ctx.send("The dozens of hours that I spent on StackOverflow/Reddit")

# simple help command
@bot.command()
async def colorhelp(ctx):
    await ctx.send("Go here and pick out a color : "
        "<https://htmlcolorcodes.com/color-picker/>, then run the command "
        "`!color #RRGGBB` where '#RRGGBB' is the hex code you want !\n"
        "You can also use general descriptions of colors (ex: `!ope color dark purple`) "
        "thanks to the colourlovers API, so shoutouts to them !")

@bot.command(name="color", aliases=["colour"])
async def color(ctx, *color):
    # if the command is improperly
    # formatted, invoke help and exit
    if len(color) == 0:
        await help.invoke(ctx)
        return

    message = ctx.message
    author  = message.author 
    guild   = message.guild
    color_lover = False # flag if used the colourlovers API

    color = " ".join(color)
    color = color.upper() # makes things easier

    if color == "remove":
        # see if any roles were removed
        # and let the user know how the removal
        # process went.
        removed = await remove_colors(ctx, author)
        if removed > 0:
            await ctx.send("Rights brought back")
        else:
            await ctx.send("no color role to remove !")
        return

    # look for hex code match
    re_color = re.compile(r'^\#[0-9A-F]{6}$')
    if not re_color.match(color):
        # if not a hex code, use colourlovers API
        color_lover = True 
        color = await color_lover_api(color)

    # remove all color roles in preperation
    # for a new color role
    await remove_colors(ctx, author)

    assigned_role = None

    # check if the role already exists. if 
    # it does, assign that instead of 
    # making a new role
    for role in guild.roles:
        if role.name.upper() == color:
            assigned_role = role

    # if we didn't find the role, make it
    if assigned_role == None:
        red   = int(color[1:3], 16) #.RR....
        green = int(color[3:5], 16) #...GG..
        blue  = int(color[5:7], 16) #.....BB
        assigned_role = await guild.create_role(
            name=color, 
            color=discord.Color.from_rgb(red, green, blue))

    # assign the role we found/created
    await author.add_roles(assigned_role)

    await ctx.send(f"colorized !")

# remove colors that somehow dont get deleted
@bot.command()
async def purge(ctx):
    message = ctx.message
    author  = message.author 
    guild   = message.guild
    allowed = author.guild_permissions.manage_roles

    if not allowed:
        await ctx.send("you can't manage roles !")
        return

    # discord throttles a lot of stuff here
    # so going through all the roles takes a little while
    await ctx.send(f"purging unassigned colors ! ... this may take a sec ...")

    re_color = re.compile(r'^\#[0-9A-F]{6}$')
    num_deleted = 0

    roles = guild.roles
    progress = await ctx.send(f"progress: 0/{len(roles)}")
    iterations = 0

    for role in roles:
        if re_color.match(role.name): # if a color role
            deleted = await check_and_delete_role(role)
            if deleted:
                num_deleted += 1
        iterations += 1
        # edit our previous progress message (fancy)
        await progress.edit(content="progress: "
                f"{iterations}/{len(roles)}")

    # final report
    await ctx.send(f"removed {num_deleted} unassigned colors !")

# -------------------
#Spotify info display.

@bot.command(
    brief="Displays user Spotify activity.",
    description="Only works if the activity displayed under User is 'Listening to Spotify.")
async def spotify(ctx, *, user: discord.Member = None):
    

    if user == None:
        user = ctx.author
        pass

    if user.activities:
        for activity in user.activities:
            if isinstance(activity, Spotify):
                embed = discord.Embed(
                    title = f"{user.name}'s Spotify", 
                    description = "Listening to {}".format(activity.title), 
                    color = discord.Colour.green())
                embed.set_thumbnail(url=activity.album_cover_url)
                embed.add_field(name="Artist", value=activity.artist)
                embed.add_field(name="Album", value=activity.album)
                embed.set_footer(text="Song started at {}".format(activity.created_at.strftime("%H:%M")))
                await ctx.send(embed=embed)
                return
    
    await ctx.send(f"{user.name} is not listening to Spotify")
    return
  
#----------------------

#the stephen's musketeer function(WIP)


#the Julian function
@bot.event
async def kids(ctx):
    if "All Might" in ctx.message.content.lower():
        await ctx.send('https://tenor.com/VpGd.gif')
        await bot.process_commands(ctx)



'''


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return # Ignore messages from the bot itself
    
    if "kids" in message.content:
        await message.channel.send('https://cdn.discordapp.com/attachments/1045825009626664990/1077325491423412304/5DBF34E8-A0F9-4A79-92A6-CB19272D16D8.jpg') # Reply with a mention of the user who said kids
        await message.channel.send('https://media.discordapp.net/attachments/954907778521104454/1088086144824135760/Y2Mate.is_-_Doflamingos_Best_Laugh-nqBxdF7chCQ-720p-1656809970696.mp4')
        await bot.process_commands(message)
'''
      
"""Literally just a ping command"""

@bot.command()
async def ping(ctx):
     await ctx.send(f'Pong! In {round(bot.latency * 1000)}ms')

  # Close the bot

@bot.command(aliases=["quit"])
@commands.has_permissions(administrator=True)
async def close(ctx):
    await ctx.send("https://tenor.com/udO9.gif")
    await bot.close()
    print("Bot Closed")  # This is optional, but it is there to tell you.

bot.run(DISCORD_TOKEN)