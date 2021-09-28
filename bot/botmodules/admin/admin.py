from telegram.ext import CommandHandler
from utils.glob import *
import utils.config as conf

@msg(adm = True)
def admin_command(update, user):
    user_perms = [conf.perm(ele) for ele in user.permissions()]
    user_perms = [ele for ele in user_perms if not ele is None]
    if len(user_perms) > 0:
        msg = "Ecco i permessi e i comandi che puoi utilizzare! ⚙️\n\n"
        for perm in user_perms:
            msg += f"📌 Nome: {perm.name}\n"
            msg += "👨‍💻 Comandi associati: "
            for i in range(len(perm.commands)):
                msg += f"{perm.commands[i]}"
                if i != len(perm.commands)-1:
                    msg += " - "
            msg+="\n"
            msg+= f"📜 Descrizione: {perm.description}\n\n"
        update.message.reply_text(msg)        
    else:
        update.message.reply_text("Non hai nessun permesso! 🚫")


handlers = [CommandHandler('admin',admin_command)]