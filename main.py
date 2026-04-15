import json
import os
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

DATA_FILE = "products.json"
def load_products():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_products(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, CallbackContext
)
from datetime import datetime

OWNER_ID = 8016264348
admin_state = {}
produk_file = "produk.json"
saldo_file = "saldo.json"
deposit_file = "pending_deposit.json"
riwayat_file = "riwayat.json"
statistik_file = "statistik.json"

def load_json(file):
    if not os.path.exists(file):
        return {} if file.endswith(".json") else []
    with open(file, "r") as f:
        content = f.read().strip()
        if not content:
            return {} if file.endswith(".json") else []
        return json.loads(content)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

def update_statistik(uid, nominal):
    statistik = load_json(statistik_file)
    uid = str(uid)
    if uid not in statistik:
        statistik[uid] = {"jumlah": 0, "nominal": 0}
    statistik[uid]["jumlah"] += 1
    statistik[uid]["nominal"] += nominal
    save_json(statistik_file, statistik)

def add_riwayat(uid, tipe, keterangan, jumlah):
    riwayat = load_json(riwayat_file)
    if str(uid) not in riwayat:
        riwayat[str(uid)] = []
    riwayat[str(uid)].append({
        "tipe": tipe,
        "keterangan": keterangan,
        "jumlah": jumlah,
        "waktu": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    })
    save_json(riwayat_file, riwayat)
    if tipe == "BELI":
        update_statistik(uid, jumlah)

async def send_main_menu(context, chat_id, user):
    saldo = load_json(saldo_file)
    statistik = load_json(statistik_file)
    s = saldo.get(str(user.id), 0)
    jumlah = statistik.get(str(user.id), {}).get("jumlah", 0)
    total = statistik.get(str(user.id), {}).get("nominal", 0)

    text = (
        f"👋 Selamat datang di *Raxi Store*!\n\n"
        f"🧑 Nama: {user.full_name}\n"
        f"🆔 ID: {user.id}\n"
        f"💰 Total Saldo Kamu: Rp{s:,}\n"
        f"📦 Total Transaksi: {jumlah}\n"
        f"💸 Total Nominal Transaksi: Rp{total:,}"
    )

    keyboard = [
        [InlineKeyboardButton("📋 List Produk", callback_data="list_produk"),
         InlineKeyboardButton("🛒 Stock", callback_data="cek_stok")],
        [InlineKeyboardButton("💰 Deposit Saldo", callback_data="deposit")],
        [InlineKeyboardButton("📖 Informasi Bot", callback_data="info_bot")],
    ]
    if user.id == OWNER_ID:
        keyboard.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel")])

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def send_main_menu_safe(update, context):
    if update.message:
        await send_main_menu(context, update.effective_chat.id, update.effective_user)
    elif update.callback_query:
        await update.callback_query.message.delete()
        await send_main_menu(context, update.callback_query.from_user.id, update.callback_query.from_user)

async def handle_list_produk(update, context): # HANDLE LIST PRODUK
    query = update.callback_query
    produk = load_json(produk_file)
    msg = "*LIST PRODUK*\n"
    keyboard = []
    row = []

    for i, (pid, item) in enumerate(produk.items(), start=1):
        msg += f"{pid} {item['nama']} - Rp{item.get('harga', 0):,}\n"
        if item["stok"] > 0:
            row.append(KeyboardButton(pid))
        else:
            row.append(KeyboardButton(f"{pid} SOLDOUT ❌"))
        if len(row) == 3:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([KeyboardButton("🔙 Kembali")])

    reply_keyboard = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await query.message.delete()
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=msg + "\nSilahkan pilih Nomor produk yang ingin dibeli.",
        reply_markup=reply_keyboard,
        parse_mode="Markdown"
    )


async def handle_cek_stok(update, context): # HANDLE CEK STOK
    query = update.callback_query
    produk = load_json(produk_file)
    now = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    msg = f"*Informasi Stok*\n- {now}\n\n"
    keyboard = []
    row = []

    for pid, item in produk.items():
        msg += f"{pid}. {item['nama']} ➔ {item['stok']}x\n"
        if item["stok"] > 0:
            row.append(KeyboardButton(pid))
        else:
            row.append(KeyboardButton(f"{pid} SOLDOUT ❌"))
        if len(row) == 3:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([KeyboardButton("🔙 Kembali")])

    reply_keyboard = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await query.message.delete()
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=msg,
        reply_markup=reply_keyboard,
        parse_mode="Markdown"
    )

async def handle_admin_add(update, context):
    query = update.callback_query
    admin_state[query.from_user.id] = "add_nama"

    await query.message.delete()
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="Kirim nama produk:"
    )

async def handle_admin_restock(update, context):
    query = update.callback_query
    admin_state[query.from_user.id] = "restock_id"

    await query.message.delete()
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="Kirim ID produk:"
    )

async def handle_admin_delete(update, context):
    query = update.callback_query

    admin_state[query.from_user.id] = "delete_id"

    await query.message.delete()
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="Kirim ID produk yang mau dihapus:"
    )

async def handle_produk_detail(update, context): # HANDLE PRODUK DETAIL
    query = update.callback_query
    data = query.data
    produk = load_json(produk_file)
    item = produk.get(data)

    if item["stok"] <= 0:
        await query.answer("Produk habis", show_alert=True)
        return

    harga = item["harga"]
    tipe = item["akun_list"][0]["tipe"] if item["akun_list"] else "-"
    stok = item["stok"]

    context.user_data["konfirmasi"] = {
        "produk_id": data,
        "jumlah": 1
    }

    text = (
        "KONFIRMASI PESANAN 🛒\n"
        "╭ - - - - - - - - - - - - - - - - - - - - - ╮\n"
        f"┊・Produk: {item['nama']}\n"
        f"┊・Variasi: {tipe}\n"
        f"┊・Harga satuan: Rp. {harga:,}\n"
        f"┊・Stok tersedia: {stok}\n"
        "┊ - - - - - - - - - - - - - - - - - - - - -\n"
        f"┊・Jumlah Pesanan: x1\n"
        f"┊・Total Pembayaran: Rp. {harga:,}\n"
        "╰ - - - - - - - - - - - - - - - - - - - - - ╯"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➖", callback_data="qty_minus"),
            InlineKeyboardButton("Jumlah: 1", callback_data="ignore"),
            InlineKeyboardButton("➕", callback_data="qty_plus")
        ],
        [InlineKeyboardButton("Konfirmasi Order ✅", callback_data="confirm_order")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_produk")]
    ])
    await query.message.delete()
    await context.bot.send_message(chat_id=query.from_user.id, text=text, reply_markup=keyboard)

async def handle_deposit(update, context):  # HANDLE DEPOSIT
    query = update.callback_query
    nominals = [10000, 15000, 20000, 25000]
    keyboard = [[InlineKeyboardButton(f"Rp{n:,}", callback_data=f"deposit_{n}") for n in nominals]]
    keyboard.append([InlineKeyboardButton("🔧 Custom Nominal", callback_data="deposit_custom")])
    keyboard.append([InlineKeyboardButton("🔙 Kembali ke Menu", callback_data="back_to_produk")])

    await query.edit_message_text(
        "💰 Pilih nominal deposit kamu:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_deposit_nominal(update, context): # HANDLE DEPOSIT NOMINAL
    query = update.callback_query
    data = query.data
    if data == "deposit_custom":
        context.user_data["awaiting_custom"] = True
        reply_keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("❌ Batalkan Deposit")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await query.message.delete()
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Ketik jumlah deposit yang kamu inginkan (angka saja):",
            reply_markup=reply_keyboard
        )
    else:
        nominal = int(data.split("_")[1])
        context.user_data["nominal_asli"] = nominal
        context.user_data["total_transfer"] = nominal + 23

        reply_keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("❌ Batalkan Deposit")]],
            resize_keyboard=True, one_time_keyboard=True
        )
        await query.message.delete()
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=f"💳 Transfer *Rp{nominal + 23:,}* ke:\n"
                 "`DANA 088902891757 A.N moh*** za*** ath****`\n"
                 "`SEABANK - A.N -`\n"
                 "`BANK JAGO - A.N -`\nSetelah transfer, kirim bukti ke bot ini.",
            parse_mode="Markdown",
            reply_markup=reply_keyboard
        )

async def handle_cancel_deposit(update, context):
    query = update.callback_query
    uid = str(query.from_user.id)
    pending = load_json(deposit_file)
    pending = [p for p in pending if str(p["user_id"]) != uid]
    save_json(deposit_file, pending)
    await query.edit_message_text("✅ Deposit kamu telah dibatalkan.")
    await send_main_menu(context, query.from_user.id, query.from_user)

async def handle_admin_panel(update, context):  # HANDLE ADMIN PANEL
    query = update.callback_query
    await query.answer()

    saldo = load_json(saldo_file)
    pending = load_json(deposit_file)

    text = "*📊 Data User:*\n"

    ada_saldo = False
    for u, s in saldo.items():
        if s > 0:
            text += f"• ID {u}: Rp{s:,}\n"
            ada_saldo = True

    if not ada_saldo:
        text += "Tidak ada saldo.\n"

    text += "\n*⏳ Pending Deposit:*\n"
    if pending:
        for p in pending:
            text += f"- @{p['username']} ({p['user_id']}) Rp{p['nominal']:,}\n"
    else:
        text += "Tidak ada."

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕️ Tambah Produk", callback_data="admin_add")],
        [InlineKeyboardButton("📦 Restock Produk", callback_data="admin_restock")],
        [InlineKeyboardButton("✏️ Rename Produk", callback_data="admin_rename")],
        [InlineKeyboardButton("🗑 Hapus Produk", callback_data="admin_delete")]
    ])

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def handle_admin_confirm(update, context): # HANDLE ADMIN CONFIRM
    query = update.callback_query
    user_id = int(query.data.split(":")[1])
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ YA", callback_data=f"final:{user_id}")],
        [InlineKeyboardButton("🔙 Batal", callback_data="back")]
    ])
    await query.edit_message_caption("Konfirmasi saldo ke user ini?", reply_markup=keyboard)


async def handle_admin_final(update, context): # HANDLE ADMIN FINAL
    query = update.callback_query
    user_id = int(query.data.split(":")[1])
    pending = load_json(deposit_file)
    saldo = load_json(saldo_file)

    item = next((p for p in pending if p["user_id"] == user_id), None)
    if item:
        nominal = item["nominal"]
        saldo[str(user_id)] = saldo.get(str(user_id), 0) + nominal
        save_json(saldo_file, saldo)
        pending = [p for p in pending if p["user_id"] != user_id]
        save_json(deposit_file, pending)
        add_riwayat(user_id, "DEPOSIT", "Konfirmasi Admin", nominal)

        await query.edit_message_caption(
            f"✅ Saldo Rp{nominal:,} berhasil ditambahkan ke user:\n"
            f"👤 Username: @{item['username']}\n"
            f"🆔 User ID: {user_id}"
        )
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ Saldo Rp{nominal:,} berhasil ditambahkan ke akunmu!",
            reply_markup=ReplyKeyboardRemove()
        )
        await send_main_menu(context, user_id, await context.bot.get_chat(user_id))

    else:
        await query.edit_message_caption("❌ Data deposit tidak ditemukan.")

async def handle_admin_reject(update, context): # HANDLE ADMIN REJECT
    query = update.callback_query
    user_id = int(query.data.split(":")[1])
    await query.edit_message_caption("❌ Deposit ditolak.")
    await context.bot.send_message(
        chat_id=user_id,
        text="❌ Deposit kamu ditolak oleh admin.",
        reply_markup=ReplyKeyboardRemove()
    )

async def handle_admin_rename(update, context):
    query = update.callback_query
    admin_state[query.from_user.id] = "rename_id"

    await query.message.delete()
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="Kirim ID produk yang mau di rename:"
    )

async def handle_qty_plus(update, context): # HANDLE QTY PLUS
    query = update.callback_query
    produk = load_json(produk_file)
    info = context.user_data.get("konfirmasi")
    if not info:
        await query.answer("Data tidak tersedia")
        return

    produk_id = info["produk_id"]
    item = produk.get(produk_id)
    if not item:
        await query.answer("Produk tidak ditemukan")
        return

    jumlah = info["jumlah"]
    if jumlah < item["stok"]:
        jumlah += 1
    context.user_data["konfirmasi"]["jumlah"] = jumlah

    total = jumlah * item["harga"]
    tipe = item["akun_list"][0]["tipe"] if item["akun_list"] else "-"

    text = (
        "KONFIRMASI PESANAN 🛒\n"
        "╭ - - - - - - - - - - - - - - - - - - - - - ╮\n"
        f"┊・Produk: {item['nama']}\n"
        f"┊・Variasi: {tipe}\n"
        f"┊・Harga satuan: Rp. {item['harga']:,}\n"
        f"┊・Stok tersedia: {item['stok']}\n"
        "┊ - - - - - - - - - - - - - - - - - - - - -\n"
        f"┊・Jumlah Pesanan: x{jumlah}\n"
        f"┊・Total Pembayaran: Rp. {total:,}\n"
        "╰ - - - - - - - - - - - - - - - - - - - - - ╯"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➖", callback_data="qty_minus"),
            InlineKeyboardButton(f"Jumlah: {jumlah}", callback_data="ignore"),
            InlineKeyboardButton("➕", callback_data="qty_plus")
        ],
        [InlineKeyboardButton("Konfirmasi Order ✅", callback_data="confirm_order")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_produk")]
    ])

    await query.edit_message_text(text, reply_markup=keyboard)

async def handle_qty_minus(update, context): # HANDLE QTY MINUS
    query = update.callback_query
    produk = load_json(produk_file)
    info = context.user_data.get("konfirmasi")
    if not info:
        await query.answer("Data tidak tersedia")
        return

    produk_id = info["produk_id"]
    item = produk.get(produk_id)
    if not item:
        await query.answer("Produk tidak ditemukan")
        return

    jumlah = info["jumlah"]
    if jumlah > 1:
        jumlah -= 1
    context.user_data["konfirmasi"]["jumlah"] = jumlah

    total = jumlah * item["harga"]
    tipe = item["akun_list"][0]["tipe"] if item["akun_list"] else "-"

    text = (
        "KONFIRMASI PESANAN 🛒\n"
        "╭ - - - - - - - - - - - - - - - - - - - - - ╮\n"
        f"┊・Produk: {item['nama']}\n"
        f"┊・Variasi: {tipe}\n"
        f"┊・Harga satuan: Rp. {item['harga']:,}\n"
        f"┊・Stok tersedia: {item['stok']}\n"
        "┊ - - - - - - - - - - - - - - - - - - - - -\n"
        f"┊・Jumlah Pesanan: x{jumlah}\n"
        f"┊・Total Pembayaran: Rp. {total:,}\n"
        "╰ - - - - - - - - - - - - - - - - - - - - - ╯"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➖", callback_data="qty_minus"),
            InlineKeyboardButton(f"Jumlah: {jumlah}", callback_data="ignore"),
            InlineKeyboardButton("➕", callback_data="qty_plus")
        ],
        [InlineKeyboardButton("Konfirmasi Order ✅", callback_data="confirm_order")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_produk")]
    ])

    await query.edit_message_text(text, reply_markup=keyboard)


async def handle_confirm_order(update, context): # HANDLE CONFIRM ORDER
    query = update.callback_query
    uid = str(query.from_user.id)
    produk = load_json(produk_file)
    saldo = load_json(saldo_file)
    info = context.user_data.get("konfirmasi")
    if not info:
        await query.answer("❌ Data pesanan tidak ditemukan", show_alert=True)
        return

    produk_id = info["produk_id"]
    jumlah = info["jumlah"]
    item = produk.get(produk_id)
    if not item:
        await query.edit_message_text("❌ Produk tidak ditemukan.")
        return

    total = jumlah * item["harga"]

    if saldo.get(uid, 0) < total:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Deposit Saldo", callback_data="deposit")],
            [InlineKeyboardButton("🔙 Kembali ke Menu", callback_data="back_to_produk")]
        ])
        await query.edit_message_text(
            "❌ *Saldo kamu tidak cukup untuk menyelesaikan pesanan.*\n"
            "Silakan deposit saldo terlebih dahulu atau kembali ke menu utama.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return

    if item["stok"] < jumlah or len(item["akun_list"]) < jumlah:
        await query.edit_message_text("❌ Stok atau akun tidak mencukupi.")
        return

    saldo[uid] -= total
    item["stok"] -= jumlah
    akun_terpakai = [item["akun_list"].pop(0) for _ in range(jumlah)]
    save_json(saldo_file, saldo)
    save_json(produk_file, produk)
    add_riwayat(uid, "BELI", f"{item['nama']} x{jumlah}", total)

    os.makedirs("akun_dikirim", exist_ok=True)
    file_path = f"akun_dikirim/{uid}_{produk_id}_x{jumlah}.txt"
    with open(file_path, "w") as f:
        for i, akun in enumerate(akun_terpakai, start=1):
            f.write(
                f"Akun #{i}\n"
                f"Username: {akun['username']}\n"
                f"Password: {akun['password']}\n"
                f"Tipe: {akun['tipe']}\n"
                "---------------------------\n"
            )

    with open(file_path, "rb") as f:
        await context.bot.send_document(
            chat_id=query.from_user.id,
            document=InputFile(f, filename=os.path.basename(file_path)),
            caption=f"📦 Pembelian *{item['nama']}* x{jumlah} berhasil!\nSisa saldo: Rp{saldo[uid]:,}",
            parse_mode="Markdown"
        )

    context.user_data.pop("konfirmasi", None)
    await send_main_menu(context, query.from_user.id, query.from_user)

async def handle_back(update, context): # HANDLE BACK
    query = update.callback_query
    await query.edit_message_caption("✅ Dibatalkan.")


async def handle_back_to_produk(update, context): # HANDLE BACK TO PRODUK
    query = update.callback_query
    await query.message.delete()
    await send_main_menu(context, query.from_user.id, query.from_user)

async def handle_info_bot(update, context):
    query = update.callback_query

    text = (
        "╔══════════════════════╗\n"
        "      📖 INFORMASI BOT\n"
        "╚══════════════════════╝\n\n"
        "🧠 Nama Bot : Store Raxi\n"
        "👨‍💻 Author   : @raxiyesir\n"
        "🛒 Fungsi   : Penjualan akun digital otomatis\n"
        "⚙️ Fitur    : Auto Order, Deposit, Instant Delivery\n\n"
        "╚══════════════════════╝"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_produk")]
    ])

    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def handle_ignore(update, context): # HANDLE IGNORE

    query = update.callback_query
    await query.answer()
    await query.edit_message_text

callback_handlers = {
    "list_produk": handle_list_produk,
    "cek_stok": handle_cek_stok,
    "deposit": handle_deposit,
    "deposit_custom": handle_deposit_nominal,
    "cancel_deposit": handle_cancel_deposit,
    "admin_panel": handle_admin_panel,
    "qty_plus": handle_qty_plus,
    "qty_minus": handle_qty_minus,
    "confirm_order": handle_confirm_order,
    "back": handle_back,
    "back_to_produk": handle_back_to_produk,
    "admin_add": handle_admin_add,
    "admin_restock": handle_admin_restock,
    "admin_rename": handle_admin_rename,
    "admin_delete": handle_admin_delete,
    "ignore": handle_ignore,
}

async def handle_admin_add(update, context):
    query = update.callback_query
    admin_state[query.from_user.id] = "add_nama"
    await query.message.delete()
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="Kirim nama produk:"
    )

async def handle_admin_restock(update, context):
    query = update.callback_query
    admin_state[query.from_user.id] = "restock_id"
    await query.message.delete()
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="Kirim ID produk:"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # 📖 INFO BOT
    if data == "info_bot":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_menu")]
        ])

        await query.edit_message_text(
            "╔══════════════════════╗\n"
            "      📖 INFORMASI BOT\n"
            "╚══════════════════════╝\n\n"
            "🧠 Nama Bot : Store Raxi\n"
            "👨‍💻 Author   : @raxiyesir\n"
            "🛒 Fungsi   : Penjualan akun digital otomatis\n"
            "⚙️ Fitur    : Auto Order, Deposit, Instant Delivery\n",
            reply_markup=keyboard
        )

    # 🛒 PRODUK DETAIL
    elif data in load_json(produk_file):
        await handle_produk_detail(update, context)

    # 💰 DEPOSIT
    elif data.startswith("deposit_"):
        await handle_deposit_nominal(update, context)

    # 🛠 ADMIN CONFIRM
    elif data.startswith("confirm:"):
        await handle_admin_confirm(update, context)

    # 🛠 ADMIN FINAL
    elif data.startswith("final:"):
        await handle_admin_final(update, context)

    # 🛠 ADMIN REJECT
    elif data.startswith("reject:"):
        await handle_admin_reject(update, context)

    # 🔧 CALLBACK LAINNYA
    elif data in callback_handlers:
        await callback_handlers[data](update, context)

    # ❌ DEFAULT
    else:
        await query.edit_message_text("❌ Aksi tidak dikenali,start ulang /start.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    saldo = load_json(saldo_file)
    transaksi = load_json(transaksi_file) if "transaksi_file" in globals() else {}

    total_transaksi = transaksi.get(str(uid), {}).get("total", 0)
    total_nominal = transaksi.get(str(uid), {}).get("nominal", 0)

    text = (
        "👋 Selamat datang di Raxi Store!\n\n"
        f"🧑 Nama: {user.first_name}\n"
        f"🆔 ID: {uid}\n"
        f"💰 Total Saldo Kamu: Rp{saldo.get(str(uid), 0):,}\n"
        f"📦 Total Transaksi: {total_transaksi}\n"
        f"💸 Total Nominal Transaksi: Rp{total_nominal:,}\n"
    )

    keyboard = [
        [InlineKeyboardButton("🛒 List Produk", callback_data="list_produk")],
        [InlineKeyboardButton("💰 Deposit", callback_data="deposit")],
        [InlineKeyboardButton("ℹ️ Info Bot", callback_data="info_bot")]
    ]

    # 🔥 tombol admin kalau ID cocok
    if uid == OWNER_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid_int = update.effective_user.id
    uid = str(uid_int)
    produk = load_json(produk_file)

    # ===== ADMIN MODE =====
    if uid_int in admin_state:
        state = admin_state[uid_int]

        # TAMBAH PRODUK
        if state == "add_nama":
            context.user_data["nama_produk"] = text
            admin_state[uid_int] = "add_harga"
            await update.message.reply_text("Kirim harga:")
            return

        elif state == "add_harga":
            context.user_data["harga"] = int(text)
            admin_state[uid_int] = "add_id"
            await update.message.reply_text("Kirim ID produk (contoh: P1):")
            return

        elif state == "add_id":
            pid = text
            produk[pid] = {
                "nama": context.user_data["nama_produk"],
                "harga": context.user_data["harga"],
                "stok": 0,
                "akun_list": []
            }
            save_json(produk_file, produk)

            admin_state.pop(uid_int)
            await update.message.reply_text(f"✅ Produk {pid} berhasil dibuat")
            return

        # RESTOCK
        elif state == "restock_id":
            if text not in produk:
                await update.message.reply_text("❌ ID tidak ditemukan")
                return

            context.user_data["pid"] = text
            admin_state[uid_int] = "restock_akun"
            await update.message.reply_text(
                "Kirim akun (format: username,password,tipe)\nPisah pakai enter"
            )
            return

        elif state == "restock_akun":
            pid = context.user_data["pid"]
            lines = text.split("\n")

            berhasil = 0
            for line in lines:
                try:
                    u, p, t = line.split(",")
                    produk[pid]["akun_list"].append({
                        "username": u,
                        "password": p,
                        "tipe": t
                    })
                    produk[pid]["stok"] += 1
                    berhasil += 1
                except:
                    continue

            save_json(produk_file, produk)

            admin_state.pop(uid_int)
            await update.message.reply_text(f"✅ Restock {berhasil} akun berhasil")
            return

        # RENAME PRODUK
        elif state == "rename_id":
            if text not in produk:
                await update.message.reply_text("❌ ID tidak ditemukan")
                return

            context.user_data["rename_pid"] = text
            admin_state[uid_int] = "rename_nama"
            await update.message.reply_text("Kirim nama baru:")
            return

        elif state == "rename_nama":
            pid = context.user_data["rename_pid"]

            produk[pid]["nama"] = text
            save_json(produk_file, produk)

            admin_state.pop(uid_int)
            await update.message.reply_text(f"✅ Nama produk {pid} berhasil diubah")
            return

        # DELETE PRODUK
        elif state == "delete_id":
            if text not in produk:
                await update.message.reply_text("❌ ID tidak ditemukan")
                return

            # hapus produk
            produk.pop(text)

            save_json(produk_file, produk)

            admin_state.pop(uid_int)

            await update.message.reply_text(f"✅ Produk {text} berhasil dihapus")
            return 

    # ===== NORMAL FLOW =====

    if "SOLDOUT" in text:
        text = text.split()[0]

    # CANCEL DEPOSIT
    if text == "❌ Batalkan Deposit":
        pending = load_json(deposit_file)
        pending = [p for p in pending if str(p["user_id"]) != uid]
        save_json(deposit_file, pending)

        await update.message.reply_text(
            "✅ Deposit kamu telah dibatalkan.",
            reply_markup=ReplyKeyboardRemove()
        )
        await send_main_menu_safe(update, context)
        return

    # CUSTOM DEPOSIT
    if context.user_data.get("awaiting_custom"):
        try:
            nominal = int(text)
            context.user_data["awaiting_custom"] = False
            context.user_data["nominal_asli"] = nominal
            context.user_data["total_transfer"] = nominal + 23

            reply_keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("❌ Batalkan Deposit")]],
                resize_keyboard=True,
                one_time_keyboard=True
            )

            await update.message.reply_text(
                f"💳 Transfer *Rp{nominal + 23:,}* ke:\n"
                "`DANA 088902891757 a.n. moh**** za**** ath*****`\n"
                "Setelah transfer, kirim bukti foto ke bot ini.",
                parse_mode="Markdown",
                reply_markup=reply_keyboard
            )
        except:
            await update.message.reply_text("❌ Masukkan angka yang benar")
        return

    # PILIH PRODUK
    if text in produk:
        item = produk[text]

        if item["stok"] <= 0:
            await update.message.reply_text("❌ Produk habis")
            await send_main_menu_safe(update, context)
            return

        harga = item["harga"]
        tipe = item["akun_list"][0]["tipe"] if item["akun_list"] else "-"
        stok = item["stok"]

        context.user_data["konfirmasi"] = {
            "produk_id": text,
            "jumlah": 1
        }

        msg = (
            "KONFIRMASI PESANAN 🛒\n"
            f"Produk: {item['nama']}\n"
            f"Variasi: {tipe}\n"
            f"Harga: Rp{harga:,}\n"
            f"Stok: {stok}\n"
            f"Total: Rp{harga:,}"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➖", callback_data="qty_minus"),
                InlineKeyboardButton("Jumlah: 1", callback_data="ignore"),
                InlineKeyboardButton("➕", callback_data="qty_plus")
            ],
            [InlineKeyboardButton("Konfirmasi Order ✅", callback_data="confirm_order")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_produk")]
        ])

        await update.message.reply_text(msg, reply_markup=keyboard)
        return

    # BACK
    if text == "🔙 Kembali":
        await send_main_menu_safe(update, context)
        return

    await send_main_menu_safe(update, context)

async def handle_photo(update: Update, context: CallbackContext):
    user = update.effective_user
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    os.makedirs("bukti", exist_ok=True)
    path = f"bukti/{user.id}.jpg"
    await file.download_to_drive(path)

    nominal = context.user_data.get("nominal_asli", 0)
    total = context.user_data.get("total_transfer", nominal)

    pending = load_json(deposit_file)
    pending.append({
        "user_id": user.id,
        "username": user.username,
        "bukti_path": path,
        "nominal": nominal,
        "total_transfer": total
    })
    save_json(deposit_file, pending)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Konfirmasi", callback_data=f"confirm:{user.id}")],
        [InlineKeyboardButton("❌ Tolak", callback_data=f"reject:{user.id}")]
    ])
    with open(path, "rb") as f:
        await context.bot.send_photo(
            chat_id=OWNER_ID,
            photo=InputFile(f),
            caption=f"📥 Deposit dari @{user.username or user.id}\n"
                    f"Transfer: Rp{total:,}\nMasuk: Rp{nominal:,}",
            reply_markup=keyboard
        )
    await update.message.reply_text("✅ Bukti dikirim! Tunggu konfirmasi admin.")

def main(): 
    app = Application.builder().token("8505410323:AAFPLFtHHj06Z-xAHyxQTSDGELYyuoAXY0w").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
