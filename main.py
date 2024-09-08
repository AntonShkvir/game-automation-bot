import datetime
from threading import Lock

import requests as req
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, \
    filters, ContextTypes

from bot.config.config import API_TOKEN
import os
import asyncio
from pyrogram import Client, errors
from bot.core.tapper import run_tapper

lock = Lock()
users = {}
memefi_users = {}
sessions_users = {}
users_phone_code_hash = {}
users_current_session_name = {}


def load_whitelist(f) -> set:
    try:
        with open(f, 'r') as file:
            return set(json.load(file))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_whitelist(data: set, f) -> None:
    with open(f, 'w') as file:
        json.dump(list(data), file)


def load(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save(data, user):
    with lock:
        with open(f"sessions/{user}/threads.json", "w") as json_file:
            json.dump(data, json_file, indent=4)

def save_sessions(data):
    with lock:
        with open("sessions/sessions.json", "w") as json_file:
            json.dump(data, json_file, indent=4)

whitelist = load_whitelist('whitelist.json')

stop_events = {}
stopped_sessions = {}
threads = {}
session_names_for_users_preload = load("sessions/sessions.json")
session_names_for_users = {}
for key, value in session_names_for_users_preload.items():
    session_names_for_users[int(key)] = value


for subdir, _, files in os.walk("sessions"):
    for file in files:
        if file == 'threads.json':
            file_path = os.path.join(subdir, file)
            os.remove(file_path)

async def async_function(tg_client, context, user):
    await run_tapper(tg_client=tg_client, context=context, proxy='', user_id=user)




def stop_async_function(name, user_id):
    parts = name.split('_', maxsplit=1)
    threads[user_id].remove(parts[1])
    save(threads[user_id], user_id)




async def start(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id in whitelist:
        keyboard = [[InlineKeyboardButton("Blum", callback_data='Blum')],
                    [InlineKeyboardButton("Memefi", callback_data='Memefi')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.message.chat_id,
                                       text="Выберете проект для запуска бота. Имейте ввиду что наш бот не имеет доступа к вашим личным данным.",
                                       reply_markup=reply_markup)
    else:
        keyboard = [[InlineKeyboardButton("Купить бота", url="https://t.me/")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.message.chat_id, text="Бот работает только после его покупки",
                                       reply_markup=reply_markup)
async def delete_session(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    chat_id = job.data[0]
    message_id = job.data[1]
    keyboard = [[InlineKeyboardButton("⏬ Добавить сессию ⏬", callback_data='Add session')],
                [InlineKeyboardButton("🗒 Мои сессии 🗒", callback_data=f"Sessions|{chat_id}|0")],
                [InlineKeyboardButton("<<<", callback_data='Back to menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.edit_message_text(
        text="Наш бот поможет вам автоматизировать игру в MemeFi, собирать монеты и покупать улучшения. Важно: наш бот не имеет доступа к личным данным пользователя",
        chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)


async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    if query.data == "Blum":

        keyboard = [[InlineKeyboardButton("Bearer Token", callback_data='Bearer')],
                    [InlineKeyboardButton("Telegram API token", callback_data='Telegram API')],
                    [InlineKeyboardButton("Туториал", callback_data='Tutorial')],
                    [InlineKeyboardButton("<<<", callback_data='Back to menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.edit_message_text(
            text="*Наш бот поможет вам собирать очки за билетики в Blum автоматически, через игровой токен в игре (как его получить смотрите по кнопке \"Туториал\"). Важно: наш бот не имеет доступа к личным данным пользователя*",
            chat_id=query.message.chat.id, message_id=query.message.message_id, reply_markup=reply_markup)
    elif query.data == "Memefi":
        if update.effective_chat.id not in stop_events.keys():
            stop_events[update.effective_chat.id] = []
        keyboard = [[InlineKeyboardButton("⏬ Добавить сессию ⏬", callback_data='Add session')],
                    [InlineKeyboardButton("🗒 Мои сессии 🗒", callback_data=f"Sessions|{query.from_user.id}|0")]]

        user_threads = load(f"sessions/{query.from_user.id}/threads.json")
        if query.from_user.id in session_names_for_users.keys() and len(session_names_for_users[
            query.from_user.id]) >= 1 and user_threads == []:
            keyboard.append([InlineKeyboardButton("Запустить все сессии", callback_data='start all')])
        keyboard.append([InlineKeyboardButton("<<<", callback_data='Back to menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.edit_message_text(
            text="Наш бот поможет вам автоматизировать игру в MemeFi, собирать монеты и покупать улучшения. Важно: наш бот не имеет доступа к личным данным пользователя",
            chat_id=query.message.chat.id, message_id=query.message.message_id, reply_markup=reply_markup)

    elif query.data == 'Add session':
        keyboard = [[InlineKeyboardButton("<<<", callback_data='Back to memefi')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.edit_message_text(
            text="Введите название для сессии",
            chat_id=query.message.chat.id, message_id=query.message.message_id, reply_markup=reply_markup)
        users[query.from_user.id] = 'collect session name'


    elif query.data == 'stop all':
        user_threads = load(f"sessions/{query.from_user.id}/threads.json")
        for i in user_threads:
            name = str(query.from_user.id) + '_' + str(i)
            stop_async_function(name, query.from_user.id)
        keyboard = [[InlineKeyboardButton("⏬ Добавить сессию ⏬", callback_data='Add session')],
                    [InlineKeyboardButton("🗒 Мои сессии 🗒", callback_data=f"Sessions|{query.from_user.id}|0")]]

        user_threads = load(f"sessions/{query.from_user.id}/threads.json")
        if query.from_user.id in session_names_for_users.keys() and len(session_names_for_users[
                                                                            query.from_user.id]) >= 1 and user_threads == []:
            keyboard.append([InlineKeyboardButton("🚀 Запустить все сессии 🚀", callback_data='start all')])
        keyboard.append([InlineKeyboardButton("<<<", callback_data='Back to menu')])
        await context.bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.split('|')[0] == "Stop session":
        stop_async_function(query.data.split('|')[1], query.from_user.id)
        name = query.data.split('|')[1]
        name = name.split('_', maxsplit=1)
        name = name[1]
        user_threads = load(f"sessions/{query.from_user.id}/threads.json")
        if len(session_names_for_users[query.from_user.id]) == 1:
            if name in user_threads:
                keyboard = [[InlineKeyboardButton("🚫 Остановить 🚫",
                                                  callback_data=f"Stop session|{str(query.from_user.id) + '_' + name}|{int(query.data.split('|')[2])}")],
                            [InlineKeyboardButton("<<<", callback_data='Back to memefi')]]
            else:
                keyboard = [[InlineKeyboardButton("🚀 Запустить 🚀",
                                                  callback_data=f"Start session|{session_names_for_users[query.from_user.id][0][0]}|0")],
                            [InlineKeyboardButton("🗑 Удалить 🗑",
                                                  callback_data=f"Delete session|{session_names_for_users[query.from_user.id][0][0]}|0")],
                            [InlineKeyboardButton("<<<", callback_data='Back to memefi')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.edit_message_text(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                                text=f"Сессия №{int(query.data.split('|')[2]) + 1}\n\nНазвание: {name}\nДата создания: {session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][1]}\nСтатус: {'Активно🟢' if session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0] in user_threads else 'Не активно🔴'}",
                                                reply_markup=reply_markup)
        elif len(session_names_for_users[query.from_user.id]) == 0:
            keyboard = [[InlineKeyboardButton("<<<", callback_data='Back to memefi')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.edit_message_text(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                                text="У вас нет ни одной сессии, добавьте ее через кнопку «Добавить сессию»",
                                                reply_markup=reply_markup)
        else:
            if name in user_threads:
                keyboard = [

                    [InlineKeyboardButton("🚫 Остановить 🚫",
                                          callback_data=f"Stop session|{str(query.from_user.id) + '_' + name}|{int(query.data.split('|')[2])}")],
                    [InlineKeyboardButton("◀️",
                                          callback_data=f"Sessions|{query.from_user.id}|{int(query.data.split('|')[2]) - 1 if int(query.data.split('|')[2]) - 1 >= 0 else len(session_names_for_users[query.from_user.id]) - 1}"),
                     InlineKeyboardButton("▶️",
                                          callback_data=f"Sessions|{query.from_user.id}|{int(query.data.split('|')[2]) + 1 if len(session_names_for_users[query.from_user.id]) > int(query.data.split('|')[2]) + 1 else 0}")],
                    [InlineKeyboardButton("<<<", callback_data='Back to memefi')]]
            else:
                keyboard = [

                    [InlineKeyboardButton("🚀 Запустить 🚀",
                                          callback_data=f"Start session|{session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0]}|{int(query.data.split('|')[2])}")],
                    [InlineKeyboardButton("🗑 Удалить 🗑",
                                          callback_data=f"Delete session|{session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0]}|{int(query.data.split('|')[2])}")],
                    [InlineKeyboardButton("◀️",
                                          callback_data=f"Sessions|{query.from_user.id}|{int(query.data.split('|')[2]) - 1 if int(query.data.split('|')[2]) - 1 >= 0 else len(session_names_for_users[query.from_user.id]) - 1}"),
                     InlineKeyboardButton("▶️",
                                          callback_data=f"Sessions|{query.from_user.id}|{int(query.data.split('|')[2]) + 1 if len(session_names_for_users[query.from_user.id]) > int(query.data.split('|')[2]) + 1 else 0}")],
                    [InlineKeyboardButton("<<<", callback_data='Back to memefi')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.edit_message_text(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                                text=f"Сессия №{int(query.data.split('|')[2]) + 1}\n\nНазвание: {name}\nДата создания: {session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][1]}\nСтатус: {'Активно🟢' if session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0] in user_threads else 'Не активно🔴'}",
                                                reply_markup=reply_markup)


    elif query.data == 'start all':
        for i in session_names_for_users[query.from_user.id]:
            name = i[0]
            api_id = i[2]
            api_hash = i[3]
            try:
                tg_client = Client(
                    name=name,
                    api_id=api_id,
                    api_hash=api_hash,
                    workdir=f'sessions/{query.from_user.id}/',
                    plugins=dict(root='bot/plugins')
                )
                process = asyncio.create_task(async_function(tg_client, name, context, update.effective_chat.id))
                user = update.effective_chat.id
                if user not in threads.keys():
                    threads[user] = [name]
                else:
                    threads[user].append(name)
            except Exception as e:
                print(e)
        save(threads[update.effective_chat.id], update.effective_chat.id)
        keyboard = [[InlineKeyboardButton("⏬ Добавить сессию ⏬", callback_data='Add session')],
                    [InlineKeyboardButton("🗒 Мои сессии 🗒", callback_data=f"Sessions|{query.from_user.id}|0")],
                    [InlineKeyboardButton("🚫 Остановить все сессии 🚫", callback_data='stop all')]]
        keyboard.append([InlineKeyboardButton("<<<", callback_data='Back to menu')])
        await context.bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                            reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.split('|')[0] == "Start session":
        name = session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0]
        api_id = session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][2]
        api_hash = session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][3]
        tg_client = Client(
            name=name,
            api_id=api_id,
            api_hash=api_hash,
            workdir=f'sessions/{query.from_user.id}/',
            plugins=dict(root='bot/plugins')
        )
        process = asyncio.create_task(async_function(tg_client, name, context, update.effective_chat.id))
        user = update.effective_chat.id
        if user not in threads.keys():
            threads[user] = [name]
        else:
            threads[user].append(name)

        save(threads[user], user)
        user_threads = load(f"sessions/{query.from_user.id}/threads.json")

        if len(session_names_for_users[query.from_user.id]) == 1:
            if name in user_threads:
                keyboard = [[InlineKeyboardButton("🚫 Остановить 🚫",
                                                  callback_data=f"Stop session|{str(query.from_user.id) + '_' + name}|{int(query.data.split('|')[2])}")],
                            [InlineKeyboardButton("<<<", callback_data='Back to memefi')]]

            else:
                keyboard = [[InlineKeyboardButton("🚀 Запустить 🚀",
                                                  callback_data=f"Start session|{session_names_for_users[query.from_user.id][0][0]}|0")],
                            [InlineKeyboardButton("🗑 Удалить 🗑",
                                                  callback_data=f"Delete session|{session_names_for_users[query.from_user.id][0][0]}|0")],
                            [InlineKeyboardButton("<<<", callback_data='Back to memefi')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.edit_message_text(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                                text=f"Сессия №{int(query.data.split('|')[2]) + 1}\n\nНазвание: {name}\nДата создания: {session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][1]}\nСтатус: {'Активно🟢' if session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0] in user_threads else 'Не активно🔴'}",
                                                reply_markup=reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🚫 Остановить 🚫",
                                              callback_data=f"Stop session|{str(query.from_user.id) + '_' + name}|{int(query.data.split('|')[2])}")],
                        [InlineKeyboardButton("◀️",
                                              callback_data=f"Sessions|{query.from_user.id}|{int(query.data.split('|')[2]) - 1 if int(query.data.split('|')[2]) - 1 >= 0 else len(session_names_for_users[query.from_user.id]) - 1}"),
                         InlineKeyboardButton("▶️",
                                              callback_data=f"Sessions|{query.from_user.id}|{int(query.data.split('|')[2]) + 1 if len(session_names_for_users[query.from_user.id]) > int(query.data.split('|')[2]) + 1 else 0}")],

                        [InlineKeyboardButton("<<<", callback_data='Back to memefi')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.edit_message_text(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                                text=f"Сессия №{int(query.data.split('|')[2]) + 1}\n\nНазвание: {name}\nДата создания: {session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][1]}\nСтатус: {'Активно🟢' if session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0] in user_threads else 'Не активно🔴'}",
                                                reply_markup=reply_markup)

    elif query.data.split('|')[0] == "Delete session":

        keyboard = [[InlineKeyboardButton("Да ✅", callback_data=f'confirm deletion|{query.data.split('|')[1]}'),
                     InlineKeyboardButton("Нет ❌",
                                          callback_data=f'cancel deletion|{query.data.split('|')[1]}|{query.data.split('|')[2]}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.edit_message_text(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                            text=f"Вы действительно хотите удалить сессию {query.data.split('|')[1]}?",
                                            reply_markup=reply_markup)

    elif query.data.split('|')[0] == 'confirm deletion':
        flag = True
        try:
            os.remove(f"sessions/{query.from_user.id}/{query.data.split('|')[1]}.session")
        except:
            flag = False

        if flag:
            session_names_for_users[query.from_user.id] = [
                session for session in session_names_for_users[query.from_user.id]
                if session[0] != query.data.split('|')[1]
            ]
            if len(session_names_for_users[query.from_user.id]) == 0:
                session_names_for_users.pop(query.from_user.id)
            session_names_for_users_upload = {}
            for key, value in session_names_for_users.items():
                session_names_for_users_upload[str(key)] = value
            save_sessions(session_names_for_users_upload, update.effective_chat.id)

            keyboard = [[InlineKeyboardButton("Удалено", callback_data='None')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.edit_message_reply_markup(chat_id=update.effective_chat.id,
                                                        message_id=query.message.message_id,
                                                        reply_markup=reply_markup)
            context.job_queue.run_once(delete_session, 1, chat_id=update.effective_chat.id,
                                       data=[update.effective_chat.id, query.message.message_id])
        else:
            await context.bot.send_message(chat_id=query.from_user.id, text='Не получилось удалить')

    elif query.data.split('|')[0] == 'cancel deletion':
        name = session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0]
        user_threads = load(f"sessions/{query.from_user.id}/threads.json")
        if len(session_names_for_users[query.from_user.id]) == 1:
            if name in user_threads:
                keyboard = [[InlineKeyboardButton("🚫 Остановить 🚫",
                                                  callback_data=f"Stop session|{str(query.from_user.id) + '_' + name}|{int(query.data.split('|')[2])}")],
                            [InlineKeyboardButton("<<<", callback_data='Back to memefi')]]
            else:
                keyboard = [[InlineKeyboardButton("🚀 Запустить 🚀",
                                                  callback_data=f"Start session|{session_names_for_users[query.from_user.id][0][0]}|0")],
                            [InlineKeyboardButton("🗑 Удалить 🗑",
                                                  callback_data=f"Delete session|{session_names_for_users[query.from_user.id][0][0]}|0")],
                            [InlineKeyboardButton("<<<", callback_data='Back to memefi')]]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.edit_message_text(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                                text=f"Сессия №{int(query.data.split('|')[2]) + 1}\n\nНазвание: {session_names_for_users[query.from_user.id][0][0]}\nДата создания: {session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][1]}\nСтатус: {'Активно🟢' if session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0] in user_threads else 'Не активно🔴'}",
                                                reply_markup=reply_markup)
        elif len(session_names_for_users[query.from_user.id]) == 0:
            keyboard = [[InlineKeyboardButton("<<<", callback_data='Back to memefi')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.edit_message_text(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                                text="У вас нет ни одной сессии, добавьте ее через кнопку «Добавить сессию»",
                                                reply_markup=reply_markup)
        else:
            if name in user_threads:
                keyboard = [

                    [InlineKeyboardButton("🚫 Остановить 🚫",
                                          callback_data=f"Stop session|{str(query.from_user.id) + '_' + name}|{int(query.data.split('|')[2])}")],
                    [InlineKeyboardButton("◀️",
                                          callback_data=f"Sessions|{query.from_user.id}|{int(query.data.split('|')[2]) - 1 if int(query.data.split('|')[2]) - 1 >= 0 else len(session_names_for_users[query.from_user.id]) - 1}"),
                     InlineKeyboardButton("▶️",
                                          callback_data=f"Sessions|{query.from_user.id}|{int(query.data.split('|')[2]) + 1 if len(session_names_for_users[query.from_user.id]) > int(query.data.split('|')[2]) + 1 else 0}")],
                    [InlineKeyboardButton("<<<", callback_data='Back to memefi')]]
            else:
                keyboard = [

                    [InlineKeyboardButton("🚀 Запустить 🚀",
                                          callback_data=f"Start session|{session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0]}|{int(query.data.split('|')[2])}")],
                    [InlineKeyboardButton("🗑 Удалить 🗑",
                                          callback_data=f"Delete session|{session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0]}|{int(query.data.split('|')[2])}")],
                    [InlineKeyboardButton("◀️",
                                          callback_data=f"Sessions|{query.from_user.id}|{int(query.data.split('|')[2]) - 1 if int(query.data.split('|')[2]) - 1 >= 0 else len(session_names_for_users[query.from_user.id]) - 1}"),
                     InlineKeyboardButton("▶️",
                                          callback_data=f"Sessions|{query.from_user.id}|{int(query.data.split('|')[2]) + 1 if len(session_names_for_users[query.from_user.id]) > int(query.data.split('|')[2]) + 1 else 0}")],
                    [InlineKeyboardButton("<<<", callback_data='Back to memefi')]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.edit_message_text(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                            text=f"Сессия №{int(query.data.split('|')[2]) + 1}\n\nНазвание: {session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0]}\nДата создания: {session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][1]}\nСтатус: {'Активно🟢' if session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0] in user_threads else 'Не активно🔴'}",
                                            reply_markup=reply_markup)

    elif query.data.split('|')[0] == "Sessions":
        if query.from_user.id not in session_names_for_users.keys() or session_names_for_users[query.from_user.id] == []:
            keyboard = [[InlineKeyboardButton("<<<", callback_data='Back to memefi')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.edit_message_text(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                                text="У вас нет ни одной сессии, добавьте ее через кнопку «Добавить сессию»", reply_markup=reply_markup)
        else:
            name = session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0]
            user_threads = load(f"sessions/{query.from_user.id}/threads.json")

            if len(session_names_for_users[query.from_user.id]) == 1:
                if name in user_threads:
                    keyboard = [[InlineKeyboardButton("🚫 Остановить 🚫", callback_data=f"Stop session|{str(query.from_user.id) + '_' + name}|{int(query.data.split('|')[2])}")],
                                [InlineKeyboardButton("<<<", callback_data='Back to memefi')]]
                else:
                    keyboard = [[InlineKeyboardButton("🚀 Запустить 🚀",
                                                      callback_data=f"Start session|{session_names_for_users[query.from_user.id][0][0]}|0")],
                                [InlineKeyboardButton("🗑 Удалить 🗑",
                                                      callback_data=f"Delete session|{session_names_for_users[query.from_user.id][0][0]}|0")],
                                [InlineKeyboardButton("<<<", callback_data='Back to memefi')]]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.edit_message_text(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                                    text=f"Сессия №{int(query.data.split('|')[2]) + 1}\n\nНазвание: {session_names_for_users[query.from_user.id][0][0]}\nДата создания: {session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][1]}\nСтатус: {'Активно🟢' if session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0] in user_threads else 'Не активно🔴'}",
                                                    reply_markup=reply_markup)
            elif len(session_names_for_users[query.from_user.id]) == 0:
                keyboard = [[InlineKeyboardButton("<<<", callback_data='Back to memefi')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.edit_message_text(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                                    text="У вас нет ни одной сессии, добавьте ее через кнопку «Добавить сессию»",
                                                    reply_markup=reply_markup)
            else:
                if name in user_threads:
                    keyboard = [

                        [InlineKeyboardButton("🚫 Остановить 🚫",
                                              callback_data=f"Stop session|{str(query.from_user.id) + '_' + name}|{int(query.data.split('|')[2])}")],
                        [InlineKeyboardButton("◀️",
                                              callback_data=f"Sessions|{query.from_user.id}|{int(query.data.split('|')[2]) - 1 if int(query.data.split('|')[2]) - 1 >= 0 else len(session_names_for_users[query.from_user.id]) - 1}"),
                         InlineKeyboardButton("▶️",
                                              callback_data=f"Sessions|{query.from_user.id}|{int(query.data.split('|')[2]) + 1 if len(session_names_for_users[query.from_user.id]) > int(query.data.split('|')[2]) + 1 else 0}")],
                        [InlineKeyboardButton("<<<", callback_data='Back to memefi')]]
                else:
                    keyboard = [

                        [InlineKeyboardButton("🚀 Запустить 🚀",
                                              callback_data=f"Start session|{session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0]}|{int(query.data.split('|')[2])}")],
                        [InlineKeyboardButton("🗑 Удалить 🗑",
                                              callback_data=f"Delete session|{session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0]}|{int(query.data.split('|')[2])}")],
                        [InlineKeyboardButton("◀️",
                                              callback_data=f"Sessions|{query.from_user.id}|{int(query.data.split('|')[2]) - 1 if int(query.data.split('|')[2]) - 1 >= 0 else len(session_names_for_users[query.from_user.id]) - 1}"),
                         InlineKeyboardButton("▶️",
                                              callback_data=f"Sessions|{query.from_user.id}|{int(query.data.split('|')[2]) + 1 if len(session_names_for_users[query.from_user.id]) > int(query.data.split('|')[2]) + 1 else 0}")],
                        [InlineKeyboardButton("<<<", callback_data='Back to memefi')]]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.edit_message_text(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                                    text=f"Сессия №{int(query.data.split('|')[2]) + 1}\n\nНазвание: {session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0]}\nДата создания: {session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][1]}\nСтатус: {'Активно🟢' if session_names_for_users[query.from_user.id][int(query.data.split('|')[2])][0] in user_threads else 'Не активно🔴'}",
                                                    reply_markup=reply_markup)
    elif query.data == 'Back to memefi':
        keyboard = [[InlineKeyboardButton("⏬ Добавить сессию ⏬", callback_data='Add session')],
                    [InlineKeyboardButton("🗒 Мои сессии 🗒", callback_data=f"Sessions|{query.from_user.id}|0")]]
        user_threads = load(f"sessions/{query.from_user.id}/threads.json")
        if query.from_user.id in session_names_for_users.keys() and len(session_names_for_users[
                                                                            query.from_user.id]) >= 1 and user_threads == []:
            keyboard.append([InlineKeyboardButton("🚀 Запустить все сессии 🚀", callback_data='start all')])
        keyboard.append([InlineKeyboardButton("<<<", callback_data='Back to menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.edit_message_text(
            text="Наш бот поможет вам автоматизировать игру в MemeFi, собирать монеты и покупать улучшения. Важно: наш бот не имеет доступа к личным данным пользователя",
            chat_id=query.message.chat.id, message_id=query.message.message_id, reply_markup=reply_markup)
        users[query.from_user.id] = ''

    elif query.data == 'Back to menu':
        keyboard = [[InlineKeyboardButton("Blum", callback_data='Blum')],
                    [InlineKeyboardButton("Memefi", callback_data='Memefi')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.edit_message_text(
            text="Выберете проект для запуска бота. Имейте ввиду что наш бот не имеет доступа к вашим личным данным.",
            chat_id=query.message.chat.id, message_id=query.message.message_id,
            parse_mode='Markdown', reply_markup=reply_markup)
    elif query.data == 'Bearer':
        users[query.from_user.id] = 'collect bearer token'
        await context.bot.send_message(chat_id=update.callback_query.message.chat.id,
                                       text='Присылай мне свой Bearer Token, и я за тебя сыграю!')
        await context.bot.edit_message_reply_markup(chat_id=update.callback_query.message.chat.id,
                                                    message_id=update.callback_query.message.message_id,
                                                    reply_markup=None)
    elif query.data == 'Telegram API':
        await context.bot.send_message(chat_id=update.callback_query.message.chat.id,
                                       text='Telegram API Token пока что находится в разработке')
    elif query.data == 'Tutorial':
        await context.bot.send_video(chat_id=update.callback_query.message.chat.id, video='',
                                     caption='⚠️Токен меняется каждый час!⚠️')
    elif query.data.split('|')[0] == 'cancel':
        users[query.from_user.id] = ''
        memefi_users[query.from_user.id] = {'api_id': '', 'api_hash': '', 'phone_number': '', 'code': ''}
        users_current_session_name[query.from_user.id] = ''
        sessions_users[query.from_user.id], users_phone_code_hash[
            query.from_user.id] = '', ''
        keyboard = [[InlineKeyboardButton("⏬ Добавить сессию ⏬", callback_data='Add session')],
                    [InlineKeyboardButton("🗒 Мои сессии 🗒", callback_data=f"Sessions|{query.from_user.id}|0")]]
        user_threads = load(f"sessions/{query.from_user.id}/threads.json")
        if query.from_user.id in session_names_for_users.keys() and len(session_names_for_users[
                                                                            query.from_user.id]) >= 1 and user_threads == []:
            keyboard.append([InlineKeyboardButton("🚀 Запустить все сессии 🚀", callback_data='start all')])
        keyboard.append([InlineKeyboardButton("<<<", callback_data='Back to menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.edit_message_text(
            text="Наш бот поможет вам автоматизировать игру в MemeFi, собирать монеты и покупать улучшения. Важно: наш бот не имеет доступа к личным данным пользователя",
            chat_id=query.message.chat.id, message_id=query.message.message_id, reply_markup=reply_markup)
    await query.answer()


async def sleep_time(context: ContextTypes.DEFAULT_TYPE) -> None:
    global users
    job = context.job
    if job.data[2] == 5:
        count = job.data[1]
        token = job.data[0]
        chat_id = job.data[3]
        total_point = 0
        for i in range(count):
            head = {
                'Authorization': 'Bearer' + token,
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
            }
            post_id = req.post('https://game-domain.blum.codes/api/v1/game/play', headers=head)
            id = json.loads(post_id.text)['gameId']
            await asyncio.sleep(random.randrange(30, 60, step=5))
            points = random.randint(150, 230)
            endGame = req.post('https://game-domain.blum.codes/api/v1/game/claim', headers=head, json={
                "gameId": id, "points": points})
            await context.bot.send_message(chat_id=chat_id, text=str(
                "Токен " + str(job.data[-1]) + ": Сыграл уже " + str(i + 1) + " игру из " + str(
                    count) + ', получил ' + str(points) + ' очков!'))
            await asyncio.sleep(random.randrange(1, 5))
            total_point += points
        await context.bot.send_message(chat_id=chat_id,
                                       text=f"Всего получено поинтов для токина {job.data[-1]} : {total_point}")



async def handle_private_messages(update: Update, context: CallbackContext):
    if update.message.from_user.id in users.keys():
        if users[update.message.from_user.id] == 'collect bearer token':
            text = update.message.text.replace(' ', '')
            count_tokens = 0
            for t in set(text.split(',')):
                count_tokens += 1
                token = t
                users[update.message.from_user.id] = 0
                head = {
                    'Authorization': 'Bearer' + token,
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
                }
                try:
                    resp = req.get('https://game-domain.blum.codes/api/v1/user/balance', headers=head)
                    count = json.loads(resp.text)['playPasses']
                    if count != 0:
                        await context.bot.send_message(chat_id=update.effective_chat.id,
                                                       text=f"Осталось билетов для Токена {count_tokens}: {count}\n\nНачинаю играть...")

                        try:
                            context.job_queue.run_once(sleep_time, 1, chat_id=update.message.from_user.id,
                                                       data=[token, count, 5, update.message.from_user.id,
                                                             count_tokens])
                        except Exception as e:
                            print(e)
                    else:
                        await context.bot.send_message(chat_id=update.effective_chat.id,
                                                       text=f"Упс! У тебя не осталось билетов")
                except Exception as e:
                    await context.bot.send_message(chat_id=update.effective_chat.id,
                                                   text=f"Токен {count_tokens} - ошибка: Неверный Токен")
                    users[update.message.from_user.id] = 1
                    print(e)
        elif users[update.message.from_user.id] == 'collect session name':
            text = update.message.text.replace('/', '')
            text = text.replace('|', '')
            try:
                if len(text) >= 200:
                    await context.bot.send_message(update.effective_chat.id,
                                                   text='Название сессии должно быть меньше, чем 200 символов')

                elif update.effective_chat.id not in session_names_for_users.keys():
                    memefi_users[update.effective_chat.id] = {'api_id': '', 'api_hash': '', 'phone_number': '',
                                                                 'code': ''}
                    users_current_session_name[update.effective_chat.id] = text
                    keyboard = [[InlineKeyboardButton("❌ Отменить ❌", callback_data=f'cancel|{text}')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    try:
                        if not os.path.exists(f"sessions/{update.message.chat_id}"):
                            os.mkdir(f"sessions/{update.message.chat_id}")
                        else:
                            ...
                        await context.bot.send_message(
                            text="Отправьте Telegram API ID для сессии",
                            chat_id=update.message.chat.id, reply_markup=reply_markup)
                        users[update.effective_chat.id] = 'collect tg api id'
                    except:
                        await context.bot.send_message(text="Не получается создать сессию, где-то ошибка(",
                                                       chat_id=update.message.chat.id)
                        users[update.effective_chat.id] = ''

                elif update.effective_chat.id in session_names_for_users.keys():
                    if text in [item[0] for item in
                                               session_names_for_users[update.message.from_user.id]]:
                        await context.bot.send_message(chat_id=update.effective_chat.id,
                                                       text='Сессия с таким именем уже существует')
                    else:
                        users_current_session_name[update.effective_chat.id] = text
                        keyboard = [[InlineKeyboardButton("❌ Отменить ❌", callback_data=f'cancel|{text}')]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await context.bot.send_message(
                                text="Отправьте Telegram API ID для сессии",
                                chat_id=update.effective_chat.id, reply_markup=reply_markup)
                        users[update.effective_chat.id] = 'collect tg api id'

            except:
                await context.bot.send_message(update.message.chat_id,
                                               text=f"Ошибка возникла(\n Проверьте правильность вводимых данных и попробуйте еще раз")
                memefi_users[update.effective_chat.id] = {'api_id': '', 'api_hash': '', 'phone_number': '',
                                                             'code': ''}
                return 0

        elif users[update.effective_chat.id] == 'collect tg api id':
            try:
                api_id = update.message.text
                memefi_users[update.effective_chat.id]['api_id'] = api_id
                keyboard = [[InlineKeyboardButton("❌ Отменить ❌", callback_data=f'cancel|{update.message.text}')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(
                    text="Отправьте Telegram API HASH для сессии",
                    chat_id=update.message.chat.id, reply_markup=reply_markup)
                users[update.effective_chat.id] = 'collect tg api hash'
            except:
                await context.bot.send_message(update.message.chat_id,
                                               text=f"Ошибка возникла(\n Проверьте правильность вводимых данных и попробуйте еще раз")
                memefi_users[update.effective_chat.id]['api_id'] = ''
                users[update.effective_chat.id] = ''
        elif users[update.effective_chat.id] == 'collect tg api hash':
            try:
                api_hash = update.message.text
                memefi_users[update.effective_chat.id]['api_hash'] = api_hash
                keyboard = [[InlineKeyboardButton("❌ Отменить ❌", callback_data=f'cancel|{update.message.text}')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(
                    text="Отправьте номер телефона в формате 38ххххххххххх",
                    chat_id=update.message.chat.id, reply_markup=reply_markup)
                users[update.effective_chat.id] = 'collect phone_number'
            except:
                await context.bot.send_message(update.message.chat_id,
                                               text=f"Ошибка возникла(\n Проверьте правильность вводимых данных и попробуйте еще раз")
                memefi_users[update.effective_chat.id]['api_hash'] = ''
                users[update.effective_chat.id] = 'collect phone_number'
        elif users[update.effective_chat.id] == 'collect phone_number':
            phone_number = update.message.text
            memefi_users[update.effective_chat.id]['phone_number'] = phone_number
            if update.effective_chat.id in session_names_for_users.keys():
                phones = []
                for entries in session_names_for_users.values():
                    phones.extend(entry[4] for entry in entries)

                if phone_number in phones:
                    await context.bot.send_message(
                        text="Номер уже зарегестрирован в боте",
                        chat_id=update.effective_chat.id)
                    return 0

            await context.bot.send_message(
                text="Теперь отправьте мне пароль для сессии\n\nПри добавлении сессии без пароля, просто отправьте \'---\'",
                chat_id=update.effective_chat.id)
            users[update.effective_chat.id] = 'collect password'

        elif users[update.effective_chat.id] == 'collect password':
            text = update.message.text
            memefi_users[update.effective_chat.id]['password'] = text if text != '---' else ''
            try:
                API_ID = int(memefi_users[update.effective_chat.id]['api_id'])
                API_HASH = memefi_users[update.effective_chat.id]['api_hash']
                PHONE_NUMBER = memefi_users[update.effective_chat.id]['phone_number']

                session_name = users_current_session_name[update.effective_chat.id]
            except:

                await context.bot.send_message(update.message.chat_id,
                                               text=f"Ошибка возникла(\n Проверьте правильность вводимых данных и попробуйте еще раз")
                memefi_users[update.effective_chat.id]['phone_number'] = ''
                return 0
            try:
                session = Client(
                    name=session_name,
                    api_id=API_ID,
                    api_hash=API_HASH,
                    workdir=f"sessions/{update.message.chat_id}/"
                )

                await session.connect()
                sent_code_info = await session.send_code(PHONE_NUMBER)
                sessions_users[update.effective_chat.id], users_phone_code_hash[
                    update.effective_chat.id] = session, sent_code_info.phone_code_hash
                await context.bot.send_message(
                    text="Теперь отправьте мне код от телеграма, который только что пришел на аккаунт добавляемой сессии\n\n(При добавлении сессии своего аккаунта, напишите код в виде суммы)\nНапример: \n43000+385\n56328-1",
                    chat_id=update.effective_chat.id)
                users[update.effective_chat.id] = 'collect code'

            except Exception as e:
                await session.disconnect()
                os.remove(f"sessions/{update.message.chat_id}/" + session_name + ".session")
                sessions_users[update.effective_chat.id], users_phone_code_hash[
                    update.effective_chat.id] = None, None

                await context.bot.send_message(update.message.chat_id,
                                               text=f"Ошибка возникла:\n{e}\n\nПроверь правильность вводимых данных и попробуй еще раз")
                users[update.effective_chat.id] = ''


        elif users[update.effective_chat.id] == 'collect code':
            try:
                code = str(eval(update.message.text))
                phone = memefi_users[update.effective_chat.id]['phone_number']
                phone_hash = users_phone_code_hash[update.effective_chat.id]
                name = users_current_session_name[update.effective_chat.id]
                password = memefi_users[update.effective_chat.id]['password']
                memefi_users[update.effective_chat.id]['code'] = code

                session_user = sessions_users[update.effective_chat.id]
            except:
                await context.bot.send_message(update.message.chat_id,
                                               text=f"Ошибка возникла(\n Проверьте правильность вводимых данных и попробуйте еще раз")
                return 0

            try:
                try:
                    await session_user.sign_in(phone_number=phone, phone_code_hash=phone_hash, phone_code=code)
                except errors.exceptions.unauthorized_401.SessionPasswordNeeded:
                    await session_user.check_password(password=password)
            except Exception as e:
                await session_user.disconnect()
                os.remove(f"sessions/{update.message.chat_id}/" + name + ".session")
                await context.bot.send_message(update.message.chat_id,
                                               text=f"Ошибка возникла:\n{e}\n\nПроверьте правильность вводимых данных и попробуйте еще раз")
                return 0
            if update.effective_chat.id not in session_names_for_users.keys():
                session_names_for_users[update.effective_chat.id] = [
                    [users_current_session_name[update.effective_chat.id], datetime.datetime.today().ctime(),
                     int(memefi_users[update.effective_chat.id]['api_id']),
                     memefi_users[update.effective_chat.id]['api_hash'], memefi_users[update.effective_chat.id]['phone_number']], memefi_users[update.effective_chat.id]['password']]
                session_names_for_users_upload = {}
                for key, value in session_names_for_users.items():
                    session_names_for_users_upload[str(key)] = value
                save_sessions(session_names_for_users_upload, update.effective_chat.id)
            else:
                session_names_for_users[update.effective_chat.id].append(
                    [users_current_session_name[update.effective_chat.id], datetime.datetime.today().ctime(),
                     int(memefi_users[update.effective_chat.id]['api_id']),
                     memefi_users[update.effective_chat.id]['api_hash'], memefi_users[update.effective_chat.id]['phone_number'], memefi_users[update.effective_chat.id]['password']])
                session_names_for_users_upload = {}
                for key, value in session_names_for_users.items():
                    session_names_for_users_upload[str(key)] = value
                save_sessions(session_names_for_users_upload, update.effective_chat.id)
            await session_user.disconnect()

            keyboard = [[InlineKeyboardButton("⏬ Добавить сессию ⏬", callback_data='Add session')],
                        [InlineKeyboardButton("🗒 Мои сессии 🗒", callback_data=f"Sessions|{update.effective_chat.id}|0")]]
            user_threads = load(f"sessions/{update.effective_chat.id}/threads.json")
            if update.effective_chat.id in session_names_for_users.keys() and len(session_names_for_users[
                                                                                update.effective_chat.id]) >= 1 and user_threads == []:
                keyboard.append([InlineKeyboardButton("🚀 Запустить все сессии 🚀", callback_data='start all')])
            keyboard.append([InlineKeyboardButton("<<<", callback_data='Back to menu')])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                text=f"Сессия {users_current_session_name[update.effective_chat.id]} успешно добавлена",
                chat_id=update.message.chat.id, reply_markup=reply_markup)


            users[update.effective_chat.id] = ''


async def add(update: Update, context: CallbackContext):
    if len(context.args) > 0:
        user_id = int(context.args[0])
        whitelist.add(user_id)
        save_whitelist(whitelist, 'whitelist.json')
        await update.message.reply_text(f'Юзер {user_id} был успешно добавлен в белый список')
    else:
        await update.message.reply_text('Ошибка. Предоставь валидный id')



api_token = API_TOKEN
application = Application.builder().token(api_token).build()

application.add_handler(CommandHandler("start", start, filters=filters.ChatType.PRIVATE))
application.add_handler(CommandHandler("add", add, filters=filters.Chat(chat_id=[1234567890])))
application.add_handler(MessageHandler(filters.ChatType.PRIVATE, handle_private_messages))
application.add_handler(CallbackQueryHandler(button))
application.run_polling()
