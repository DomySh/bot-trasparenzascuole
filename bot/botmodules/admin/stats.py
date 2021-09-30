from telegram.ext import CommandHandler
from utils.glob import *
from utils import db

@msg(adm="stats")
def stats_command(update,user):
    update.message.reply_text(f"""Le statistiche del bot 🤖:

😃 {db.TelegramUser.count_users()} utenti registrati
📰 {db.Docs.length()} documenti acquisiti
💡 {db.Events.length()} eventi registrati
📌 {len(db.Docs.pids_info())} bacheche registrate
""")

handlers = [CommandHandler('stats',stats_command)]