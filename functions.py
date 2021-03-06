# -*- coding: utf-8 -*-

# Telegram
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import Updater, Filters, MessageHandler, CommandHandler, CallbackQueryHandler, RegexHandler, CallbackContext
from telegram.error import (TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError)

# Drive
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth

# Custom classes
from classes.StringParser import StringParser

# System libraries
from datetime import date, datetime, timedelta
import json
import re
import random
import os
import sys
import requests
import sqlite3
import logging
import pytz
from urllib.request import urlopen
from bs4 import BeautifulSoup

from module.shared import read_md, check_log, config_map
from module.lezioni import lezioni_cmd
from module.esami import esami_cmd
from module.professori import prof_cmd
from module.scraper_exams import scrape_exams
from module.scraper_lessons import scrape_lessons
from module.scraper_professors import scrape_prof
from module.scraper_notices import scrape_notices
from module.gitlab import gitlab_handler
from module.easter_egg_func import *
from module.regolamento_didattico import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Token of your telegram bot that you created from @BotFather, write it on settings.yml
TOKEN = config_map["token"]

def send_message(update: Update, context: CallbackContext, messaggio):
    msg = ""
    righe = messaggio.split('\n')
    for riga in righe:
        if riga.strip() == "" and len(msg) > 3000:
            context.bot.sendMessage(chat_id=update.message.chat_id, text=msg, parse_mode='Markdown')
            msg = ""
        else:
            msg += riga + "\n"
    context.bot.sendMessage(chat_id=update.message.chat_id, text=msg, parse_mode='Markdown')


def lezioni(update: Update, context: CallbackContext, *m):
    check_log(update, context, "lezioni")
    message_text = lezioni_cmd(update, context, context.args)
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode='Markdown')


def esami(update: Update, context: CallbackContext):
    check_log(update, context, "esami")
    message_text = esami_cmd(context.args)
    if len(message_text) > 4096:
        send_message(update, context, message_text)
    else:
        context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode='Markdown')

# Commands
CUSicon = {0: "🏋",
           1: "⚽️",
           2: "🏀",
           3: "🏈",
           4: "🏐",
           5: "🏊",
           }


def help_cmd():
    output = "@DMI_Bot risponde ai seguenti comandi: \n\n"
    output += "📖 /esami - linka il calendario degli esami\n"
    output += "🗓 /aulario - linka l\'aulario\n"
    output += "👔 /prof <nome> - es. /prof Barbanera\n"
    output += "👥 /rappresentanti - elenco dei rappresentanti del DMI\n"
    output += "📚 /biblioteca - orario biblioteca DMI\n"
    output += CUSicon[random.randint(0, 5)] + " /cus sede e contatti\n"
    output += "  /cloud - linka le cartelle condivise su cloud\n\n"
    output += "Segreteria orari e contatti:\n"
    output += "/sdidattica - segreteria didattica\n"
    output += "/sstudenti - segreteria studenti\n"
    output += "/cea - CEA\n"
    output += "\nERSU orari e contatti\n"
    output += "/ersu - sede centrale\n"
    output += "/ufficioersu - (ufficio tesserini)\n"
    output += "/urp - URP studenti\n\n"
    output += "~Bot~\n"
    output += "📂 /drive - accedi a drive\n"
    output += "📂 /git - /gitlab - accedi a gitlab\n"
    output += "/contributors"
    output += "/regolamentodidattico"
    return output


def informative_callback(update: Update, context: CallbackContext, cmd):
    check_log(update, context, cmd)
    message_text = read_md(cmd)
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode='Markdown')


def exit_cmd():
    output = "."
    return output


def esami_button():
    output = "Scrivi /esami inserendo almeno uno dei seguenti parametri: giorno, materia, sessione (prima, seconda, terza, straordinaria)"
    return output

def lezioni_button():
    output = "Scrivi /lezioni inserendo almeno uno dei seguenti parametri: giorno, materia"
    return output

def callback(update: Update, context: CallbackContext):
    conn = sqlite3.connect('data/DMI_DB.db')
    keyboard2 = [[]]
    icona = ""
    number_row = 0
    number_array = 0

    update.callback_query.data = update.callback_query.data.replace("Drive_", "")

    if len(update.callback_query.data) < 13: # "Accetta" (/request command)

        array_value = update['callback_query']['message']['text'].split(" ")

        try:
            if len(array_value) == 5:
                conn.execute("INSERT INTO 'Chat_id_List' VALUES ("+update.callback_query.data+",'" + array_value[4] + "','" + array_value[1] + "','" + array_value[2] + "','" + array_value[3] + "') ")
                context.bot.sendMessage(chat_id=update.callback_query.data, text="🔓 La tua richiesta è stata accettata. Leggi il file README")
                context.bot.sendDocument(chat_id=update.callback_query.data, document=open('data/README.pdf', 'rb'))

                request_elimination_text = "Richiesta di " + str(array_value[1]) + " " + str(array_value[2]) + " estinta"
                context.bot.editMessageText(text=request_elimination_text, chat_id=config_map['dev_group_chatid'], message_id=update.callback_query.message.message_id)

                context.bot.sendMessage(chat_id=config_map['dev_group_chatid'], text=str(array_value[1]) + " " + str(array_value[2] + str(" è stato inserito nel database")))
            elif len(array_value) == 4:
                conn.execute("INSERT INTO 'Chat_id_List'('Chat_id','Nome','Cognome','Email') VALUES (" + update.callback_query.data + ",'" + array_value[1] + "','" + array_value[2] + "','" + array_value[3] + "')")
                context.bot.sendMessage(chat_id=update.callback_query.data, text="🔓 La tua richiesta è stata accettata. Leggi il file README")
                context.bot.sendDocument(chat_id=update.callback_query.data, document=open('data/README.pdf', 'rb'))

                request_elimination_text = "Richiesta di " + str(array_value[1]) + " " + str(array_value[2]) + " estinta"
                context.bot.editMessageText(text=request_elimination_text, chat_id=config_map['dev_group_chatid'], message_id=update.callback_query.message.message_id)
            else:
                context.bot.sendMessage(chat_id=config_map['dev_group_chatid'], text=str("ERRORE INSERIMENTO: ") + str(update['callback_query']['message']['text']) + " " + str(update['callback_query']['data']))
            conn.commit()
        except Exception as error:
            print(error)
            context.bot.sendMessage(chat_id=config_map['dev_group_chatid'], text=str("ERRORE INSERIMENTO: ") + str(update['callback_query']['message']['text']) + " " + str(update['callback_query']['data']))

        text = ""

    else:
        pid = os.fork()
        if (pid == 0):
            settings_file = "config/settings.yaml"
            gauth2 = GoogleAuth(settings_file=settings_file)
            gauth2.CommandLineAuth()
            # gauth2.LocalWebserverAuth()
            drive2 = GoogleDrive(gauth2)
            bot2 = telegram.Bot(TOKEN)

            file1 = drive2.CreateFile({'id': update.callback_query.data})
            file1.FetchMetadata()
            if file1['mimeType'] == "application/vnd.google-apps.folder":
                file_list2 = None

                try:
                    istance_file = drive2.ListFile({'q': "'"+file1['id']+"' in parents and trashed=false", 'orderBy': 'folder,title'})
                    file_list2 = istance_file.GetList()
                    with open("./logs/debugDrive.txt", "a") as debugfile:
                        debugfile.write("- Log time:\n {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        debugfile.write("- File:\n {}".format(str(json.dumps(file1))))
                        debugfile.write("- IstanceFile:\n {}".format(str(json.dumps(istance_file))))
                        debugfile.write("- FileList:\n {}".format(str(json.dumps(file_list2))))
                        debugfile.write("\n------------\n")
                except Exception as e:
                    with open("./logs/debugDrive.txt", "a") as debugfile:
                        debugfile.write("- Log time:\n {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        debugfile.write("- Error:\n {}".format(e))
                        debugfile.write("\n------------\n")
                    print("- Drive error: {}".format(e))
                    bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text="Si è verificato un errore, ci scusiamo per il disagio. Contatta i devs. /help")
                    sys.exit(0)

                formats = {
                	** { "pdf" : "📕 " },
                	** dict.fromkeys([' a', 'b', 'c'], 10),
                	** dict.fromkeys(["doc", "docx", "txt"], "📘 "),
                	** dict.fromkeys(["jpg", "png", "gif"], "📷 "),
                	** dict.fromkeys(["rar", "zip"], "🗄 "),
                	** dict.fromkeys(["out", "exe"], "⚙ "),
                	** dict.fromkeys(["c", "cpp", "h", "py", "java", "js", "html", "php"], "💻 ")
                }

                for file2 in file_list2:
                    file2.FetchMetadata()
                    if file2['mimeType'] == "application/vnd.google-apps.folder":
                        if number_row >= 1:
                            keyboard2.append([InlineKeyboardButton("🗂 "+file2['title'], callback_data="Drive_" + file2['id'])])
                            number_row = 0
                            number_array += 1
                        else:
                            keyboard2[number_array].append(InlineKeyboardButton("🗂 "+file2['title'], callback_data="Drive_" + file2['id']))
                            number_row += 1
                    else:
                        file_format = file2['title'][-5:] # get last 5 characters of strings
                        file_format = file_format.split(".") # split file_format per "."
                        file_format = file_format[len(file_format)-1] # get last element of file_format

                        icona = "📄 "

                        if file_format in formats.keys():
                            icona = formats[file_format]

                        if number_row >= 1:
                            keyboard2.append([InlineKeyboardButton(icona+file2['title'], callback_data="Drive_" + file2['id'])])
                            number_row = 0
                            number_array += 1
                        else:
                            keyboard2[number_array].append(InlineKeyboardButton(icona+file2['title'], callback_data="Drive_" + file2['id']))
                            number_row += 1

                if len(file1['parents']) > 0 and file1['parents'][0]['id'] != '0ADXK_Yx5406vUk9PVA':
                    keyboard2.append([InlineKeyboardButton("🔙", callback_data="Drive_" + file1['parents'][0]['id'])])

                reply_markup3 = InlineKeyboardMarkup(keyboard2)
                bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text=file1['title']+":", reply_markup=reply_markup3)

            elif file1['mimeType'] == "application/vnd.google-apps.document":
                bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text="Impossibile scaricare questo file poichè esso è un google document, Andare sul seguente link")
                bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text=file1['exportLinks']['application/pdf'])

            else:
                try:
                    file_d = drive2.CreateFile({'id': file1['id']})
                    file_d.FetchMetadata()
                    if int(file_d['fileSize']) < 5e+7:
                        file_d.GetContentFile('file/'+file1['title'])
                        file_s = file1['title']
                        filex = open(str("file/" + file_s), "rb")
                        bot2.sendChatAction(chat_id=update['callback_query']['from_user']['id'], action="UPLOAD_DOCUMENT")
                        bot2.sendDocument(chat_id=update['callback_query']['from_user']['id'], document=filex)
                        os.remove(str("file/" + file_s))
                    else:
                        bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text="File troppo grande per il download diretto, scarica dal seguente link")
                        # file_d['downloadUrl']
                        bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text=file_d['alternateLink'])
                except Exception as e:
                    print("- Drive error: {}".format(e))
                    bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text="Impossibile scaricare questo file, contattare gli sviluppatori del bot")
                    open("logs/errors.txt", "a+").write(str(e) + str(file_d['title'])+"\n")

            sys.exit(0)

        os.waitpid(pid, 0)
    conn.close()



def request(update: Update, context: CallbackContext):
    conn = sqlite3.connect('data/DMI_DB.db')
    chat_id = update.message.chat_id

    if chat_id > 0:
        # if we do not find any chat_id in the db
        if not conn.execute("SELECT Chat_id FROM Chat_id_List WHERE Chat_id = " + str(chat_id)).fetchone():
            message_text = "✉️ Richiesta inviata"
            keyboard = [[]]

            username = ""
            if update['message']['from_user']['username']:
                username = update['message']['from_user']['username']

            update.message.text = re.sub('<|>', '', update.message.text)

            if len(update.message.text.split(" ")) == 4 and "@" in update.message.text.split(" ")[3] and "." in update.message.text.split()[3]:
                text_send = str(update.message.text) + " " + username
                keyboard.append([InlineKeyboardButton("Accetta", callback_data="Drive_"+str(chat_id))])
                reply_markup2 = InlineKeyboardMarkup(keyboard)
                context.bot.sendMessage(chat_id=config_map['dev_group_chatid'], text=text_send, reply_markup=reply_markup2)
            else:
                message_text = "Errore compilazione /request:\n Forma esatta: /request <nome> <cognome> <e-mail> (il nome e il cognome devono essere scritti uniti Es: Di mauro -> Dimauro)"
        else:
            message_text = "Hai già effettuato la richiesta di accesso"
    else:
        message_text = "Non è possibile utilizzare /request in un gruppo"

    context.bot.sendMessage(chat_id=chat_id, text=message_text)
    conn.close()


def add_db(update: Update, context: CallbackContext):
    conn = sqlite3.connect('data/DMI_DB.db')
    chat_id = update.message.chat_id

    if (config_map['dev_group_chatid'] != 0 and chat_id == config_map['dev_group_chatid']):
        # /add nome cognome e-mail username chatid
        array_value = update.message.text.split(" ")
        if len(array_value) == 6:
            conn.execute("INSERT INTO 'Chat_id_List' VALUES (" + array_value[5] + ",'" + array_value[4] + "','" + array_value[1] + "','" + array_value[2] + "','" + array_value[3] + "') ")
            context.bot.sendMessage(chat_id=array_value[5], text="🔓 La tua richiesta è stata accettata. Leggi il file README")
            context.bot.sendDocument(chat_id=array_value[5], document=open('data/README.pdf', 'rb'))
            conn.commit()
        elif len(array_value) == 5:
            conn.execute("INSERT INTO 'Chat_id_List'('Chat_id','Nome','Cognome','Email') VALUES (" + array_value[4] + ",'" + array_value[1] + "','" + array_value[2] + "','" + array_value[3] + "')")
            context.bot.sendMessage(chat_id=int(array_value[4]), text="🔓 La tua richiesta è stata accettata. Leggi il file README")
            context.bot.sendDocument(chat_id=int(array_value[4]), document=open('data/README.pdf', 'rb'))
            conn.commit()
        else:
            context.bot.sendMessage(chat_id=chat_id, text="/adddb <nome> <cognome> <e-mail> <username> <chat_id>")
    conn.close()


def drive(update: Update, context: CallbackContext):
    check_log(update, context, "drive")
    conn = sqlite3.connect('data/DMI_DB.db')

    settings_file = "config/settings.yaml"
    gauth = GoogleAuth(settings_file=settings_file)
    gauth.CommandLineAuth()
    # gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    chat_id = update.message.chat_id
    id_drive = '0B7-Gi4nb88hremEzWnh3QmN3ZlU'
    if chat_id < 0:
        context.bot.sendMessage(chat_id=chat_id, text="La funzione /drive non è ammessa nei gruppi")
    else:
        if conn.execute("SELECT Chat_id FROM 'Chat_id_List' WHERE Chat_id = " + str(chat_id)).fetchone():
            keyboard2 = [[]]

            try:
                file_list = drive.ListFile({'q': "'" + id_drive + "' in parents and trashed=false", 'orderBy': 'folder,title'}).GetList()
            except Exception as error:
                print (str(error))

            number_row = 0
            number_array = 0

            for file1 in file_list:
                if file1['mimeType'] == "application/vnd.google-apps.folder":
                    if number_row >= 3:
                        keyboard2.append([InlineKeyboardButton("🗂 "+file1['title'], callback_data="Drive_" + file1['id'])])
                        number_row = 0
                        number_array += 1
                    else:
                        keyboard2[number_array].append(InlineKeyboardButton("🗂 "+file1['title'], callback_data="Drive_" + file1['id']))
                        number_row += 1
                else:
                    if number_row >= 3:
                        keyboard2.append([InlineKeyboardButton("📃 "+file1['title'], callback_data="Drive_" + file1['id'])])
                        number_row = 0
                        number_array += 1
                    else:
                        keyboard2[number_array].append(InlineKeyboardButton("📃 "+file1['title'], callback_data="Drive_" + file1['id']))
                        number_row += 1

            reply_markup3 = InlineKeyboardMarkup(keyboard2)
            context.bot.sendMessage(chat_id=chat_id, text="DMI UNICT - Appunti & Risorse:", reply_markup=reply_markup3)
        else:
            context.bot.sendMessage(chat_id=chat_id, text="🔒 Non hai i permessi per utilizzare la funzione /drive,\n Utilizzare il comando /request <nome> <cognome> <e-mail> (il nome e il cognome devono essere scritti uniti Es: Di mauro -> Dimauro) ")
    conn.close()


def help(update: Update, context: CallbackContext):
    check_log(update, context, "help")
    chat_id = update.message.chat_id
    keyboard = [[]]
    message_text = "@DMI_Bot risponde ai seguenti comandi:"

    keyboard.append([InlineKeyboardButton(" ~ Dipartimento e CdL ~ ", callback_data="_div")])

    keyboard.append(
        [
            InlineKeyboardButton("📖 Esami (Triennale)",    url='http://dev7.unict.it/_esami_x_curl.php?cds=X81&aa=1' + str(get_year_code(12 , 20))),
            InlineKeyboardButton("📖 Esami (Magistrale)",   url='http://dev7.unict.it/_esami_x_curl.php?cds=W82&aa=1' + str(get_year_code(12 , 20))),
            InlineKeyboardButton("🗓 Aulario",              url='http://aule.dmi.unict.it/aulario/roschedule.php'),
            InlineKeyboardButton("Lezioni",                 url='http://web.dmi.unict.it/corsi/l-31/orario-lezioni')
        ]
    )

    keyboard.append(
        [InlineKeyboardButton("Regolamento Didattico", callback_data="regolamentodidattico_button")]
    )

    keyboard.append(
        [
            InlineKeyboardButton("👥 Rappresentanti",                       callback_data="sm_rapp_menu"),
            InlineKeyboardButton("📚 Biblioteca",                           callback_data="md_biblioteca"),
            InlineKeyboardButton(CUSicon[random.randint(0, 5)] + " CUS",    callback_data="md_cus"),
            InlineKeyboardButton("☁️ Cloud",                                 callback_data="md_cloud")
        ]
    )

    keyboard.append([InlineKeyboardButton(" ~ Segreteria orari e contatti ~ ", callback_data="_div")])

    keyboard.append(
        [
            InlineKeyboardButton("Seg. Didattica",  callback_data="md_sdidattica"),
            InlineKeyboardButton("Seg. Studenti",   callback_data="md_sstudenti"),
            InlineKeyboardButton("CEA",             callback_data="md_cea")
        ]
    )

    keyboard.append([InlineKeyboardButton(" ~ ERSU orari e contatti ~ ", callback_data="_div")])

    keyboard.append(
        [
            InlineKeyboardButton("ERSU",          callback_data="md_ersu"),
            InlineKeyboardButton("Ufficio ERSU",  callback_data="md_ufficioersu"),
            InlineKeyboardButton("URP",           callback_data="md_urp")
        ]
    )

    keyboard.append([InlineKeyboardButton(" ~ Bot e varie ~ ", callback_data="_div")])

    keyboard.append(
        [
            InlineKeyboardButton("📂 Drive",     callback_data="md_drive"),
            InlineKeyboardButton("📂 GitLab",    callback_data="md_gitlab"),
            InlineKeyboardButton("Contributors", callback_data="md_contributors"),
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton("Tutti i comandi", callback_data="help_cmd"),
            InlineKeyboardButton("Chiudi",          callback_data="exit_cmd")
        ]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.sendMessage(chat_id=chat_id, text=message_text, reply_markup=reply_markup)


def rapp_menu(update: Update, context: CallbackContext, chat_id, message_id):
    keyboard = [[]]
    message_text = "Quali rappresentanti vuoi contattare?"

    keyboard.append(
        [
            InlineKeyboardButton("Rapp. DMI",         callback_data="md_rappresentanti_dmi"),
            InlineKeyboardButton("Rapp. Informatica", callback_data="md_rappresentanti_informatica"),
            InlineKeyboardButton("Rapp. Matematica",  callback_data="md_rappresentanti_matematica"),
        ]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)


def prof(update: Update, context: CallbackContext):
    check_log(update, context, "prof")
    message_text = prof_cmd(context.args)
    if len(message_text) > 4096:
        send_message(update, context, message_text)
    else:
        context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode='Markdown')


def stats_gen(update: Update, context: CallbackContext, days):
    conn = sqlite3.connect('data/DMI_DB.db')
    chat_id = update.message.chat_id
    query = ""
    text = ""

    if days == 0:
        text += "Record Globale:\n"
        query = "SELECT Type, count(chat_id) FROM stat_list GROUP BY Type ORDER BY Type;"
    else:
        text += "Record di "+str(days)+" giorni:\n"
        query = "SELECT Type, count(chat_id) FROM stat_list WHERE DateCommand > '"+ str(date.today()-timedelta(days=days)) + "' GROUP BY Type ORDER BY Type;"

    for row in conn.execute(query):
        if str(row[0]) != "leiCheNePensaSignorina" and str(row[0]) != "smonta_portoni" and str(row[0]) != "santino" and str(row[0]) != "bladrim" and str(row[0]) != "prof_sticker":
            text += str(row[1]) + ": " + str(row[0]) + "\n"
    context.bot.sendMessage(chat_id=chat_id, text=text)
    conn.close()

def stats(update: Update, context: CallbackContext):
    if(len(update['message']['text'].split(' ')) == 2):
        days = int(update['message']['text'].split(' ')[1])
        if(days <= 0):
            days = 30
    else:
        days = 30
    stats_gen(update, context, days)

def stats_tot(update: Update, context: CallbackContext):
    stats_gen(update, context, 0)

def give_chat_id(update: Update, context: CallbackContext):
    update.message.reply_text(str(update.message.chat_id))


def send_log(update: Update, context: CallbackContext):
    if(config_map['dev_group_chatid'] != 0 and update.message.chat_id == config_map['dev_group_chatid']):
        context.bot.sendDocument(chat_id=config_map['dev_group_chatid'], document=open('logs/logs.txt', 'rb'))


def send_chat_ids(update: Update, context: CallbackContext):
    if(config_map['dev_group_chatid'] != 0 and update.message.chat_id == config_map['dev_group_chatid']):
        context.bot.sendDocument(chat_id=config_map['dev_group_chatid'], document=open('logs/chatid.txt', 'rb'))


def send_errors(update: Update, context: CallbackContext):
    if(config_map['dev_group_chatid'] != 0 and update.message.chat_id == config_map['dev_group_chatid']):
        context.bot.sendDocument(chat_id=config_map['dev_group_chatid'], document=open('logs/errors.txt', 'rb'))

def updater_lep(context):
    job = context.job
    year_exam = get_year_code(11 , 30) # aaaa/12/01 (cambio nuovo anno esami) data dal quale esami del vecchio a nuovo anno coesistono
    scrape_exams("1" + str(year_exam), delete= True) # flag che permette di eliminare tutti gli esami presenti in tabella exams
    if(check_print_old_exams(year_exam)):
        scrape_exams("1" + str(int(year_exam) - 1))
    scrape_lessons("1" + str(get_year_code(9 , 20))) # aaaa/09/21 (cambio nuovo anno lezioni) data dal quale vengono prelevate le lezioni del nuovo anno
    scrape_prof()

def check_print_old_exams(year_exam):
    date_time = get_current_date()
    ckdate = get_checkdate(date_time.year, 12, 23) # aaaa/12/24 data dal quale vengono prelevati solo gli esami del nuovo anno
    if((year_exam != str(date_time.year)[-2:]) and date_time < ckdate):
        return True
    return False

def get_checkdate(year, month, day):
    tz = pytz.timezone('Europe/Rome')
    checkdate = datetime(year= year, month= month, day= day)
    checkdate = tz.localize(checkdate)
    return checkdate

def get_current_date():
    tz = pytz.timezone('Europe/Rome')
    date_time = datetime.now(tz)
    return date_time

def get_year_code(month, day):
    date_time = get_current_date()
    check_new_year = get_checkdate(date_time.year, month, day)
    year = date_time.year
    if date_time > check_new_year:
        year = date_time.year + 1
    return str(year)[-2:]

def start(update: Update, context: CallbackContext):
    context.bot.sendMessage(chat_id=update.message.chat_id, text="Benvenuto! Questo bot è stato realizzato dagli studenti del Corso di Laurea in Informatica al fine di suppotare gli studenti del DMI! Per scoprire cosa puoi fare usa /help")

def git(update: Update, context: CallbackContext):
    check_log(update, context, "gitlab")

    chat_id = update.message.chat_id
    executed_command = update.message.text.split(' ')[0]

    if chat_id < 0:
        context.bot.sendMessage(chat_id=chat_id, text="❗️ La funzione %s non è ammessa nei gruppi" % executed_command)
    else:
        db = sqlite3.connect('data/DMI_DB.db')

        if db.execute("SELECT Chat_id FROM 'Chat_id_List' WHERE Chat_id = %s" % chat_id).fetchone():
            gitlab_handler(update, context)
        else:
            context.bot.sendMessage(chat_id=chat_id, text="🔒 Non hai i permessi per utilizzare la funzione %s\nUtilizzare il comando /request <nome> <cognome> <e-mail> (il nome e il cognome devono essere scritti uniti Es: Di Mauro -> DiMauro)" % executed_command)

        db.close()

def report(update: Update, context: CallbackContext):
    check_log(update, context, "report")
    chat_id = update.message.chat_id
    chat_username = update.message.from_user.username
    executed_command = update.message.text.split(' ')[0]


    if chat_id < 0:
        context.bot.sendMessage(chat_id=chat_id, text="! La funzione %s non è ammessa nei gruppi" % executed_command)
    elif not chat_username:
        context.bot.sendMessage(chat_id=chat_id, text="La funzione %s non è ammessa se non si dispone di un username." % executed_command)
    else:
        if  context.args:
            db = sqlite3.connect('data/DMI_DB.db')
            message = "⚠️Segnalazione⚠️\n"
            if db.execute("SELECT Chat_id FROM 'Chat_id_List' WHERE Chat_id = %s" %chat_id).fetchone():
                name = db.execute("SELECT Username,Nome,Cognome FROM 'Chat_id_List' WHERE Chat_id = %s" %chat_id)
                row = name.fetchone()

                if row[0] is None:
                    message += "Nome: " + row[1] + "\n" + "Cognome: " + row[2] + "\n" + " ".join(context.args)
                else:
                    message += "Username: @" + row[0] + "\n" + "Nome: " + row[1] + "\n" + "Cognome: " + row[2] + "\n" + " ".join(context.args)
                context.bot.sendMessage(chat_id = config_map['representatives_group'], text = message)
                context.bot.sendMessage(chat_id = chat_id, text = "Resoconto segnalazione: \n" + message + "\n Grazie per la segnalazione, un rappresentante ti contatterà nel minor tempo possibile.")

                db.close()
            else:
                context.bot.sendMessage(chat_id=chat_id, text="🔒 Non hai i permessi per utilizzare la funzione %s\nUtilizzare il comando /request <nome> <cognome> <e-mail> (il nome e il cognome devono essere scritti uniti Es: Di Mauro -> DiMauro)" % executed_command)

        else:
            context.bot.sendMessage(chat_id = chat_id, text="Errore. Inserisci la tua segnalazione dopo /report (Ad esempio /report Invasione ingegneri in corso.)")

# Callback Query Handlers

def submenu_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    func_name = data[3:len(data)]
    globals()[func_name](
      query,
      context,
      query.message.chat_id,
      query.message.message_id
    )
  
def generic_button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    message_text = globals()[data]()
    context.bot.editMessageText(
      text=message_text,
      chat_id=query.message.chat_id,
      message_id=query.message.message_id
    )

def md_handler(update: Update, context: CallbackContext):
    query = update.callback_query

    data = query.data.replace("md_", "")

    message_text = read_md(data)
    check_log(update, context, data, 1)

    context.bot.editMessageText(
      text=message_text,
      chat_id=query.message.chat_id,
      message_id=query.message.message_id,
      parse_mode='Markdown'
    )
