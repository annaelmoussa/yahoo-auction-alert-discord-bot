import os
import dotenv
import lightbulb
import hikari
import dataset
import asyncio
from easygoogletranslate import EasyGoogleTranslate
from logging import info, basicConfig, INFO
from get import check_get_auctions

basicConfig(
    level=INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

dotenv.load_dotenv()

translator = EasyGoogleTranslate(source_language="jp", target_language="en", timeout=10)
db = dataset.connect("sqlite:///alerts.db")
bot = lightbulb.BotApp(os.environ["BOT_TOKEN"])
bot.d.table = db["alerts"]
bot.d.synced = db["synced_alerts"]


async def check_alerts() -> None:
    while True:
        alerts = list(bot.d.table.all())
        alert_count = len(alerts)
        info(f"Starting alert check cycle. Found {alert_count} alerts to process.")

        for alert in alerts:
            info(f"Processing alert: '{alert['name']}' for user {alert['user_id']} in channel {alert['channel_id']}")
            if os.getenv("ENABLE_GET_AUCTION", "true").lower() == "true":
                try:
                    info(f"Starting search for '{alert['name']}'...")
                    await check_get_auctions(bot, translator, alert)
                except Exception as e:
                    info(f"Error processing alert '{alert['name']}': {str(e)}")
                    info(f"Full error details: {repr(e)}")
            else:
                info("GET auction checking is disabled via ENABLE_GET_AUCTION environment variable")

        check_interval = int(os.getenv("CHECK_INTERVAL", 60))
        info(f"Completed alert check cycle. Next check in {check_interval} seconds.")
        await asyncio.sleep(check_interval)


@bot.listen()
async def on_ready(event: hikari.StartingEvent) -> None:
    info("Starting event loop...")
    await bot.rest.edit_my_user(username="Yapper")
    asyncio.create_task(check_alerts())


@bot.command
@lightbulb.option("currency", "Currency for conversion (e.g. USD, EUR), defaults to JPY", required=False)
@lightbulb.option("name", "Name of the item to register.", required=True)
@lightbulb.command("register", "Register a new alert for a GET Auction item.", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def register(ctx: lightbulb.SlashContext, name: str, currency: str = "JPY") -> None:
    if any(True for _ in bot.d.table.find(name=name)):
        await ctx.respond(f"Alert for **{name}** already exists!")
        return

    bot.d.table.insert({
        "user_id": ctx.author.id,
        "channel_id": ctx.channel_id,
        "name": name,
        "currency": currency
    })
    await ctx.respond(f"Registered alert for **{name}** with currency {currency.upper()}!")


@bot.command
@lightbulb.option("name", "Name of the item to delete.", required=True)
@lightbulb.command("unregister", "Delete an alert", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def unregister(ctx: lightbulb.SlashContext, name: str) -> None:
    if not bot.d.table.find_one(name=name):
        await ctx.respond(f"Alert for **{name}** does not exist!")
        return

    bot.d.table.delete(user_id=ctx.author.id, name=name)
    await ctx.respond(f"Unregistered alert for **{name}**!")


@bot.command
@lightbulb.command("alerts", "List alerts")
@lightbulb.implements(lightbulb.SlashCommand)
async def alerts(ctx: lightbulb.SlashContext) -> None:
    alerts = bot.d.table.find(user_id=ctx.author.id)
    if all(False for _ in alerts):
        await ctx.respond("You have no alerts!")
        return

    await ctx.respond("\n".join([f"{alert['name']}" for alert in alerts]) or "None")
    
if __name__ == "__main__":
    bot.run(
        activity=hikari.Activity(
            name="GET Auction items", type=hikari.ActivityType.WATCHING
        )
    )
