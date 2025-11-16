import discord
from discord.ext import commands
import discord.ui
# --- SECURE CONFIGURATION ---
import os 
from keep_alive import keep_alive 

# ⚠️ 1. Get the token securely from the Railway Environment Variables/Secrets
try:
    BOT_TOKEN = os.environ['BOT_TOKEN']
except KeyError:
    print("FATAL ERROR: The BOT_TOKEN environment variable is not set in Railway's Variables tab.")
    exit(1)

# --- GLOBAL VARIABLES ---
# ⚠️ IDs confirmed by user
GUILD_ID = 1432940470102659194     
SUPPORT_CATEGORY_ID = 1439321682803167242 
SUPPORT_ROLE_ID = 1434347506778505319     

# Store active threads: {user_id: thread_channel_id}
active_tickets = {} 

# 🌟 DEFINITIVE FIX: Set to track IDs to prevent the bot from responding multiple times
last_processed_dm_ids = set() 

# --- INTENTS ---
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ----------------------------------------------------------------------
# --- BOT EVENTS & COMMANDS ---
# ----------------------------------------------------------------------

@bot.event
async def on_ready():
    """Confirms the bot is logged in and sets its status."""
    print(f'Bot is logged in as {bot.user}')

    activity = discord.Activity(
        name="for DMs | Support Online.", 
        type=discord.ActivityType.watching
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.command()
@commands.has_role(SUPPORT_ROLE_ID) # 🔑 RESTRICTS command usage to ONLY the SUPPORT_ROLE_ID
async def close(ctx):
    """Closes the current support ticket (channel)."""
    
    if ctx.channel.id not in active_tickets.values():
        try:
            return await ctx.send("This is not an active support ticket channel.")
        except Exception:
            return
    
    user_id = next((k for k, v in active_tickets.items() if v == ctx.channel.id), None)
    
    if user_id:
        user = bot.get_user(user_id)
        if user:
            try:
                await user.send("✅ Your support thread has been closed by the staff team. Thank you for contacting support!")
            except discord.HTTPException:
                print(f"Could not DM user {user.id} to confirm ticket closure.")
        
        await ctx.send("Deleting channel and closing ticket...")
        
        del active_tickets[user_id]
        await ctx.channel.delete()
    else:
        await ctx.send("Error: Could not find the associated user for this ticket.")

@close.error
async def close_error(ctx, error):
    """Handles the error when a user without the support role tries to use !close."""
    if isinstance(error, commands.MissingRole):
        await ctx.send("🛑 You do not have the required role to close a ticket.")
    elif isinstance(error, commands.NoPrivateMessage):
        pass # Command cannot be used in DMs anyway
    else:
        # For general errors during command execution
        print(f"Error in !close command: {error}")


# ----------------------------------------------------------------------
# --- MESSAGE HANDLING (Includes crash safety for forwarding) ---
# ----------------------------------------------------------------------

@bot.event
async def on_message(message):
    
    if message.author == bot.user:
        return

    # 🌟 FIX: Check for duplicate message ID to stop the multiple welcome messages
    if message.id in last_processed_dm_ids:
        return 
    
    last_processed_dm_ids.add(message.id)

    # === SECTION 1: DM from User to Bot (Forward to Staff) ===
    if isinstance(message.channel, discord.DMChannel):
        user = message.author
        
        if user.id in active_tickets: 
            # Ticket is active: Forward DM to the server channel
            try:
                channel_id = active_tickets[user.id]
                support_channel = bot.get_channel(channel_id)
                
                if support_channel:
                    # --- Attachment Forwarding: User to Staff ---
                    attachment_info = ""
                    if message.attachments:
                        attachments = [f"[{i+1}. {a.filename}]({a.url})" for i, a in enumerate(message.attachments)]
                        attachment_info = "\n\n**Attachments (Clickable Links):**\n" + "\n".join(attachments)

                    embed = discord.Embed(
                        title=f"📩 New Message from {user.name} (DM)",
                        description=message.content + attachment_info, 
                        color=discord.Color.blue()
                    )
                    embed.set_footer(text="To reply, type your message in this channel.")
                    
                    if message.attachments and message.attachments[0].content_type.startswith('image'):
                        embed.set_image(url=message.attachments[0].url)

                    await support_channel.send(embed=embed)
                    await message.channel.send("Your message has been forwarded to the support team.")
            except KeyError:
                # CRASH SAFETY: This handles if active_tickets somehow contains a bad key/value
                print(f"Error: active_tickets dictionary missing key for user {user.id}")
                await message.channel.send("An internal error occurred while forwarding your message. Please try again or create a new ticket.")
            except Exception as e:
                # Catch any other forwarding errors without crashing the process
                print(f"Unexpected error during DM forwarding: {e}")
                
        else:
            # No active ticket: Send auto-response with button
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Open Support Thread", custom_id="open_ticket", style=discord.ButtonStyle.green))
            
            await message.channel.send(
                "👋 Hello! Thanks for reaching out. Are you sure you want to contact staff? Click the button below to confirm and open a support thread.",
                view=view
            )
            return

    # === SECTION 2: Message in Staff Channel (Forward to User DM) ===
    elif message.guild and message.guild.id == GUILD_ID and message.channel.id in active_tickets.values():
        
        # Safely find the user ID
        user_id = next((k for k, v in active_tickets.items() if v == message.channel.id), None)
        
        if user_id:
            user = bot.get_user(user_id)
            if user:
                # --- Attachment Forwarding: Staff to User ---
                attachment_info = ""
                if message.attachments:
                    attachments = [f"[{i+1}. {a.filename}]({a.url})" for i, a in enumerate(message.attachments)]
                    attachment_info = "\n\n**Attachments:**\n" + "\n".join(attachments)

                reply_embed = discord.Embed(
                    title=f"👤 Support Agent Reply",
                    description=message.content + attachment_info,
                    color=discord.Color.red()
                )
                reply_embed.set_footer(text=f"Sent by {message.author.display_name}")
                
                if message.attachments and message.attachments[0].content_type.startswith('image'):
                    reply_embed.set_image(url=message.attachments[0].url)
                
                try:
                    await user.send(embed=reply_embed)
                except discord.HTTPException:
                    # CRASH SAFETY: Fails gracefully if user DMs are closed
                    print(f"Could not send DM to user {user.id}. DMs likely closed.")
                    
    await bot.process_commands(message)

# ----------------------------------------------------------------------
# --- INTERACTIONS (Crash prevention confirmed) ---
# ----------------------------------------------------------------------

@bot.event
async def on_interaction(interaction):
    """Handles button clicks for creating a ticket."""
    
    if interaction.type == discord.InteractionType.component and interaction.data.get('custom_id') == "open_ticket":
        user = interaction.user
        guild = bot.get_guild(GUILD_ID)
        category = discord.utils.get(guild.categories, id=SUPPORT_CATEGORY_ID)
        
        if not guild or not category:
            return await interaction.response.send_message("❌ Configuration Error: Guild or Category not found. Please contact a server admin.", ephemeral=True)
            
        # 1. Check for active ticket, and use try/except to prevent crash on duplicate event
        if user.id in active_tickets:
            try:
                # This handles the case where the interaction event is received a second time
                return await interaction.response.send_message("🛑 You already have an active support thread!", ephemeral=True)
            except discord.HTTPException:
                # Safely ignore if the interaction was already acknowledged by a successful parallel event
                return
            
        channel_name = f"ticket-{user.name.lower().replace(' ', '-')}"
        
        # Create the support channel
        new_channel = await guild.create_text_channel(
            channel_name, 
            category=category,
            topic=f"Support ticket for user ID: {user.id}"
        )
        
        # Add the new ticket to the dictionary (Bot memory)
        active_tickets[user.id] = new_channel.id 
        
        # 2. 🌟 CRITICAL CRASH PREVENTION FIX: Handle the 'Interaction has already been acknowledged' error (40060)
        try:
            # Acknowledges the interaction and sends confirmation message
            await interaction.response.edit_message(
                content=f"✅ **Thread Created!** The staff team will get back to you soon. All your future DMs will be sent to the staff. See {new_channel.mention}",
                view=None
            )
        except discord.errors.HTTPException as e:
            # This handles the repeated event that would otherwise crash the bot
            if e.code == 40060: 
                pass 
            else:
                raise # Re-raise other errors
        
        staff_embed = discord.Embed(
            title="🎫 NEW SUPPORT TICKET",
            description=f"**User:** {user.mention} ({user.id})",
            color=discord.Color.green()
        )
        
        support_role = f"<@&{SUPPORT_ROLE_ID}>" 
        await new_channel.send(f"Hey {support_role}, a new ticket has been opened by {user.mention}!", embed=staff_embed)


# --- Run the Bot ---
keep_alive() 
bot.run(BOT_TOKEN)
