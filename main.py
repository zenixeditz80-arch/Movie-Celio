import telebot
import json
import os
import base64
import time
import threading

TOKEN = ""
ADMIN_ID = 8758830915

bot = telebot.TeleBot(TOKEN)

DB_FILE = "files.json"
USERS_DB_FILE = "users.json"

CHANNEL_USERNAME = "@"
CHANNEL_LINK = "https://t.me/"

if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            files_db = json.load(f)
    except:
        files_db = {}
else:
    files_db = {}

if os.path.exists(USERS_DB_FILE):
    try:
        with open(USERS_DB_FILE, "r", encoding="utf-8") as f:
            users_db = set(json.load(f))
    except:
        users_db = set()
else:
    users_db = set()

def save_db():
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(files_db, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"DB Save Error: {e}")

def save_users():
    try:
        with open(USERS_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(list(users_db), f, indent=4)
    except Exception as e:
        print(f"Users Save Error: {e}")

def normalize(text):
    return text.lower().replace(" ", "").replace("-", "").replace("_", "")

def encode_data(text):
    return base64.urlsafe_b64encode(text.encode()).decode()

def decode_data(text):
    return base64.urlsafe_b64decode(text.encode()).decode()

def is_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return False

def join_message(chat_id):
    bot.send_message(
        chat_id,
        f"""
❌ Please Join Channel First

📢 {CHANNEL_LINK}

ပြီးမှ Bot ကိုပြန်သုံးပါ။
"""
    )

def fast_send(chat_id, files):
    sent_count = 0

    try:
        for data in files:
            caption = data.get("caption", "")
            sent_msg = None

            if data["type"] == "document":
                sent_msg = bot.send_document(
                    chat_id,
                    data["file_id"],
                    caption=caption
                )

            elif data["type"] == "video":
                sent_msg = bot.send_video(
                    chat_id,
                    data["file_id"],
                    caption=caption,
                    supports_streaming=True
                )

            elif data["type"] == "audio":
                sent_msg = bot.send_audio(
                    chat_id,
                    data["file_id"],
                    caption=caption
                )

            elif data["type"] == "photo":
                sent_msg = bot.send_photo(
                    chat_id,
                    data["file_id"],
                    caption=caption
                )

            if sent_msg:
                auto_delete(
                    sent_msg.chat.id,
                    sent_msg.message_id,
                    300
                )

            sent_count += 1

        info_msg = bot.send_message(
            chat_id,
            f"""
✅ {sent_count} File Sent Successfully

🎥 Thank You For Using Our Movie Bot

❗️❗️❗️IMPORTANT❗️❗️❗️

ဤရုပ်ရှင်ဖိုင်များ / ဗီဒီယိုများ / ဓာတ်ပုံများကို
👉 5 👈 မိနစ်ကြာရင် 🫥
(မူပိုင်ခွင့်ပြဿနာများကြောင့်)
အလိုအလျောက် ဖျက်ပါမည်။

ကျေးဇူးပြု၍ ဤဖိုင်များအားလုံးကို
Saved Messages သို့ Forward လုပ်ထားပါ။
"""
        )

        auto_delete(
            info_msg.chat.id,
            info_msg.message_id,
            300
        )

    except Exception as e:
        print(f"Send Error: {e}")

@bot.message_handler(commands=['start'])
def start(message):

    user_id = message.from_user.id

    users_db.add(user_id)
    save_users()

    if not is_joined(user_id):
        join_message(message.chat.id)
        return

    args = message.text.split(maxsplit=1)

    if len(args) > 1:
        try:
            keyword = decode_data(args[1])
            keyword = normalize(keyword)

        except Exception:
            bot.send_message(
                message.chat.id,
                "❌ Invalid Link"
            )
            return

        matched_files = []

        for _, data in files_db.items():

            movie_name = normalize(
                data.get("name", "")
            )

            if keyword in movie_name or movie_name in keyword:
                matched_files.append(data)

        if matched_files:
            fast_send(
                message.chat.id,
                matched_files
            )
        else:
            bot.send_message(
                message.chat.id,
                "❌ Movie Not Found"
            )

        return

    bot.send_message(
        message.chat.id,
        f"""
🎬 Welcome To Movie Bot

📢 Join Our Channel
{CHANNEL_LINK}

🔎 Use Movie Links To Get Files Instantly.
"""
    )

@bot.message_handler(content_types=['document', 'video', 'audio', 'photo'])
def upload_file(message):

    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(
            message,
            "❌ Only admin can upload."
        )

    file_unique = str(message.message_id)
    caption_text = message.caption if message.caption else ""

    if message.document:
        file_id = message.document.file_id
        file_name = (
            message.caption
            if message.caption
            else message.document.file_name
        )
        file_type = "document"

    elif message.video:
        file_id = message.video.file_id
        file_name = (
            message.caption
            if message.caption
            else "MovieVideo"
        )
        file_type = "video"

    elif message.audio:
        file_id = message.audio.file_id
        file_name = (
            message.caption
            if message.caption
            else "MovieAudio"
        )
        file_type = "audio"

    elif message.photo:
        file_id = message.photo[-1].file_id
        file_name = (
            message.caption
            if message.caption
            else "MoviePhoto"
        )
        file_type = "photo"

    else:
        return

    files_db[file_unique] = {
        "file_id": file_id,
        "name": file_name,
        "type": file_type,
        "caption": caption_text
    }

    save_db()

    bot_username = bot.get_me().username

    movie_only = file_name

    if "ep" in movie_only.lower():
        movie_only = (
            movie_only.lower()
            .split("ep")[0]
            .strip()
        )

    encoded = encode_data(
        normalize(movie_only)
    )

    link = (
        f"https://t.me/"
        f"{bot_username}?start={encoded}"
    )

    bot.reply_to(
        message,
        f"""
✅ Movie Saved

🎬 {file_name}

🆔 {file_unique}
"""
    )

    bot.send_message(
        message.chat.id,
        f"🔗 Movie Link:\n{link}"
    )

def auto_delete(chat_id, message_id, delay=300):
    def delete():
        try:
            time.sleep(delay)
            bot.delete_message(chat_id, message_id)
        except:
            pass

    threading.Thread(target=delete, daemon=True).start()

@bot.message_handler(commands=['delete'])
def delete_file(message):
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    if len(args) < 2:
        return bot.reply_to(message, "Usage:\n/delete ID")

    file_key = args[1]

    if file_key not in files_db:
        return bot.reply_to(message, "❌ File not found.")

    del files_db[file_key]
    save_db()

    bot.reply_to(message, "✅ Deleted")

@bot.message_handler(commands=['deleteall'])
def delete_all(message):
    if message.from_user.id != ADMIN_ID:
        return

    files_db.clear()
    save_db()

    bot.reply_to(message, "✅ All Files Deleted.")

@bot.message_handler(commands=['delname'])
def delete_by_name(message):

    if message.from_user.id != ADMIN_ID:
        return

    movie_name = message.text.replace(
        "/delname",
        ""
    ).strip().lower()

    if not movie_name:
        return bot.reply_to(
            message,
            "Usage:\n/delname Movie name"
        )

    deleted = 0

    for file_id, data in list(files_db.items()):

        if movie_name in data.get(
            "name",
            ""
        ).lower():

            del files_db[file_id]
            deleted += 1

    save_db()

    if deleted:
        bot.reply_to(
            message,
            f"✅ Deleted {deleted} Files."
        )
    else:
        bot.reply_to(
            message,
            "❌ File not found."
        )

@bot.message_handler(commands=['backup'])
def backup_files(message):

    if message.from_user.id != ADMIN_ID:
        return

    try:
        backup_file = "backup.json"

        with open(
            backup_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                files_db,
                f,
                indent=4,
                ensure_ascii=False
            )

        with open(
            backup_file,
            "rb"
        ) as f:

            bot.send_document(
                message.chat.id,
                f,
                caption="📦 Backup Completed"
            )

        os.remove(backup_file)

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ Backup Failed\n\n{e}"
        )

@bot.message_handler(commands=['stats'])
def stats(message):

    if message.from_user.id != ADMIN_ID:
        return

    try:
        bot.send_message(
            message.chat.id,
            f"""
📊 Bot Statistics

👥 Total Users: {len(users_db)}
🎬 Total Files: {len(files_db)}
"""
        )

    except Exception as e:
        bot.reply_to(
            message,
            f"❌ Stats Error\n\n{e}"
        )

print("🤖 Movie Bot Running...")

while True:
    try:
        bot.infinity_polling(
            skip_pending=True,
            timeout=60,
            long_polling_timeout=60
        )
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)