import html
import re
from datetime import datetime
from typing import List
import wikipedia
import random
from telegram import ChatAction
from gtts import gTTS
import time
from tswift import Song
from telegram import ChatAction
from feedparser import parse
import json
import urllib.request
import urllib.parse
import requests
from Megumi import (DEV_USERS, OWNER_ID, SUDO_USERS,MESSAGE_DUMP, SUPPORT_USERS,
                          TIGER_USERS, WHITELIST_USERS, TIME_API_KEY, dispatcher, updater)
from Megumi.__main__ import STATS, TOKEN, USER_INFO
from Megumi.modules.disable import DisableAbleCommandHandler
from Megumi.modules.helper_funcs.filters import CustomFilters
from Megumi.modules.helper_funcs.chat_status import sudo_plus, user_admin
from Megumi.modules.helper_funcs.extraction import extract_user
from telegram import MessageEntity, ParseMode, Update, constants
from telegram.error import BadRequest
from emoji import UNICODE_EMOJI
from googletrans import LANGUAGES, Translator
from Megumi.modules.helper_funcs.alternate import typing_action
from Megumi.modules.sql import rss_sql as sql
from Megumi.modules.sql import afk_sql as asql
from Megumi.modules.sql import users_sql as usql
from wikipedia.exceptions import DisambiguationError, PageError
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html

MARKDOWN_HELP = f"""
Markdown is a very powerful formatting tool supported by telegram. {dispatcher.bot.first_name} has some enhancements, to make sure that \
saved messages are correctly parsed, and to allow you to create buttons.

• <code>_italic_</code>*:* wrapping text with '_' will produce italic text
• <code>*bold*</code>*:* wrapping text with '*' will produce bold text
• <code>`code`</code>*:* wrapping text with '`' will produce monospaced text, also known as 'code'
• <code>[sometext](someURL)</code>*:* this will create a link - the message will just show <code>sometext</code>, \
and tapping on it will open the page at <code>someURL</code>.
<b>Example:</b>Example:<b>Example:</b> <code>[test](example.com)</code>

• <code>[buttontext](buttonurl:someURL)</code>*:* this is a special enhancement to allow users to have telegram \
buttons in their markdown. <code>buttontext</code> will be what is displayed on the button, and <code>someurl</code> \
will be the url which is opened.
<b>Example:</b> <code>[This is a button](buttonurl:example.com)</code>

If you want multiple buttons on the same line, use :same, as such:
<code>[one](buttonurl://example.com)
[two](buttonurl://google.com:same)</code>
This will create two buttons on a single line, instead of one button per line.

Keep in mind that your message <b>MUST</b> contain some text other than just a button!
"""

normiefont = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
]
weebyfont = [
    '卂', '乃', '匚', '刀', '乇', '下', '厶', '卄', '工', '丁', '长', '乚', '从', '𠘨', '口',
    '尸', '㔿', '尺', '丂', '丅', '凵', 'リ', '山', '乂', '丫', '乙'
]

@run_async
def feedback(update: Update, context:CallbackContext):
  bot = context.bot
  name = update.effective_message.from_user.first_name
  message = update.effective_message
  userid=message.from_user.id
  text = message.text[len('/feedback '):]
   

  feed_text = f"Megumi's *New* feedback from [{name}](tg://user?id={userid})\n\nfeed: {text}"
  

  bot.send_message(MESSAGE_DUMP, feed_text, parse_mode=ParseMode.MARKDOWN)
 
  text = html.escape(text)
  reply_text=f"Thankyou for giving us your feedback."
  message.reply_text(reply_text) 

@run_async
def tts(update: Update, context: CallbackContext):
    args = context.args
    current_time = datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M:%S")
    filename = datetime.now().strftime("%d%m%y-%H%M%S%f")
    reply = " ".join(args)
    update.message.chat.send_action(ChatAction.RECORD_AUDIO)
    lang="ml"
    tts = gTTS(reply, lang)
    tts.save("k.mp3")
    with open("k.mp3", "rb") as f:
        linelist = list(f)
        linecount = len(linelist)
    if linecount == 1:
        update.message.chat.send_action(ChatAction.RECORD_AUDIO)
        lang = "en"
        tts = gTTS(reply, lang)
        tts.save("k.mp3")
    with open("k.mp3", "rb") as speech:
        update.message.reply_voice(speech, quote=False)

@run_async
def paste(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message

    if message.reply_to_message:
        data = message.reply_to_message.text

    elif len(args) >= 1:
        data = message.text.split(None, 1)[1]

    else:
        message.reply_text("What am I supposed to do with this?")
        return

    key = requests.post(
        'https://nekobin.com/api/documents', json={
            "content": data
        }).json().get('result').get('key')

    url = f'https://nekobin.com/{key}'

    reply_text = f'Nekofied to *Nekobin* : {url}'

    message.reply_text(
        reply_text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True)

@run_async
def totranslate(update: Update, context: CallbackContext):
    msg = update.effective_message
    problem_lang_code = []
    for key in LANGUAGES:
        if "-" in key:
            problem_lang_code.append(key)
    try:
        if msg.reply_to_message:
            args = update.effective_message.text.split(None, 1)
            if msg.reply_to_message.text:
                text = msg.reply_to_message.text
            elif msg.reply_to_message.caption:
                text = msg.reply_to_message.caption

            message = update.effective_message
            dest_lang = None

            try:
                source_lang = args[1].split(None, 1)[0]
            except:
                source_lang = "en"

            if source_lang.count('-') == 2:
                for lang in problem_lang_code:
                    if lang in source_lang:
                        if source_lang.startswith(lang):
                            dest_lang = source_lang.rsplit("-", 1)[1]
                            source_lang = source_lang.rsplit("-", 1)[0]
                        else:
                            dest_lang = source_lang.split("-", 1)[1]
                            source_lang = source_lang.split("-", 1)[0]
            elif source_lang.count('-') == 1:
                for lang in problem_lang_code:
                    if lang in source_lang:
                        dest_lang = source_lang
                        source_lang = None
                        break
                if dest_lang is None:
                    dest_lang = source_lang.split("-")[1]
                    source_lang = source_lang.split("-")[0]
            else:
                dest_lang = source_lang
                source_lang = None

            exclude_list = UNICODE_EMOJI.keys()
            for emoji in exclude_list:
                if emoji in text:
                    text = text.replace(emoji, '')

            trl = Translator()
            if source_lang is None:
                detection = trl.detect(text)
                tekstr = trl.translate(text, dest=dest_lang)
                return message.reply_text(
                    f"Translated from `{detection.lang}` to `{dest_lang}`:\n`{tekstr.text}`",
                    parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(text, dest=dest_lang, src=source_lang)
                message.reply_text(
                    f"Translated from `{source_lang}` to `{dest_lang}`:\n`{tekstr.text}`",
                    parse_mode=ParseMode.MARKDOWN)
        else:
            args = update.effective_message.text.split(None, 2)
            message = update.effective_message
            source_lang = args[1]
            text = args[2]
            exclude_list = UNICODE_EMOJI.keys()
            for emoji in exclude_list:
                if emoji in text:
                    text = text.replace(emoji, '')
            dest_lang = None
            temp_source_lang = source_lang
            if temp_source_lang.count('-') == 2:
                for lang in problem_lang_code:
                    if lang in temp_source_lang:
                        if temp_source_lang.startswith(lang):
                            dest_lang = temp_source_lang.rsplit("-", 1)[1]
                            source_lang = temp_source_lang.rsplit("-", 1)[0]
                        else:
                            dest_lang = temp_source_lang.split("-", 1)[1]
                            source_lang = temp_source_lang.split("-", 1)[0]
            elif temp_source_lang.count('-') == 1:
                for lang in problem_lang_code:
                    if lang in temp_source_lang:
                        dest_lang = None
                        break
                    else:
                        dest_lang = temp_source_lang.split("-")[1]
                        source_lang = temp_source_lang.split("-")[0]
            trl = Translator()
            if dest_lang is None:
                detection = trl.detect(text)
                tekstr = trl.translate(text, dest=source_lang)
                return message.reply_text(
                    "Translated from `{}` to `{}`:\n`{}`".format(
                        detection.lang, source_lang, tekstr.text),
                    parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(text, dest=dest_lang, src=source_lang)
                message.reply_text(
                    "Translated from `{}` to `{}`:\n`{}`".format(
                        source_lang, dest_lang, tekstr.text),
                    parse_mode=ParseMode.MARKDOWN)

    except IndexError:
        update.effective_message.reply_text(
            "Reply to messages or write messages from other languages ​​for translating into the intended language\n\n"
            "Example: `/tr en-ml` to translate from English to Malayalam\n"
            "Or use: `/tr ml` for automatic detection and translating it into Malayalam.\n",
            parse_mode="markdown",
            disable_web_page_preview=True)
    except ValueError:
        update.effective_message.reply_text(
            "The intended language is not found!")
    else:
        return

def show_url(update: Update, context: CallbackContext):
    tg_chat_id = str(update.effective_chat.id)
    bot = context.bot
    args = context.args
    if len(args) >= 1:
        tg_feed_link = args[0]
        link_processed = parse(tg_feed_link)

        if link_processed.bozo == 0:
            feed_title = link_processed.feed.get("title", default="Unknown")
            feed_description = "<i>{}</i>".format(
                re.sub(
                    '<[^<]+?>', '',
                    link_processed.feed.get("description", default="Unknown")))
            feed_link = link_processed.feed.get("link", default="Unknown")

            feed_message = "<b>Feed Title:</b> \n{}" \
                           "\n\n<b>Feed Description:</b> \n{}" \
                           "\n\n<b>Feed Link:</b> \n{}".format(html.escape(feed_title),
                                                               feed_description,
                                                               html.escape(feed_link))

            if len(link_processed.entries) >= 1:
                entry_title = link_processed.entries[0].get(
                    "title", default="Unknown")
                entry_description = "<i>{}</i>".format(
                    re.sub(
                        '<[^<]+?>', '', link_processed.entries[0].get(
                            "description", default="Unknown")))
                entry_link = link_processed.entries[0].get(
                    "link", default="Unknown")

                entry_message = "\n\n<b>Entry Title:</b> \n{}" \
                                "\n\n<b>Entry Description:</b> \n{}" \
                                "\n\n<b>Entry Link:</b> \n{}".format(html.escape(entry_title),
                                                                     entry_description,
                                                                     html.escape(entry_link))
                final_message = feed_message + entry_message

                bot.send_message(
                    chat_id=tg_chat_id,
                    text=final_message,
                    parse_mode=ParseMode.HTML)
            else:
                bot.send_message(
                    chat_id=tg_chat_id,
                    text=feed_message,
                    parse_mode=ParseMode.HTML)
        else:
            update.effective_message.reply_text(
                "This link is not an RSS Feed link")
    else:
        update.effective_message.reply_text("URL missing")

def generate_time(to_find: str, findtype: List[str]) -> str:
    data = requests.get(
        f"https://api.timezonedb.com/v2.1/list-time-zone"
        f"?key={TIME_API_KEY}"
        f"&format=json"
        f"&fields=countryCode,countryName,zoneName,gmtOffset,timestamp,dst"
    ).json()

    for zone in data["zones"]:
        for eachtype in findtype:
            if to_find in zone[eachtype].lower():
                country_name = zone['countryName']
                country_zone = zone['zoneName']
                country_code = zone['countryCode']

                if zone['dst'] == 1:
                    daylight_saving = "Yes"
                else:
                    daylight_saving = "No"

                date_fmt = r"%d-%m-%Y"
                time_fmt = r"%H:%M:%S"
                day_fmt = r"%A"
                gmt_offset = zone['gmtOffset']
                timestamp = datetime.datetime.now(
                    datetime.timezone.utc) + datetime.timedelta(
                        seconds=gmt_offset)
                current_date = timestamp.strftime(date_fmt)
                current_time = timestamp.strftime(time_fmt)
                current_day = timestamp.strftime(day_fmt)

                break

    try:
        result = (
            f'<b>Country:</b> <code>{country_name}</code>\n'
            f'<b>Zone Name:</b> <code>{country_zone}</code>\n'
            f'<b>Country Code:</b> <code>{country_code}</code>\n'
            f'<b>Daylight saving:</b> <code>{daylight_saving}</code>\n'
            f'<b>Day:</b> <code>{current_day}</code>\n'
            f'<b>Current Time:</b> <code>{current_time}</code>\n'
            f'<b>Current Date:</b> <code>{current_date}</code>\n'
            '<b>Timezones:</b> <a href="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones">List here</a>'
        )
    except:
        result = None

    return result

@run_async
@typing_action
def lyrics(update: Update, context:CallbackContext):
    msg = update.effective_message
    args = context.args
    query = " ".join(args)
    song = ""
    if not query:
        msg.reply_text("You haven't specified which song to look for!")
        return
    else:
        song = Song.find_song(query)
        if song:
            if song.lyrics:
                reply = song.format()
            else:
                reply = "Couldn't find any lyrics for that song!"
        else:
            reply = "Song not found!"
        if len(reply) > 4090:
            with open("lyrics.txt", 'w') as f:
                f.write(f"{reply}\n\n\nOwO UwU OmO")
            with open("lyrics.txt", 'rb') as f:
                msg.reply_document(document=f,
                caption="Message length exceeded max limit! Sending as a text file.")
        else:
            msg.reply_text(reply)

@run_async
def gettime(update: Update, context: CallbackContext):
    message = update.effective_message

    try:
        query = message.text.strip().split(" ", 1)[1]
    except:
        message.reply_text(
            "Provide a country name/abbreviation/timezone to find.")
        return
    send_message = message.reply_text(
        f"Finding timezone info for <b>{query}</b>", parse_mode=ParseMode.HTML)

    query_timezone = query.lower()
    if len(query_timezone) == 2:
        result = generate_time(query_timezone, ["countryCode"])
    else:
        result = generate_time(query_timezone, ["zoneName", "countryName"])

    if not result:
        send_message.edit_text(
            f'Timezone info not available for <b>{query}</b>\n'
            '<b>All Timezones:</b> <a href="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones">List here</a>',
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True)
        return

    send_message.edit_text(
        result, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

def list_urls(update: Update, context: CallbackContext):
    tg_chat_id = str(update.effective_chat.id)
    bot = context.bot
    user_data = sql.get_urls(tg_chat_id)

    # this loops gets every link from the DB based on the filter above and appends it to the list
    links_list = [row.feed_link for row in user_data]

    final_content = "\n\n".join(links_list)

    # check if the length of the message is too long to be posted in 1 chat bubble
    if len(final_content) == 0:
        bot.send_message(
            chat_id=tg_chat_id, text="This chat is not subscribed to any links")
    elif len(final_content) <= constants.MAX_MESSAGE_LENGTH:
        bot.send_message(
            chat_id=tg_chat_id,
            text="This chat is subscribed to the following links:\n" +
            final_content)
    else:
        bot.send_message(
            chat_id=tg_chat_id,
            parse_mode=ParseMode.HTML,
            text="<b>Warning:</b> The message is too long to be sent")


@user_admin
def add_url(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if len(args) >= 1:
        chat = update.effective_chat
        tg_chat_id = str(update.effective_chat.id)

        tg_feed_link = args[0]

        link_processed = parse(tg_feed_link)

        # check if link is a valid RSS Feed link
        if link_processed.bozo == 0:
            if len(link_processed.entries[0]) >= 1:
                tg_old_entry_link = link_processed.entries[0].link
            else:
                tg_old_entry_link = ""

            # gather the row which contains exactly that telegram group ID and link for later comparison
            row = sql.check_url_availability(tg_chat_id, tg_feed_link)

            # check if there's an entry already added to DB by the same user in the same group with the same link
            if row:
                update.effective_message.reply_text(
                    "This URL has already been added")
            else:
                sql.add_url(tg_chat_id, tg_feed_link, tg_old_entry_link)

                update.effective_message.reply_text("Added URL to subscription")
        else:
            update.effective_message.reply_text(
                "This link is not an RSS Feed link")
    else:
        update.effective_message.reply_text("URL missing")


@user_admin
def remove_url(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if len(args) >= 1:
        tg_chat_id = str(update.effective_chat.id)

        tg_feed_link = args[0]

        link_processed = parse(tg_feed_link)

        if link_processed.bozo == 0:
            user_data = sql.check_url_availability(tg_chat_id, tg_feed_link)

            if user_data:
                sql.remove_url(tg_chat_id, tg_feed_link)

                update.effective_message.reply_text(
                    "Removed URL from subscription")
            else:
                update.effective_message.reply_text(
                    "You haven't subscribed to this URL yet")
        else:
            update.effective_message.reply_text(
                "This link is not an RSS Feed link")
    else:
        update.effective_message.reply_text("URL missing")


def rss_update(context: CallbackContext):
    user_data = sql.get_all()
    job = context.job
    bot = context.bot
    # this loop checks for every row in the DB
    for row in user_data:
        row_id = row.id
        tg_chat_id = row.chat_id
        tg_feed_link = row.feed_link

        feed_processed = parse(tg_feed_link)

        tg_old_entry_link = row.old_entry_link

        new_entry_links = []
        new_entry_titles = []

        # this loop checks for every entry from the RSS Feed link from the DB row
        for entry in feed_processed.entries:
            # check if there are any new updates to the RSS Feed from the old entry
            if entry.link != tg_old_entry_link:
                new_entry_links.append(entry.link)
                new_entry_titles.append(entry.title)
            else:
                break

        # check if there's any new entries queued from the last check
        if new_entry_links:
            sql.update_url(row_id, new_entry_links)
        else:
            pass

        if len(new_entry_links) < 5:
            # this loop sends every new update to each user from each group based on the DB entries
            for link, title in zip(
                    reversed(new_entry_links), reversed(new_entry_titles)):
                final_message = "<b>{}</b>\n\n{}".format(
                    html.escape(title), html.escape(link))

                if len(final_message) <= constants.MAX_MESSAGE_LENGTH:
                    bot.send_message(
                        chat_id=tg_chat_id,
                        text=final_message,
                        parse_mode=ParseMode.HTML)
                else:
                    bot.send_message(
                        chat_id=tg_chat_id,
                        text="<b>Warning:</b> The message is too long to be sent",
                        parse_mode=ParseMode.HTML)
        else:
            for link, title in zip(
                    reversed(new_entry_links[-5:]),
                    reversed(new_entry_titles[-5:])):
                final_message = "<b>{}</b>\n\n{}".format(
                    html.escape(title), html.escape(link))

                if len(final_message) <= constants.MAX_MESSAGE_LENGTH:
                    bot.send_message(
                        chat_id=tg_chat_id,
                        text=final_message,
                        parse_mode=ParseMode.HTML)
                else:
                    bot.send_message(
                        chat_id=tg_chat_id,
                        text="<b>Warning:</b> The message is too long to be sent",
                        parse_mode=ParseMode.HTML)

            bot.send_message(
                chat_id=tg_chat_id,
                parse_mode=ParseMode.HTML,
                text="<b>Warning: </b>{} occurrences have been left out to prevent spam"
                .format(len(new_entry_links) - 5))


def rss_set(context: CallbackContext):
    user_data = sql.get_all()
    bot, job = context.bot, context.job
    # this loop checks for every row in the DB
    for row in user_data:
        row_id = row.id
        tg_feed_link = row.feed_link
        tg_old_entry_link = row.old_entry_link

        feed_processed = parse(tg_feed_link)

        new_entry_links = []
        new_entry_titles = []

        # this loop checks for every entry from the RSS Feed link from the DB row
        for entry in feed_processed.entries:
            # check if there are any new updates to the RSS Feed from the old entry
            if entry.link != tg_old_entry_link:
                new_entry_links.append(entry.link)
                new_entry_titles.append(entry.title)
            else:
                break

        # check if there's any new entries queued from the last check
        if new_entry_links:
            sql.update_url(row_id, new_entry_links)
        else:
            pass

@run_async
def wiki(update: Update, context: CallbackContext):
    msg = update.effective_message.reply_to_message if update.effective_message.reply_to_message else update.effective_message
    res = ""
    if msg == update.effective_message:
        search = msg.text.split(" ", maxsplit=1)[1]
    else:
        search = msg.text
    try:
        res = wikipedia.summary(search)
    except DisambiguationError as e:
        update.message.reply_text(
            "Disambiguated pages found! Adjust your query accordingly.\n<i>{}</i>"
            .format(e),
            parse_mode=ParseMode.HTML)
    except PageError as e:
        update.message.reply_text(
            "<code>{}</code>".format(e), parse_mode=ParseMode.HTML)
    if res:
        result = f"<b>{search}</b>\n\n"
        result += f"<i>{res}</i>\n"
        result += f"""<a href="https://en.wikipedia.org/wiki/{search.replace(" ", "%20")}">Read more...</a>"""
        if len(result) > 4000:
            with open("result.txt", 'w') as f:
                f.write(f"{result}\n\nUwU OwO OmO UmU")
            with open("result.txt", 'rb') as f:
                context.bot.send_document(
                    document=f,
                    filename=f.name,
                    reply_to_message_id=update.message.message_id,
                    chat_id=update.effective_chat.id,
                    parse_mode=ParseMode.HTML)
        else:
            update.message.reply_text(
                result,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True)

@run_async
def weebify(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    string = ""

    if message.reply_to_message:
        string = message.reply_to_message.text.lower().replace(" ", "  ")

    if args:
        string = '  '.join(args).lower()

    if not string:
        message.reply_text(
            "Usage is `/weebify <text>`", parse_mode=ParseMode.MARKDOWN)
        return

    for normiecharacter in string:
        if normiecharacter in normiefont:
            weebycharacter = weebyfont[normiefont.index(normiecharacter)]
            string = string.replace(normiecharacter, weebycharacter)

    if message.reply_to_message:
        message.reply_to_message.reply_text(string)
    else:
        message.reply_text(string)

@run_async
def react(update: Update, context: CallbackContext):
    message = update.effective_message
    react = random.choice(reactions)
    if message.reply_to_message:
        message.reply_to_message.reply_text(react)
    else:
        message.reply_text(react)

@run_async
def pat(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat_id = update.effective_chat.id
    msg = str(update.message.text)
    try:
        msg = msg.split(" ", 1)[1]
    except IndexError:
        msg = ""
    msg_id = update.effective_message.reply_to_message.message_id if update.effective_message.reply_to_message else update.effective_message.message_id
    pats = []
    pats = json.loads(urllib.request.urlopen(urllib.request.Request(
    'http://headp.at/js/pats.json',
    headers={'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) '
         'Gecko/20071127 Firefox/2.0.0.11'}
    )).read().decode('utf-8'))
    if "@" in msg and len(msg) > 5:
        bot.send_photo(chat_id, f'https://headp.at/pats/{urllib.parse.quote(random.choice(pats))}', caption=msg)
    else:
        bot.send_photo(chat_id, f'https://headp.at/pats/{urllib.parse.quote(random.choice(pats))}', reply_to_message_id=msg_id)

@run_async
def snipe(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    try:
        chat_id = str(args[0])
        del args[0]
    except TypeError:
        update.effective_message.reply_text(
            "Please give me a chat to echo to!")
    to_send = " ".join(args)
    if len(to_send) >= 2:
        try:
            bot.sendMessage(int(chat_id), str(to_send))
        except TelegramError:
            LOGGER.warning("Couldn't send to group %s", str(chat_id))
            update.effective_message.reply_text(
                "Couldn't send the message. Perhaps I'm not part of that group?")

@run_async
def ud(update: Update, context: CallbackContext):
    message = update.effective_message
    text = message.text[len('/ud '):]
    results = requests.get(
        f'https://api.urbandictionary.com/v0/define?term={text}').json()
    try:
        reply_text = f'*{text}*\n\n{results["list"][0]["definition"]}\n\n_{results["list"][0]["example"]}_'
    except:
        reply_text = "No results found."
    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

@run_async
def get_id(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    msg = update.effective_message
    user_id = extract_user(msg, args)

    if user_id:

        if msg.reply_to_message and msg.reply_to_message.forward_from:

            user1 = message.reply_to_message.from_user
            user2 = message.reply_to_message.forward_from

            msg.reply_text(
                f"The original sender, {html.escape(user2.first_name)},"
                f" has an ID of <code>{user2.id}</code>.\n"
                f"The forwarder, {html.escape(user1.first_name)},"
                f" has an ID of <code>{user1.id}</code>.",
                parse_mode=ParseMode.HTML)

        else:
            user = bot.get_chat(user_id)
            msg.reply_text(
                f"{html.escape(user.first_name)}'s id is <code>{user.id}</code>.",
                parse_mode=ParseMode.HTML)

    else:

        if chat.type == "private":
            msg.reply_text(
                f"Your id is <code>{chat.id}</code>.",
                parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(
                f"This group's id is <code>{chat.id}</code>.",
                parse_mode=ParseMode.HTML)

@run_async
def gifid(update: Update, context: CallbackContext):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.animation:
        update.effective_message.reply_text(
            f"Gif ID:\n<code>{msg.reply_to_message.animation.file_id}</code>",
            parse_mode=ParseMode.HTML)
    else:
        update.effective_message.reply_text(
            "Please reply to a gif to get its ID.")


@run_async
@typing_action
@run_async
def info(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = extract_user(update.effective_message, args)

    if user_id:
        user = bot.get_chat(user_id)

    elif not message.reply_to_message and not args:
        user = message.from_user

    elif not message.reply_to_message and (not args or (
            len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not message.parse_entities(
        [MessageEntity.TEXT_MENTION]))):
        message.reply_text("I can't extract a user from this.")
        return

    else:
        return

    text = (f"<b>Characteristics:</b>\n"
            f"ID: <code>{user.id}</code>\n"
            f"First Name: {html.escape(user.first_name)}")

    if user.last_name:
        text += f"\nLast Name: {html.escape(user.last_name)}"

    if user.username:
        text += f"\nUsername: @{html.escape(user.username)}"

    text += f"\nPermanent user link: {mention_html(user.id, 'link')}"

    if user.id == OWNER_ID:
        text += "\nThis person is my owner - I would never do anything against them!."
        
    elif user.id in DEV_USERS:
        text += "\nThis person is my dev - I would never do anything against them!."
        
    elif user.id in SUDO_USERS:
        text += "\nThis person is one of my sudo users! " \
                    "Nearly as powerful as my owner - so watch it.."
        
    elif user.id in SUPPORT_USERS:
        text += "\nThis person is one of my support users! " \
                        "Not quite a sudo user, but can still gban you off the map."
       
    elif user.id in WHITELIST_USERS:
        text += "\nThis person has been whitelisted! " \
                        "That means I'm not allowed to ban/kick them."

    try:
        user_member = chat.get_member(user.id)
        if user_member.status == 'administrator':
            result = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={chat.id}&user_id={user.id}"
            )
            result = result.json()["result"]
            if "custom_title" in result.keys():
                custom_title = result['custom_title']
                text += f"\n\nThis user holds the title <b>{custom_title}</b> here."
    except BadRequest:
        pass

    for mod in USER_INFO:
        try:
            mod_info = mod.__user_info__(user.id).strip()
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    num_chats = usql.get_user_num_chats(user.id)
    if user_id == dispatcher.bot.id:    
            text += "\n\nI've seen them in... Wow. Are they stalking me? They're in all the same places I am... oh. It's me."
    else:
            text += f"\n\nI've seen them in <code>{num_chats}</code> groups."

    update.effective_message.reply_text(
        text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@run_async
@user_admin
def echo(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)
    message.delete()

@run_async
def markdown_help(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "Try forwarding the following message to me, and you'll see!")
    update.effective_message.reply_text(
        "/save test This is a markdown test. _italics_, *bold*, `code`, "
        "[URL](example.com) [button](buttonurl:github.com) "
        "[button2](buttonurl://google.com:same)")

@run_async
def stats(update: Update, context: CallbackContext):
    stats = "Current stats:\n" + "\n".join([mod.__stats__() for mod in STATS])
    result = re.sub(r'(\d+)', r'<code>\1</code>', stats)
    update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)

__help__ = """
 • `/id`*:* get the current group id. If used by replying to a message, gets that user's id.
 • `/gifid`*:* reply to a gif to me to tell you its file ID.
 • `/pat`*:* give a headpat :)
 • `/reverse`*:* Reverse searches image or stickers on google.
 • `/weebify <text>`*:* returns a weebified text.
 • `/ud <word>`*:* Type the word or expression you want to search use.
 • `/info`*:* get information about a user.
 • `/feedback`*:* You can give us your feedbacks 
 • `/paste`*:* Do a paste at `neko.bin`
 • `/wiki <query>`*:* wiki your query.
 • `/tts <your text>`*:* turns text to speech
 • `/markdownhelp`*:* quick summary of how markdown works in telegram - can only be called in private chats.
 • `/time <query>`*:* Gives information about a timezone.
 *Available queries:* Country Code/Country Name/Timezone Name
 • `/lyrics <song>`*:* returns the lyrics of that song. you can either enter just the song name or both the artist and song name.
 • `/tr` or `/tl` (language code) as reply to a long message.
*Example:* `/tr en`*:* translates something to english. 
`/tr hi-en`*:* translates hindi to english.
 \n*RSS Feed*\n
 • `/addrss <link>`*:* add an RSS link to the subscriptions.
 • `/removerss <link>`*:* removes the RSS link from the subscriptions.
 • `/rss <link>`*:* shows the link's data and the last entry, for testing purposes.
 • `/listrss`*:* shows the list of rss feeds that the chat is currently subscribed to.

*NOTE:* In groups, only admins can add/remove RSS links to the group's subscription

"""
job = updater.job_queue

job_rss_set = job.run_once(rss_set, 5)
job_rss_update = job.run_repeating(rss_update, interval=60, first=60)
job_rss_set.enabled = True
job_rss_update.enabled = True

SHOW_URL_HANDLER = CommandHandler("rss", show_url)
ADD_URL_HANDLER = CommandHandler("addrss", add_url)
REMOVE_URL_HANDLER = CommandHandler("removerss", remove_url)
LIST_URLS_HANDLER = CommandHandler("listrss", list_urls)
ID_HANDLER = DisableAbleCommandHandler("id", get_id)
TTS_HANDLER = DisableAbleCommandHandler("tts", tts, pass_args=True)
GIFID_HANDLER = DisableAbleCommandHandler("gifid", gifid)
INFO_HANDLER = DisableAbleCommandHandler(["info"], info)
UD_HANDLER = DisableAbleCommandHandler(["ud"], ud)
LYRICS_HANDLER = DisableAbleCommandHandler("lyrics", lyrics, pass_args=True)
TIME_HANDLER = DisableAbleCommandHandler("time", gettime)
TRANSLATE_HANDLER = DisableAbleCommandHandler(["tr", "tl"], totranslate)
PASTE_HANDLER = DisableAbleCommandHandler("paste", paste)

ECHO_HANDLER = DisableAbleCommandHandler("echo", echo, filters=Filters.group)
WEEBIFY_HANDLER = DisableAbleCommandHandler("weebify", weebify)
MD_HELP_HANDLER = CommandHandler(
    "markdownhelp", markdown_help, filters=Filters.private)
PAT_HANDLER = DisableAbleCommandHandler("pat", pat)
WIKI_HANDLER = DisableAbleCommandHandler("wiki", wiki)
FEED_HANDLER = DisableAbleCommandHandler("feedback", feedback)
SNIPE_HANDLER = CommandHandler(
    "snipe",
    snipe,
    pass_args=True,
    filters=CustomFilters.sudo_filter)
STATS_HANDLER = CommandHandler(
    "stats",
    stats,
    filters=Filters.user(SUDO_USERS))


dispatcher.add_handler(SNIPE_HANDLER)
dispatcher.add_handler(FEED_HANDLER)
dispatcher.add_handler(TRANSLATE_HANDLER)
dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(GIFID_HANDLER)
dispatcher.add_handler(WEEBIFY_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(PAT_HANDLER)
dispatcher.add_handler(TTS_HANDLER)
dispatcher.add_handler(UD_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(TIME_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(WIKI_HANDLER)
dispatcher.add_handler(PASTE_HANDLER)
dispatcher.add_handler(LYRICS_HANDLER)
dispatcher.add_handler(SHOW_URL_HANDLER)
dispatcher.add_handler(ADD_URL_HANDLER)
dispatcher.add_handler(REMOVE_URL_HANDLER)
dispatcher.add_handler(LIST_URLS_HANDLER)

__mod_name__ = "Misc"
__command_list__ = ["id", "info", "echo", "pat", "snipe", "weebify", "ud", 
"runs", "slap", "roll", "toss", "shrug", "bluetext", "rlg", "decide",
    "table", "react", "wiki","tr", "paste", "time","tr", "tl", "lyrics", "tts", "feedback"]
__handlers__ = [
    ID_HANDLER, GIFID_HANDLER, INFO_HANDLER, ECHO_HANDLER, MD_HELP_HANDLER,
    SNIPE_HANDLER, PAT_HANDLER, STATS_HANDLER, WEEBIFY_HANDLER, UD_HANDLER,
    WIKI_HANDLER, PASTE_HANDLER, TIME_HANDLER, TRANSLATE_HANDLER, LYRICS_HANDLER, TTS_HANDLER,
    FEED_HANDLER
]
