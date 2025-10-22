# Loey the Coal Miner v7 — Levels, Games, Moderation, Fun & Custom Welcome with Leaderboard
import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import os
import aiohttp
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from keep_alive import keep_alive

keep_alive()

# ------------------ Setup ------------------
load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

# ------------------ Data ------------------
if os.path.exists("xp.json"):
    with open("xp.json", "r") as f:
        xp_data = json.load(f)
else:
    xp_data = {}

if os.path.exists("warns.json"):
    with open("warns.json", "r") as f:
        warns = json.load(f)
else:
    warns = {}

if os.path.exists("welcome.json"):
    with open("welcome.json", "r") as f:
        welcome_messages = json.load(f)
else:
    welcome_messages = {}

level_titles = [
    "Amateur 🥉", "Novice", "Apprentice", "Adept", "Skilled", "Specialist",
    "Expert", "Virtuoso", "Master", "Grandmaster 🏆"
]

bad_words = [
    "fuck", "shit", "bitch", "nigga", "retard", "asshole", "dumbfuck",
    "bastard"
]


def get_level(xp):
    lvl = xp // 100
    if lvl >= len(level_titles):
        lvl = len(level_titles) - 1
    return lvl, level_titles[lvl]


# ------------------ Events ------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ {bot.user} is online and ready!")
    await bot.change_presence(activity=discord.Game("⛏️ Mining coal for fun!"))


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # XP gain
    user_id = str(message.author.id)
    xp_data[user_id] = xp_data.get(user_id, 0) + random.randint(5, 15)
    with open("xp.json", "w") as f:
        json.dump(xp_data, f)

    # Auto-moderation
    msg_content = message.content.lower()
    if any(bad in msg_content for bad in bad_words):
        warns[user_id] = warns.get(user_id, 0) + 1
        with open("warns.json", "w") as f:
            json.dump(warns, f)
        await message.delete()
        await message.channel.send(
            f"⚠️ {message.author.mention}, watch your language! Warning #{warns[user_id]}"
        )
        return

    await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    user_id = str(member.id)
    msg = welcome_messages.get(user_id,
                               f"Welcome {member.mention} to the server! 🎉")
    try:
        await member.send(msg)
    except:
        pass


# ------------------ Level Commands ------------------
@bot.tree.command(name="level",
                  description="Check your or another member's level.")
async def level(interaction: discord.Interaction,
                member: discord.Member = None):
    member = member or interaction.user
    user_id = str(member.id)
    xp = xp_data.get(user_id, 0)
    lvl, title = get_level(xp)
    await interaction.response.send_message(
        f"{member.mention} is Level {lvl} — {title} ({xp} XP)")


@bot.tree.command(name="leaderboard", description="View the top 10 miners.")
async def leaderboard(interaction: discord.Interaction):
    if not xp_data:
        await interaction.response.send_message("No XP data yet.")
        return
    sorted_xp = sorted(xp_data.items(), key=lambda x: x[1], reverse=True)[:10]
    embed = discord.Embed(title="🏆 Miner Leaderboard",
                          color=discord.Color.gold())
    for i, (user_id, xp) in enumerate(sorted_xp, start=1):
        user = interaction.guild.get_member(int(user_id))
        if user:
            lvl, title = get_level(xp)
            embed.add_field(name=f"{i}. {user.display_name}",
                            value=f"Level {lvl} — {title} ({xp} XP)",
                            inline=False)
    await interaction.response.send_message(embed=embed)


# ------------------ Moderation Commands ------------------
@bot.tree.command(name="kick", description="Kick a member.")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction,
               member: discord.Member,
               reason: str = "No reason provided"):
    await member.kick(reason=reason)
    await interaction.response.send_message(
        f"👢 {member} was kicked. Reason: {reason}")


@bot.tree.command(name="ban", description="Ban a member.")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction,
              member: discord.Member,
              reason: str = "No reason provided"):
    await member.ban(reason=reason)
    await interaction.response.send_message(
        f"🔨 {member} was banned. Reason: {reason}")


    @bot.tree.command(name="mute", description="Mute (timeout) a member for a certain duration in minutes.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(interaction: discord.Interaction,
                   member: discord.Member,
                   duration: int,  # duration in minutes
                   reason: str = "No reason provided"):
        try:
            await member.timeout(duration=discord.utils.timedelta(minutes=duration), reason=reason)
            await interaction.response.send_message(
                f"🤐 {member} has been muted for {duration} minutes. Reason: {reason}")
        except Exception as e:
            await interaction.response.send_message(
                f"⚠ Could not mute {member}. Error: {e}")


@bot.tree.command(name="timeout",
                  description="Timeout a member for X minutes.")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member,
                  minutes: int):
    await member.timeout(datetime.utcnow() + timedelta(minutes=minutes))
    await interaction.response.send_message(
        f"⏳ {member} timed out for {minutes} minutes.")


@bot.tree.command(name="warns",
                  description="Check how many warnings a member has.")
async def check_warns(interaction: discord.Interaction,
                      member: discord.Member):
    user_id = str(member.id)
    count = warns.get(user_id, 0)
    await interaction.response.send_message(
        f"⚠️ {member.mention} has {count} warning(s).")


# ------------------ Fun Commands ------------------
@bot.tree.command(name="joke", description="Tell a miner joke.")
async def joke(interaction: discord.Interaction):
    jokes = [
        "Why did the miner get promoted? Because he was outstanding in his field! 😄",
        "Coal miners do it under pressure! 😂",
        "I would tell you a coal joke… but it might be too dirty! 😆"
    ]
    await interaction.response.send_message(random.choice(jokes))


@bot.tree.command(name="meme", description="Send a random meme.")
async def meme(interaction: discord.Interaction):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://meme-api.com/gimme") as resp:
                data = await resp.json()
                await interaction.response.send_message(data["url"])
                return
    except:
        pass
    await interaction.response.send_message(
        random.choice([
            "https://i.imgflip.com/7yz7fz.jpg",
            "https://i.imgflip.com/7yz7gg.jpg"
        ]))


@bot.tree.command(name="rickroll", description="Rickroll a member via DM.")
async def rickroll(interaction: discord.Interaction, member: discord.Member):
    try:
        await member.send(
            "🎵 Never gonna give you up! https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        await interaction.response.send_message(
            f"✅ {member.mention} has been Rickrolled via DM!")
    except:
        await interaction.response.send_message("❌ Could not DM that user.")


@bot.tree.command(name="setwelcome",
                  description="Set a custom welcome message via DM.")
async def setwelcome(interaction: discord.Interaction, *, message: str):
    user_id = str(interaction.user.id)
    welcome_messages[user_id] = message
    with open("welcome.json", "w") as f:
        json.dump(welcome_messages, f)
    await interaction.response.send_message(
        "✅ Your custom welcome message has been saved!")


# ------------------ Games ------------------
@bot.tree.command(name="coin", description="Flip a coin.")
async def coin(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🪙 Result: **{random.choice(['Heads', 'Tails'])}**")


@bot.tree.command(name="rps", description="Play Rock-Paper-Scissors.")
async def rps(interaction: discord.Interaction, choice: str):
    choice = choice.lower()
    options = ["rock", "paper", "scissors"]
    if choice not in options:
        await interaction.response.send_message(
            "❌ Choose rock, paper, or scissors!")
        return
    bot_choice = random.choice(options)
    result = ("It's a tie!" if choice == bot_choice else "You win! 🎉" if (
        (choice == "rock" and bot_choice == "scissors") or
        (choice == "paper" and bot_choice == "rock") or
        (choice == "scissors" and bot_choice == "paper")) else "You lose! 😢")
    await interaction.response.send_message(
        f"You: **{choice}**, Bot: **{bot_choice}** — {result}")


@bot.tree.command(name="hangman", description="Play Hangman.")
async def hangman(interaction: discord.Interaction):
    words = ["miner", "diamond", "torch", "coal", "pickaxe", "helmet"]
    word = random.choice(words)
    guessed = ["_"] * len(word)
    lives = 6
    guessed_letters = []

    await interaction.response.send_message(
        f"🎮 Hangman started!\nWord: {' '.join(guessed)}\nLives: {lives}")

    def check(msg):
        return msg.author == interaction.user and msg.channel == interaction.channel

    while lives > 0 and "_" in guessed:
        try:
            msg = await bot.wait_for("message", check=check, timeout=45)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Time's up! Game ended.")
            return

        guess = msg.content.lower()
        if len(guess) != 1 or not guess.isalpha():
            await msg.channel.send("Enter one valid letter!")
            continue
        if guess in guessed_letters:
            await msg.channel.send("Already guessed that one!")
            continue

        guessed_letters.append(guess)
        if guess in word:
            for i, letter in enumerate(word):
                if letter == guess:
                    guessed[i] = guess
        else:
            lives -= 1

        await msg.channel.send(f"Word: {' '.join(guessed)} | ❤️ Lives: {lives}"
                               )

    if "_" not in guessed:
        await interaction.followup.send(f"🎉 You won! The word was **{word}**.")
    else:
        await interaction.followup.send(f"💀 You lost! The word was **{word}**."
                                        )


# ------------------ Run ------------------
bot.run(TOKEN)
