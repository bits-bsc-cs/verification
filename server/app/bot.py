import discord
from discord.ext import commands
import logging
from logging.handlers import RotatingFileHandler
from aiohttp import web
import urllib.request
import json
import asyncio
import signal

try:
    from .utils import printStat
except ImportError:
    from utils import printStat

try:
    from .cfg import settings
except ImportError:
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.cfg import settings

TOKEN = settings.discord_token
ROLE_NAME = settings.discord_role_name
IPC_SECRET = settings.ipc_secret
IPC_PORT = 5001  # Port for communication between main.py and bot.py

handler = RotatingFileHandler(
    filename="discord.log",
    maxBytes=10 * 1024 * 1024,  # 5 max page files of 10MB
    backupCount=5,
    encoding="utf-8",
)
logger = logging.getLogger("discord_bot")

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Global runner to allow cleanup
ipc_runner = None


async def handle_verify_request(request):
    """
    HTTP handler inside the bot process to process verification
    requests sent from the main.py process via bot.verify().
    """
    try:
        # Check IPC Secret for security
        auth_header = request.headers.get("Authorization")
        if auth_header != f"Bearer {IPC_SECRET}":
            logger.warning("Unauthorized IPC request attempt")
            return web.json_response({"error": "Unauthorized"}, status=401)

        data = await request.json()
        username = data.get("username")
        if not username:
            return web.json_response({"error": "No username provided"}, status=400)

        logger.info(f"Received verification request for: {username}")

        user_id = None
        guild_id = settings.discord_guild_id

        if not guild_id:
            logger.error("DISCORD_GUILD_ID not set in configuration")
            return web.json_response({"error": "Guild ID not configured"}, status=500)

        guild = bot.get_guild(int(guild_id))
        if not guild:
            logger.error(f"Guild with ID {guild_id} not found")
            return web.json_response({"error": "Guild not found"}, status=500)

        # Look for member only in the specific server
        member = discord.utils.get(guild.members, name=username)

        if not member:
            # If not in cache, try to fetch/query the member
            try:
                found_members = await guild.query_members(query=username, limit=10)
                member = discord.utils.find(
                    lambda m: m.name.lower() == username.lower(), found_members
                )
            except Exception as e:
                logger.error(f"Error querying members in {guild.name}: {e}")

        if member:
            role = discord.utils.get(guild.roles, name=ROLE_NAME)
            if role:
                try:
                    await member.add_roles(role)
                    user_id = str(member.id)
                    logger.info(
                        f"Successfully added role '{ROLE_NAME}' to {username} ({user_id}) in guild {guild.name}"
                    )
                except discord.Forbidden:
                    logger.error(
                        f"[CRITICAL]==> Bot lacks permissions to add role in guild: {guild.name}"
                    )
                    printStat(
                        "c",
                        f"[CRITICAL]==> Bot lacks permissions to add role in guild: {guild.name}",
                    )
                except Exception as e:
                    logger.error(
                        f"[CRITICAL]==> Error adding role in guild {guild.name}: {e}"
                    )
                    printStat(
                        "c",
                        f"[CRITICAL]==> Error adding role in guild {guild.name}: {e}",
                    )

        if user_id:
            return web.json_response({"uid": user_id})
        else:
            logger.warning(
                f"User '{username}' or role '{ROLE_NAME}' not found in any shared guilds."
            )
            return web.json_response({"error": "User or role not found"}, status=404)

    except Exception as e:
        logger.error(f"IPC Server Error: {e}")
        printStat("c", f"IPC Server Error: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def start_ipc_server():
    """Starts the internal web server for inter-process communication"""
    global ipc_runner
    app = web.Application()
    app.router.add_post("/verify", handle_verify_request)
    ipc_runner = web.AppRunner(app)
    await ipc_runner.setup()
    site = web.TCPSite(ipc_runner, "localhost", IPC_PORT)
    await site.start()
    logger.info(f"IPC Server listening on port {IPC_PORT}")
    printStat("o", f"IPC Server listening on port {IPC_PORT}")


async def shutdown(sig, loop):
    """Cleanup tasks on shutdown"""
    logger.info(f"Received exit signal {sig.name}...")
    printStat("o", f"Shutting down bot (Signal: {sig.name})...")

    # Shut the IPC
    if ipc_runner:
        logger.info("Closing IPC server...")
        await ipc_runner.cleanup()

    # Shut the bot
    logger.info("Closing Discord connection...")
    await bot.close()

    # Stop the async loop
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


@bot.event
async def on_ready():
    if bot.user:
        logger.info(f"Bot logged in as {bot.user} (ID: {bot.user.id})")
        printStat("o", f"Bot logged in as {bot.user} (ID: {bot.user.id})")
    await start_ipc_server()


def verify(username: str):
    """
    This is the function called by main.py.
    It communicates with the running bot process via the IPC server.
    Wasn't able to do normal calling because wouldn't execute more than once.

    returns the dc uid, or null if fails.
    """
    url = f"http://localhost:{IPC_PORT}/verify"
    payload = json.dumps({"username": username}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {IPC_SECRET}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data.get("uid")
    except Exception as e:
        printStat("c", f"Failed to communicate with the Discord bot process: {e}")
        return None


if __name__ == "__main__":
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logging.basicConfig(level=logging.INFO)

    loop = asyncio.get_event_loop()

    # Register signal handlers for shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda s=sig: asyncio.create_task(shutdown(s, loop))
        )

    try:
        loop.run_until_complete(bot.start(TOKEN))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
