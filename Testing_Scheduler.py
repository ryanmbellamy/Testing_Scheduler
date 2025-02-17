import os
import discord
from discord.ext import commands
from discord import ui
from dotenv import load_dotenv
from datetime import datetime
import pytz  # For handling time zones

# Load environment variables
load_dotenv()
TOKEN = 'MTM0MDg3NTU5MDk1MzIwNTg1MQ'+'.GF5A8W.WK0FtcgRErMlHLt'+'9hSGaJkMzJGK04yeuqE-isc'  # Restore token

intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent
bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary to store active test requests (Message ID -> User data)
test_requests = {}

class JoinTestButton(ui.Button):
    """A button to join a test request."""
    def __init__(self, host_id, host_mention, play_with, play_against, message_id):
        super().__init__(label="Join Match", style=discord.ButtonStyle.green)
        self.host_id = host_id
        self.host_mention = host_mention  # Store host mention
        self.play_with = play_with
        self.play_against = play_against
        self.message_id = message_id

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user

        # Prevent host from joining their own challenge
        if user.id == self.host_id:
            await interaction.response.send_message("You can't join your own test request!", ephemeral=True)
            return

        # Get the challenge message and update it
        message = interaction.message
        await message.edit(content=f"✅ {user.mention} has joined {self.host_mention}'s 1v1 test match!\n"
                                   f"**Testing:** {self.play_with} vs {self.play_against}",
                           view=None)  # Remove buttons

        # Acknowledge the interaction
        await interaction.response.send_message(f"You have joined {self.host_mention}'s match!", ephemeral=True)

        # Remove the request from tracking
        test_requests.pop(self.message_id, None)


class CancelMatchButton(ui.Button):
    """A button to cancel a test request."""
    def __init__(self, host_id, message_id):
        super().__init__(label="Cancel Match", style=discord.ButtonStyle.red)
        self.host_id = host_id
        self.message_id = message_id

    async def callback(self, interaction: discord.Interaction):
        # Only the host can cancel the match
        if interaction.user.id != self.host_id:
            await interaction.response.send_message("Only the host can cancel the match.", ephemeral=True)
            return

        # Get the challenge message and update it
        message = interaction.message
        await message.edit(content="Test Cancelled :(", view=None)  # Change text and remove buttons

        # Acknowledge the cancellation
        await interaction.response.send_message(f"{interaction.user.mention}, your test request has been cancelled.", ephemeral=True)

        # Remove the request from tracking
        test_requests.pop(self.message_id, None)

# Event: Bot successfully starts
@bot.event
async def on_ready():
    print(f'{bot.user} is now online and ready!')

# Command: Start a test request with a join button and a cancel match button
@bot.command(name="test")
async def start_test(ctx, play_with: str, play_against: str, date: str, time: str, timezone: str):
    """Creates a 1v1 test request with interactive buttons (join and cancel)."""
    user_id = ctx.author.id
    user_mention = ctx.author.mention  # Store the user's mention

    # Get the current year
    current_year = datetime.now().year

    # Combine the current year with the provided date (MM-DD)
    try:
        # Assuming current year for date input and parse it into a datetime object
        datetime_input = f"{current_year}-{date} {time}"
        suggested_datetime = datetime.strptime(datetime_input, "%Y-%m-%d %H:%M")

        # Get the time zone and check if it's valid
        try:
            tz = pytz.timezone(timezone.upper())
        except pytz.UnknownTimeZoneError:
            await ctx.send(f"Unknown timezone: `{timezone}`. Please use a valid time zone.")
            return

        # Convert to the provided time zone
        localized_time = tz.localize(suggested_datetime)
        formatted_datetime = localized_time.strftime("%B %d at %I:%M %p %Z")  # Format with time zone

    except ValueError:
        # If the date/time format is incorrect, send an error
        await ctx.send("Invalid date or time format. Please use the format `MM-DD` for date and `HH:MM` for time.")
        return

    # Create a new embed message with the suggested date/time
    embed = discord.Embed(title="1v1 Test Request",
                          description=f"{ctx.author.mention} wants to test **{play_with}** against **{play_against}**.\n"
                                      f"**Suggested Time:** {formatted_datetime}",
                          color=discord.Color.blue())

    # Create the buttons (Join and Cancel)
    join_button = JoinTestButton(user_id, user_mention, play_with, play_against, ctx.message.id)
    cancel_button = CancelMatchButton(user_id, ctx.message.id)

    # Create a view and add both buttons
    view = discord.ui.View()
    view.add_item(join_button)
    view.add_item(cancel_button)

    # Send the message with the embed and both buttons
    message = await ctx.send(embed=embed, view=view)

    # Store the message ID for tracking
    test_requests[message.id] = {"host_id": user_id, "host_mention": user_mention, "play_with": play_with, 
                                 "play_against": play_against, "date_time": formatted_datetime}

# Command: Show active test requests
@bot.command(name="tests")
async def list_tests(ctx):
    """Displays all active test requests."""
    if not test_requests:
        await ctx.send("No active test requests.")
        return

    response = "**Active 1v1 Test Requests:**\n"
    for message_id, data in test_requests.items():
        member = ctx.guild.get_member(data['host_id'])  # Get member from the guild
        response += f"{member.name} wants to test **{data['play_with']}** against **{data['play_against']}**\n"
        response += f"Suggested Time: {data['date_time']}\n"  # Display the suggested date and time

    await ctx.send(response)

# Command: Cancel a test request
@bot.command(name="canceltest")
async def cancel_test(ctx):
    """Allows a user to cancel their own test request."""
    for message_id, data in list(test_requests.items()):
        if data["host_id"] == ctx.author.id:
            test_requests.pop(message_id)
            await ctx.send(f"{ctx.author.mention} has canceled their test request.")
            return

    await ctx.send(f"{ctx.author.mention}, you don't have an active test request.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("hi"):
        await message.channel.send("Hello!")

    # This line is crucial to allow commands to work
    await bot.process_commands(message)

# Run the bot
bot.run(TOKEN)
