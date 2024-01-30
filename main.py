import json
import discord
from discord.ext import commands
from discord.ui import Button, View
from itertools import combinations
import random
import dotenv
import os


description = """
An example bot to showcase the discord.ext.commands extension module.
There are a number of utility commands being showcased here.
"""

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    description=description,
    intents=intents,
)

# Load Bot Token from .env file
dotenv.load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    print(f"Guilds:")
    for guild in bot.guilds:
        print(f"- {guild.name} (ID: {guild.id})")
    print("------")
    print(f"Use this link to invite {bot.user}:")
    print(
        f"https://discordapp.com/oauth2/authorize?client_id={bot.user.id}&scope=bot&permissions=8"
    )
    print("------")


def create_embed(title, description, color):
    """Helper function to create and return a Discord embed."""
    embed = discord.Embed(title=title, description=description, color=color)
    return embed


async def send_embed(ctx, title, description, color=discord.Color.blue()):
    """Helper function to send an embed message."""
    embed = create_embed(title, description, color)
    await ctx.send(embed=embed)


@bot.command()
async def rate(ctx: commands.Context, user: discord.Member = None, elo_value: str = None):
    """
    Changes the elo of a player or adds the player with the given elo if he is not yet rated.
    Example:
    `!add @user 5`
    """
    # Check if a user is mentioned
    if user is None:
        await send_embed(ctx, "Rating Error", "You need to mention a user to rate him.", discord.Color.red())
        return

    # Check if elo value is specified and is a digit
    if elo_value is None or not elo_value.isdigit():
        await send_embed(ctx, "Rating Error", "You need to specify the elo as a number.", discord.Color.red())
        return

    # Convert elo_value to an integer
    elo_value = int(elo_value)

    # Check for valid elo range
    if elo_value < 0:
        await send_embed(ctx, "Rating Error", "The elo has to be a positive number.", discord.Color.red())
        return
    if elo_value > 10:
        await send_embed(ctx, "Rating Error", "The elo has to be smaller or equal to 10.", discord.Color.red())
        return
    
    # Rest of the code remains the same
    with open("data/ratings.json", "r") as f:
        elo_ratings = json.load(f)
    
    # check if user is already rated
    rated = False
    for player in elo_ratings:
        if player["id"] == user.id:
            player["elo"] = elo_value
            rated = True
            break

    # if not, add him
    if not rated:
        elo_ratings.append({
            "id": user.id,
            "name": user.name,
            "elo": elo_value
        })
    
    with open("data/ratings.json", "w") as f:
        json.dump(elo_ratings, f, indent=4)

    await send_embed(ctx, "Rating Successful", f"Rated {user.global_name} with {elo_value} elo.", discord.Color.green())


@bot.command()
async def leaderboard(ctx: commands.Context):
    """
    Shows the top 20 players with the highest elo.
    Example:
    `!leaderboard`
    """
    try:
        with open("data/ratings.json", "r") as f:
            elo_ratings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        await ctx.send(f"Error loading ratings: {e}")
        return

    sorted_ratings = sorted(elo_ratings, key=lambda x: (-x['elo'], bot.get_user(x['id']).global_name.lower() if bot.get_user(x['id']) else ""))
    leaderboard = ""
    for i, player in enumerate(sorted_ratings[:20]):
        leaderboard += f"{i+1}. {bot.get_user(player['id']).global_name}: {player['elo']}\n"
    await send_embed(ctx, "Leaderboard", leaderboard)


@bot.command()
async def stats(ctx: commands.Context, user: discord.Member = None):
    """
    Shows the stats of a player.
    Example:
    `!stats @user`
    """
    if user is None:
        await send_embed(ctx, "Stats Error", "You need to mention a user to show his stats.", discord.Color.red())
        return

    try:
        with open("data/ratings.json", "r") as f:
            elo_ratings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        await ctx.send(f"Error loading ratings: {e}")
        return

    for player in elo_ratings:
        if player["id"] == user.id:
            await send_embed(ctx, f"Stats of {user.global_name}", f"Current elo: {player['elo']}")
            return

    await send_embed(ctx, "Stats Error", f"{user.global_name} is not yet rated.", discord.Color.red())


@bot.command()
async def generate_teams(ctx: commands.Context):
    """
    Creates teams with the users in the voice channel the user is in.
    Example:
    `!generate_teams`
    """
    if ctx.author.voice is None:
        await send_embed(ctx, "Team Generation Error", "You are not in a voice channel.", discord.Color.red())
        return
    
    voice_channel = ctx.author.voice.channel
    voice_channel_members = voice_channel.members

    if len(voice_channel_members) < 2:
        await send_embed(ctx, "Team Generation Error", "There are not enough people in the voice channel.", discord.Color.red())
        return
    
    # check if all members are rated
    try:
        with open("data/ratings.json", "r") as f:
            elo_ratings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        await ctx.send(f"Error loading ratings: {e}")
        return
    
    not_rated = []
    for member in voice_channel_members:
        rated = False
        for player in elo_ratings:
            if player["id"] == member.id:
                rated = True
                break
        if not rated:
            not_rated.append(member.global_name)

    if len(not_rated) > 0:
        await send_embed(ctx, "Team Generation Error", f"The following players are not rated: {', '.join(not_rated)}", discord.Color.red())
        return
    
    # Check if the amount of players is even
    if len(voice_channel_members) % 2 != 0:
        await send_embed(ctx, "Team Generation Error", "The amount of players has to be even.", discord.Color.red())
        return
    
    participants = []
    for member in voice_channel_members:
        for player in elo_ratings:
            if player["id"] == member.id:
                participants.append(player)
                break

    # Create all possible teams
    all_teams = list(combinations(participants, len(participants) // 2))

    # Create a list of all possible team combinations
    all_team_combinations = list(combinations(all_teams, 2))

    # Remove all team combinations where a player is in both teams
    valid_team_combinations = []
    for team_combination in all_team_combinations:
        team1, team2 = team_combination
        if not any(player in team2 for player in team1):
            valid_team_combinations.append(team_combination)

    # Calculate the difference in elo for each team combination
    team_combination_differences = []
    for team_combination in valid_team_combinations:
        team1, team2 = team_combination
        team1_elo = sum(player["elo"] for player in team1)
        team2_elo = sum(player["elo"] for player in team2)
        team_combination_differences.append(abs(team1_elo - team2_elo))

    # Sort the team combinations by elo difference
    sorted_team_combinations = sorted(zip(valid_team_combinations, team_combination_differences), key=lambda x: x[1])

    # If the best team combination difference is for example 1
    # find all team combinations with a difference of 1
    # and choose one of them randomly
    best_team_combination_difference = sorted_team_combinations[0][1]
    best_team_combinations = []
    for team_combination in sorted_team_combinations:
        if team_combination[1] == best_team_combination_difference:
            best_team_combinations.append(team_combination[0])
        else:
            break

    # Choose a random team combination
    chosen_team_combination = random.choice(best_team_combinations)
    team1, team2 = chosen_team_combination
    team1_elo = sum(player["elo"] for player in team1)
    team2_elo = sum(player["elo"] for player in team2)

    # Create a dictionary with the global names of the players and their elo
    team1_players = []
    for player in team1:
        team1_players.append(f"{bot.get_user(player['id']).global_name}: {player['elo']}")
    team2_players = []
    for player in team2:
        team2_players.append(f"{bot.get_user(player['id']).global_name}: {player['elo']}")


    # Create the team embed
    team_embed = discord.Embed(title="Team Generation", color=discord.Color.blue())
    team_embed.add_field(name=f"Team 1 ({team1_elo})", value="\n".join(team1_players), inline=True)
    team_embed.add_field(name=f"Team 2 ({team2_elo})", value="\n".join(team2_players), inline=True)
    team_embed.set_footer(text=f"Found {len(sorted_team_combinations)} possible team combinations of which {len(best_team_combinations)} have the optimal elo distribution.")

    await ctx.send(embed=team_embed)


@bot.command()
async def command_list(ctx: commands.Context):
    """
    Shows the help message.
    Example:
    `!command_list`
    """
    help_message = """
    **!rate @user elo**
    Rates a player with the given elo. If the player is already rated, his elo will be updated.
    Example:
    `!rate @user 5`

    **!leaderboard**
    Shows the top 20 players with the highest elo.
    Example:
    `!leaderboard`

    **!stats @user**
    Shows the stats of a player.
    Example:
    `!stats @user`
    
    **!generate_teams**
    Creates balanced teams with the users in the voice channel the user is in.
    Example:
    `!generate_teams`
    """
    await send_embed(ctx, "Help", help_message)


bot.run(BOT_TOKEN)
