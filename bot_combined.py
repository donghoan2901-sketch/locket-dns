import asyncio
import re
import json
import os
import time
from datetime import datetime
from telethon import TelegramClient, events
from playwright.async_api import async_playwright
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# ========== CẤU HÌNH ==========
API_ID = 31864866
API_HASH = "f86d98c1be623429ce7fbbfe8b0bd53f"
PHONE = "+84354538918"
ADMIN_ID = 6713837761
BOT_TOKEN = "8992567482:AAHbURXtE9x7xHxVTtjDFPzTn7Muay3jX2M"
POSITION_FILE = "input_position.json"
KEYS_FILE = "keys.json"
USER_KEYS_FILE = "user_keys.json"
BANNED_FILE = "banned.json"
PROFILE_PATH = "D:/locket-bot/locket.mobileconfig"
ZALO_LINK = "https://zalo.me/0815544869"
# ================================

otp_queue = asyncio.Queue()
browser = None
page = None
web_logged_in = False

# ========== QUẢN LÝ KEY & BAN ==========
def load_keys():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_keys(keys):
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)

def load_user_keys():
    if os.path.exists(USER_KEYS_FILE):
        with open(USER_KEYS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_keys(keys):
    with open(USER_KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)

def load_banned():
    if os.path.exists(BANNED_FILE):
        with open(BANNED_FILE, "r") as f:
            return json.load(f)
    return []

def save_banned(banned):
    with open(BANNED_FILE, "w") as f:
        json.dump(banned, f, indent=2)

def generate_key():
    import random
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=12))

def check_key(key):
    keys = load_keys()
    if key not in keys:
        return None
    if keys[key]["expires"] < time.time():
        return None
    return keys[key]

def is_banned(username):
    return username in load_banned()

# ========== USERBOT ĐỌC OTP ==========
user_client = TelegramClient("locket_user", API_ID, API_HASH)

@user_client.on(events.NewMessage)
async def user_handler(event):
    text = event.message.text
    match = re.search(r'\b(\d{6})\b', text)
    if match:
        print(f"📥 Bắt OTP: {match.group(1)}")
        await otp_queue.put(match.group(1))

# ========== ĐĂNG NHẬP WEB ==========
async def save_position(selector):
    with open(POSITION_FILE, "w") as f:
        json.dump({"selector": selector}, f)

async def load_position():
    if os.path.exists(POSITION_FILE):
        with open(POSITION_FILE, "r") as f:
            data = json.load(f)
            return data.get("selector")
    return None

async def login_web():
    global browser, page, web_logged_in
    print("🚀 Mở trình duyệt...")
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=False)
    page = await browser.new_page()
    
    await page.goto('https://locket.khotools.com/')
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(1000)
    
    saved_selector = await load_position()
    if saved_selector:
        await page.wait_for_selector(saved_selector, timeout=5000)
        await page.fill(saved_selector, str(ADMIN_ID))
    else:
        print("👉 Lần đầu: Click chuột vào ô 'Telegram ID (số)'")
        await page.wait_for_selector('input:focus', timeout=30000)
        focused_selector = await page.evaluate('''() => {
            let el = document.activeElement;
            if (el.id) return '#' + el.id;
            if (el.name) return '[name="' + el.name + '"]';
            return null;
        }''')
        if focused_selector:
            await save_position(focused_selector)
            await page.fill(focused_selector, str(ADMIN_ID))
    
    await page.click('button:has-text("Gửi mã OTP")')
    print("📨 Đã gửi OTP, đang chờ...")
    otp = await otp_queue.get()
    print(f"✅ Nhận OTP: {otp}")
    
    await page.wait_for_timeout(3000)
    otp_boxes = await page.query_selector_all('input[type="text"][maxlength="1"]')
    if len(otp_boxes) == 6:
        for i, digit in enumerate(otp):
            await otp_boxes[i].fill(digit)
    else:
        otp_input = await page.wait_for_selector('input[placeholder*="OTP"], input[name="otp"]', timeout=5000)
        await otp_input.fill(otp)
    
    await page.click('button:has-text("Xác nhận")')
    await page.wait_for_load_state('networkidle')
    web_logged_in = True
    print("✅ Đăng nhập web thành công!")

# ========== KICK GOLD ==========
async def kick_gold(username):
    global page, web_logged_in
    if not web_logged_in or not page:
        return {"ok": False, "error": "Bot chưa sẵn sàng"}
    
    if is_banned(username):
        return {"ok": False, "error": f"Username {username} đã bị ban"}
    
    await page.goto('https://locket.khotools.com/dashboard')
    await page.fill('#act-username', username)
    await page.click('#form-activate-username button')
    
    await page.wait_for_selector('.terminal .t-success, .terminal .t-error', timeout=60000)
    terminal_text = await page.inner_text('.terminal')
    
    return {"ok": True, "terminal": terminal_text}

# ========== GỬI DNS ==========
async def send_dns_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dns_link = "https://drive.google.com/uc?export=download&id=1mmhv2dDDGdoy4p-xdyHQfCt7xm6R8y1c"
    
    await update.message.reply_text(
        f"📱 *🔐 CÀI DNS CHẶN THU HỒI GOLD (iOS)*\n\n"
        f"👉 [Bấm vào đây để tải và cài DNS]({dns_link})\n\n"
        f"Sau khi tải, file sẽ tự động mở trong **Cài đặt**.\n"
        f"Nhấn **'Cài đặt'** → **'Cài đặt'** → **'Tin cậy'** (nếu có).\n\n"
        f"🎉 *XONG! Gold sẽ không bị thu hồi!*",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    
    await update.message.reply_text(
        f"🤖 *🔐 HƯỚNG DẪN CÀI DNS TRÊN ANDROID*\n\n"
        f"1️⃣ Vào **Cài đặt** → **Kết nối** → **DNS riêng (Private DNS)**\n"
        f"2️⃣ Chọn **Tên máy chủ DNS riêng**\n"
        f"3️⃣ Nhập: `acb2f8.dns.subhatde.id.vn`\n\n"
        f"🎉 *XONG! Gold sẽ không bị thu hồi!*",
        parse_mode="Markdown"
    )

# ========== BOT TELEGRAM ==========
app = Application.builder().token(BOT_TOKEN).build()
ENTER_KEY, ENTER_USERNAME = 1, 2

# ========== ADMIN LUỒNG RIÊNG ==========
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Chỉ admin.")
        return
    
    keyboard = [
        [InlineKeyboardButton("➕ Tạo Key", callback_data="admin_create_key")],
        [InlineKeyboardButton("📋 Danh sách Key", callback_data="admin_list_keys")],
        [InlineKeyboardButton("🗑️ Thu hồi Key", callback_data="admin_revoke_key")],
        [InlineKeyboardButton("🚫 Ban Username", callback_data="admin_ban")],
        [InlineKeyboardButton("✅ Gỡ Ban", callback_data="admin_unban")],
        [InlineKeyboardButton("👑 Kick Gold (Admin)", callback_data="admin_kick")],
        [InlineKeyboardButton("❌ Thoát", callback_data="admin_exit")]
    ]
    await update.message.reply_text(
        "✨ *BẢNG ĐIỀU KHIỂN ADMIN* ✨\n\n👇 *Chọn chức năng:* 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "admin_create_key":
        await query.edit_message_text("⏰ Nhập số giờ muốn key có hiệu lực (VD: 24):")
        context.user_data["admin_action"] = "create_key"
        return
    
    elif data == "admin_list_keys":
        keys = load_keys()
        if not keys:
            await query.edit_message_text("📭 Chưa có key nào.")
            return
        text = "📋 *Danh sách key:*\n\n"
        for k, v in keys.items():
            expires = datetime.fromtimestamp(v["expires"]).strftime("%d/%m %H:%M")
            text += f"🔑 `{k}`\n   ⏰ hết {expires}\n\n"
        await query.edit_message_text(text, parse_mode="Markdown")
        await asyncio.sleep(5)
        await admin_panel(update, context)
        return
    
    elif data == "admin_revoke_key":
        await query.edit_message_text("🗑️ Nhập key cần thu hồi:")
        context.user_data["admin_action"] = "revoke_key"
        return
    
    elif data == "admin_ban":
        await query.edit_message_text("🚫 Nhập username Locket cần BAN:")
        context.user_data["admin_action"] = "ban"
        return
    
    elif data == "admin_unban":
        await query.edit_message_text("✅ Nhập username Locket cần GỠ BAN:")
        context.user_data["admin_action"] = "unban"
        return
    
    elif data == "admin_kick":
        await query.edit_message_text("✏️ Nhập username Locket cần kick:")
        context.user_data["admin_action"] = "admin_kick"
        return ENTER_USERNAME
    
    elif data == "admin_exit":
        await query.edit_message_text("👋 Thoát menu admin. Gõ /admin để mở lại.")
        return

async def admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    action = context.user_data.get("admin_action")
    value = update.message.text.strip()
    
    if action == "create_key":
        hours = int(value)
        key = generate_key()
        keys = load_keys()
        keys[key] = {"expires": time.time() + hours * 3600}
        save_keys(keys)
        await update.message.reply_text(f"✅ *Key:* `{key}`\n⏰ {hours} giờ", parse_mode="Markdown")
    
    elif action == "revoke_key":
        keys = load_keys()
        if value in keys:
            del keys[value]
            save_keys(keys)
            await update.message.reply_text(f"✅ Đã thu hồi key `{value}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Không tìm thấy key.")
    
    elif action == "ban":
        banned = load_banned()
        if value not in banned:
            banned.append(value)
            save_banned(banned)
            await update.message.reply_text(f"✅ Đã ban `{value}`", parse_mode="Markdown")
    
    elif action == "unban":
        banned = load_banned()
        if value in banned:
            banned.remove(value)
            save_banned(banned)
            await update.message.reply_text(f"✅ Đã gỡ ban `{value}`", parse_mode="Markdown")
    
    elif action == "admin_kick":
        await update.message.reply_text(f"👑 *Admin đang kick {value}...*", parse_mode="Markdown")
        result = await kick_gold(value)
        if result["ok"]:
            await update.message.reply_text(f"✅ *KICK THÀNH CÔNG!*\n\n`{result['terminal'][:300]}`", parse_mode="Markdown")
            await send_dns_instructions(update, context)
        else:
            await update.message.reply_text(f"❌ *Lỗi:* {result['error']}", parse_mode="Markdown")
        await admin_panel(update, context)
        return
    
    context.user_data["admin_action"] = None
    await admin_panel(update, context)

# ========== NGƯỜI DÙNG (GIAO DIỆN ĐẸP) ==========
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔑 Nhập Key", callback_data="enter_key")],
        [InlineKeyboardButton("⚡ KICK GOLD NGAY", callback_data="kick_ready")],
        [InlineKeyboardButton("🆘 Hỗ Trợ", url=ZALO_LINK)]
    ]
    await update.message.reply_text(
        "✨ *LOCKET GOLD BOT* ✨\n\n"
        f"👤 *User:* Đồng Hoan\n"
        f"🆔 *Telegram ID:* `{ADMIN_ID}`\n"
        f"💎 *Gói:* VIP\n"
        f"♾️ *Trạng thái:* Không giới hạn lượt kick\n\n"
        "🤝 *Hy vọng mỗi người dùng ủng hộ 5-10k để bọn mình có động lực phát triển!*\n\n"
        "👇 *Chọn chức năng bên dưới:* 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def enter_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("🔑 Vui lòng gửi key của bạn:")
    return ENTER_KEY

async def receive_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = update.message.text.strip().upper()
    if not check_key(key):
        keyboard = [[InlineKeyboardButton("🆘 Hỗ Trợ", url=ZALO_LINK)]]
        await update.message.reply_text(
            "❌ *Key không hợp lệ hoặc hết hạn!*\n\nVui lòng liên hệ admin để được hỗ trợ.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    user_keys = load_user_keys()
    user_keys[str(update.effective_user.id)] = key
    save_user_keys(user_keys)
    
    await update.message.reply_text(
        "✅ *KEY HỢP LỆ!*\n\n👉 Bấm nút **'KICK GOLD NGAY'** bên dưới để tiếp tục.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚡ KICK GOLD NGAY", callback_data="kick_ready")]]),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def kick_ready_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("✏️ Nhập username Locket cần kick:")
    return ENTER_USERNAME

async def receive_username_and_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip()
    user_id = str(update.effective_user.id)
    user_keys = load_user_keys()
    
    if user_id not in user_keys:
        await update.message.reply_text("❌ Bạn chưa có key. Gõ /start để nhập key.")
        return ConversationHandler.END
    
    key = user_keys[user_id]
    if not check_key(key):
        await update.message.reply_text("❌ Key đã hết hạn. Vui lòng nhập key mới.")
        user_keys.pop(user_id, None)
        save_user_keys(user_keys)
        return ConversationHandler.END
    
    msg = await update.message.reply_text(f"⏳ *Đang kick {username}...*", parse_mode="Markdown")
    result = await kick_gold(username)
    
    if result["ok"]:
        await msg.edit_text(f"✅ *KICK THÀNH CÔNG!*\n\n`{result['terminal'][:300]}`", parse_mode="Markdown")
        await send_dns_instructions(update, context)
        keyboard = [[InlineKeyboardButton("⚡ KICK TIẾP", callback_data="kick_ready")]]
        await update.message.reply_text("👉 *Bấm nút để kick tiếp:*", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        error_keyboard = [[InlineKeyboardButton("🆘 Hỗ Trợ", url=ZALO_LINK)]]
        await msg.edit_text(
            f"❌ *LỖI:* `{result['error']}`\n\nLiên hệ admin để được hỗ trợ.",
            reply_markup=InlineKeyboardMarkup(error_keyboard),
            parse_mode="Markdown"
        )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Đã hủy.")
    return ConversationHandler.END

# ========== ĐĂNG KÝ HANDLER ==========
# Người dùng
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", welcome), CallbackQueryHandler(enter_key_callback, pattern="enter_key"), CallbackQueryHandler(kick_ready_callback, pattern="kick_ready")],
    states={ENTER_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_key)], ENTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username_and_kick)]},
    fallbacks=[CommandHandler("cancel", cancel)],
)
app.add_handler(conv_handler)

# Admin
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Chat(ADMIN_ID), admin_input))

# ========== MAIN ==========
async def main():
    await user_client.start(PHONE)
    print("✅ Userbot đã đăng nhập Telegram")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("✅ Bot Telegram đã sẵn sàng")
    await login_web()
    print("🚀 HỆ THỐNG SẴN SÀNG!")
    print(f"👑 Admin: gõ /admin để mở menu")
    print("📌 Người dùng: gõ /start để bắt đầu")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())