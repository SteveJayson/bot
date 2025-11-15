import discord
from discord.ext import commands
import discord.ui
# 🌟 NEW: Import the os module to read the token securely
import os

# --- CONFIGURATION (You MUST change these) ---
# ⚠️ 1. Get the token securely from the Replit environment/Secrets
#    You MUST add a Secret Key named 'BOT_TOKEN' with your actual token as the value.
BOT_TOKEN = os.environ['BOT_TOKEN']

# ⚠️ 2. ID of your main Discord server where support channels will be created
GUILD_ID = 1432940470102659194

# ⚠️ 3. ID of the Category where the new support channels (tickets) will be placed
SUPPORT_CATEGORY_ID = 1439321682803167242

# ⚠️ 4. ID of the role to mention when a new ticket is opened
SUPPORT_ROLE_ID = 1434347506778505319

# Store active threads: {user_id: thread_channel_id}
active_tickets = {}

# --- INTENTS ---
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


# ----------------------------------------------------------------------
# --- EVENTS ---
# ----------------------------------------------------------------------

@bot.event
async def on_ready():
    """Confirms the bot is logged in and sets its status."""
    print(f'Bot is logged in as {bot.user}')

    # Set the bot's status and description (Activity)
    activity = discord.Activity(
        name="for DMs | Support Online",
        type=discord.ActivityType.watching
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)


# ----------------------------------------------------------------------
# --- COMMANDS ---
# ----------------------------------------------------------------------

@bot.command()
@commands.has_permissions(manage_channels=True)
async def close(ctx):
    """Closes the current support ticket (channel)."""

    if ctx.channel.id not in active_tickets.values():
        return await ctx.send("This is not an active support ticket channel.")

    user_id = next((k for k, v in active_tickets.items() if v == ctx.channel.id), None)

    if user_id:
        user = bot.get_user(user_id)
        if user:
            await user.send(
                "✅ Your support thread has been closed by the staff team. Thank you for contacting support!")

        await ctx.send("Deleting channel and closing ticket...")

        del active_tickets[user_id]
        await ctx.channel.delete()
    else:
        await ctx.send("Error: Could not find the associated user for this ticket.")


# ----------------------------------------------------------------------
# --- MESSAGE HANDLING ---
# ----------------------------------------------------------------------

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # === SECTION 1: DM from User to Bot (Forward to Staff) ===
    if isinstance(message.channel, discord.DMChannel):
        user = message.author

        if user.id in active_tickets:
            # Ticket is active: Forward DM to the server channel
            channel_id = active_tickets[user.id]
            support_channel = bot.get_channel(channel_id)

            if support_channel:
                # --- Attachment Forwarding: User to Staff ---
                attachment_info = ""
                if message.attachments:
                    attachments = [f"[{i + 1}. {a.filename}]({a.url})" for i, a in enumerate(message.attachments)]
                    attachment_info = "\n\n**Attachments (Clickable Links):**\n" + "\n".join(attachments)

                embed = discord.Embed(
                    title=f"📩 New Message from {user.name} (DM)",
                    description=message.content + attachment_info,
                    color=discord.Color.blue()
                )
                embed.set_footer(text="To reply, type your message in this channel.")

                # Embed the first image for direct viewing by staff
                if message.attachments and message.attachments[0].content_type.startswith('image'):
                    embed.set_image(url=message.attachments[0].url)
                # ----------------------------------------------

                await support_channel.send(embed=embed)
                await message.channel.send("Your message has been forwarded to the support team.")

        else:
            # No active ticket: Send auto-response with button
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Open Support Thread", custom_id="open_ticket",
                                            style=discord.ButtonStyle.green))

            await message.channel.send(
                "👋 Hello! Thanks for reaching out. Are you sure you want to contact staff? Click the button below to confirm and open a support thread.",
                view=view
            )

    # === SECTION 2: Message in Staff Channel (Forward to User DM) ===
    elif message.guild and message.guild.id == GUILD_ID and message.channel.id in active_tickets.values():

        user_id = next((k for k, v in active_tickets.items() if v == message.channel.id), None)

        if user_id:
            user = bot.get_user(user_id)
            if user:
                # --- Attachment Forwarding: Staff to User ---
                attachment_info = ""
                if message.attachments:
                    attachments = [f"[{i + 1}. {a.filename}]({a.url})" for i, a in enumerate(message.attachments)]
                    attachment_info = "\n\n**Attachments:**\n" + "\n".join(attachments)

                reply_embed = discord.Embed(
                    title=f"👤 Support Agent Reply",
                    description=message.content + attachment_info,
                    color=discord.Color.red()
                )
                reply_embed.set_footer(text=f"Sent by {message.author.display_name}")

                # Embed the first image for direct viewing by the user
                if message.attachments and message.attachments[0].content_type.startswith('image'):
                    reply_embed.set_image(url=message.attachments[0].url)
                # -----------------------------------------------------------

                await user.send(embed=reply_embed)

    await bot.process_commands(message)


# ----------------------------------------------------------------------
# --- INTERACTIONS ---
# ----------------------------------------------------------------------

@bot.event
async def on_interaction(interaction):
    """Handles button clicks for creating a ticket."""

    if interaction.type == discord.InteractionType.component and interaction.data.get('custom_id') == "open_ticket":
        user = interaction.user
        guild = bot.get_guild(GUILD_ID)
        category = discord.utils.get(guild.categories, id=SUPPORT_CATEGORY_ID)

        if not guild or not category:
            return await interaction.response.send_message(
                "❌ Configuration Error: Guild or Category not found. Please contact a server admin.", ephemeral=True)

        channel_name = f"ticket-{user.name.lower().replace(' ', '-')}"

        new_channel = await guild.create_text_channel(
            channel_name,
            category=category,
            topic=f"Support ticket for user ID: {user.id}"
        )

        active_tickets[user.id] = new_channel.id

        await interaction.response.edit_message(
            content=f"✅ **Thread Created!** The staff team will get back to you soon. All your future DMs will be sent to the staff.",
            view=None
        )

        staff_embed = discord.Embed(
            title="🎫 NEW SUPPORT TICKET",
            description=f"**User:** {user.mention} ({user.id})\n**Initial Message:** {interaction.message.content}",
            color=discord.Color.green()
        )

        support_role = f"<@&{SUPPORT_ROLE_ID}>"
        await new_channel.send(f"Hey {support_role}, a new ticket has been opened by {user.mention}!",
                               embed=staff_embed)


# --- Run the Bot ---
# 🌟 CHANGE: Use the secure environment variable read at the top
bot.run(BOT_TOKEN)
