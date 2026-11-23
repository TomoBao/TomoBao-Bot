import logging
import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID') or '0')
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID') or '0')
if not TOKEN:
    raise RuntimeError('Set DISCORD_TOKEN in .env')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger('tomobao')

class TomoBaoBot(commands.Bot):
    async def setup_hook(self):
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            if os.getenv('SYNC_ON_STARTUP', 'false').lower() == 'true':
                synced = await self.tree.sync(guild=guild)
                logger.info('Synced %d commands to test guild', len(synced))
        elif os.getenv('SYNC_ON_STARTUP', 'false').lower() == 'true':
            synced = await self.tree.sync()
            logger.info('Synced %d global commands', len(synced))

intents = discord.Intents.default()
intents.members = True
bot = TomoBaoBot(command_prefix='!', intents=intents, allowed_mentions=discord.AllowedMentions.none())

@bot.event
async def on_ready():
    logger.info('Logged in as %s', bot.user)

@bot.event
async def on_member_join(member: discord.Member):
    if GUILD_ID and member.guild.id != GUILD_ID:
        return
    channel = (member.guild.get_channel(WELCOME_CHANNEL_ID) if WELCOME_CHANNEL_ID
               else discord.utils.get(member.guild.text_channels, name='👋・welcome'))
    if not isinstance(channel, discord.TextChannel):
        logger.warning('Welcome channel not found; set WELCOME_CHANNEL_ID')
        return
    embed = discord.Embed(
        title='👋 Welcome!',
        description=(f'Welcome to **{discord.utils.escape_markdown(member.guild.name)}**, '
                     f'{member.mention}!\n\n📜 Please read the server rules.\n💬 Enjoy your stay!'),
        color=discord.Color.blurple(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    if member.guild.member_count is not None:
        embed.set_footer(text=f'Member #{member.guild.member_count}')
    try:
        await channel.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
        )
    except discord.HTTPException:
        logger.exception('Failed to send welcome message to channel %s', channel.id)


@bot.tree.command(name='ping', description='Check the bot latency')
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'Pong! {round(bot.latency * 1000)} ms', ephemeral=True)

@bot.tree.command(name='help', description='Show available commands')
async def help_command(interaction: discord.Interaction):
    await interaction.response.send_message('**TomoBao Bot**\n/ping, /help, /userinfo, /serverinfo, /avatar, /botinfo, /clear (moderators)', ephemeral=True)

@bot.tree.command(name='userinfo', description='Show member information')
@app_commands.guild_only()
async def userinfo(interaction: discord.Interaction, member: discord.Member | None = None):
    member = member or interaction.user
    embed = discord.Embed(title='User Information', color=0x5865F2)
    embed.add_field(name='Username', value=discord.utils.escape_markdown(str(member)), inline=False)
    embed.add_field(name='ID', value=str(member.id))
    embed.add_field(name='Account created', value=discord.utils.format_dt(member.created_at, 'D'))
    if member.joined_at:
        embed.add_field(name='Joined server', value=discord.utils.format_dt(member.joined_at, 'D'))
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='serverinfo', description='Show server information')
@app_commands.guild_only()
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=guild.name, color=0x5865F2)
    embed.add_field(name='Members', value=str(guild.member_count or 'Unknown'))
    embed.add_field(name='Channels', value=str(len(guild.channels)))
    embed.add_field(name='Roles', value=str(len(guild.roles)))
    embed.add_field(name='Server ID', value=str(guild.id), inline=False)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='avatar', description='Show a member avatar')
@app_commands.guild_only()
async def avatar(interaction: discord.Interaction, member: discord.Member | None = None):
    member = member or interaction.user
    embed = discord.Embed(title=f'{member.display_name} — Avatar', color=0x5865F2)
    embed.set_image(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='botinfo', description='Show TomoBao Bot information')
async def botinfo(interaction: discord.Interaction):
    await interaction.response.send_message(f'**TomoBao Bot** — Multipurpose Discord bot\nPowered by discord.py {discord.__version__}', ephemeral=True)

@bot.tree.command(name='clear', description='Delete up to 50 recent messages (moderators only)')
@app_commands.guild_only()
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(amount='Number of messages (1–50)')
async def clear(interaction: discord.Interaction, amount: app_commands.Range[int, 1, 50]):
    if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message('Manage Messages permission required.', ephemeral=True)
    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel):
        return await interaction.response.send_message('Use this in a text channel.', ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    try:
        deleted = await channel.purge(limit=amount, reason=f'Moderation by {interaction.user} ({interaction.user.id})')
    except discord.Forbidden:
        return await interaction.followup.send('Bot needs Manage Messages and Read Message History.', ephemeral=True)
    except discord.HTTPException:
        logger.exception('Message deletion failed')
        return await interaction.followup.send('Unable to delete messages. See server logs.', ephemeral=True)
    await interaction.followup.send(f'Deleted {len(deleted)} messages.', ephemeral=True)

@bot.tree.error
async def on_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    logger.error('Slash command error: %s', error)
    if not interaction.response.is_done():
        try:
            await interaction.response.send_message('Command failed. Check bot logs.', ephemeral=True)
        except discord.HTTPException:
            logger.warning('Could not send error response (possible rate limit)')

bot.run(TOKEN, log_handler=None)
