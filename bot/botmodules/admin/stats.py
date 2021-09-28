from telegram.ext import CommandHandler
from utils.glob import *
from utils import db, funcs

@msg(adm="stats")
def stats_command(update,user):
    update.message.reply_text(f"""Le statistiche del bot 🤖:

😃 {db.TelegramUser.count_users()} utenti registrati
📰 {funcs.api("/docs/len")["data"]} documenti acquisiti
💡 {funcs.api("/events/len")["data"]} eventi registrati
📌 {len(funcs.api("/docs/pids"))} bacheche registrate
""")

handlers = [CommandHandler('stats',stats_command)]