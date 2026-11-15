from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import subprocess, requests, time, os
TOKEN_TELEGRAM_BOT = os.getenv("TOKEN_TELEGRAM_BOT")
AKUN_FB = {
6565700506: {
"nama": "zax",
    "FB_TOKEN": os.getenv("FB_TOKEN_ZAX"),
    "FB_PAGE_ID": os.getenv("FB_PAGE_ID_ZAX"),
"watermark": "RizkyDrama",
"telegram_link": "https://t.me/RizkyDrama"
},
987654321: {
"nama": "Budi",
"FB_TOKEN": os.getenv("FB_TOKEN_BUDI"),
    "FB_PAGE_ID": os.getenv("FB_PAGE_ID_BUDI"),
"watermark": "BudiDrama",
"telegram_link": "https://t.me/BudiDrama"
},
}
nunggu_judul = {}

def upload_reels(akun, hasil, caption, judul):
    import requests, os
    base = f"https://graph.facebook.com/v19.0/{akun['FB_PAGE_ID']}/video_reels"
    token = akun['FB_TOKEN']
    # TAHAP 1: START
    r1 = requests.post(base, data={"access_token": token, "upload_phase": "start", "file_size": os.path.getsize(hasil)})
    print("START:", r1.text[:300])
    if r1.status_code != 200:
        return r1
    data = r1.json()
    video_id = data.get("video_id")
    upload_url = data.get("upload_url")
    # TAHAP 2: TRANSFER
    with open(hasil, "rb") as f:
        r2 = requests.post(upload_url, headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(os.path.getsize(hasil))}, data=f)
    print("TRANSFER:", r2.text[:300])
    # TAHAP 3: FINISH + PUBLISH
    r3 = requests.post(base, data={"access_token": token, "upload_phase": "finish", "video_id": video_id, "video_state": "PUBLISHED", "description": caption, "title": judul})
    print("FINISH:", r3.text[:300])
    # Gawe object koyo requests ben kode lawas iso mlaku
    class R:
        def __init__(self, resp, vid):
            self.status_code = resp.status_code
            self._resp = resp
            self._vid = vid
        def json(self):
            try:
                j = self._resp.json()
            except:
                j = {}
            if "id" not in j and self._vid:
                j["id"] = self._vid
            return j
        @property
        def text(self):
            return self._resp.text
    return R(r3, video_id)

def edit_pro(input_path, output_path, judul, watermark, part_ke, start):

    filter_pro = f"crop=iw*0.95:ih*0.95,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,eq=contrast=1.05:brightness=0.01:saturation=1.08,drawbox=x=0:y=0:w=iw:h=80:color=black:t=fill,drawbox=x=0:y=ih-80:w=iw:h=80:color=black:t=fill,drawtext=text='{judul.upper()}':fontsize=30:fontcolor=white:borderw=3:bordercolor=black:x=(w-text_w)/2:y=20,drawtext=text='':fontsize=22:fontcolor=yellow:borderw=2:bordercolor=black:x=(w-text_w)/2:y=h-th-110,drawtext=text='{watermark}':fontsize=20:fontcolor=white@0.8:borderw=2:bordercolor=black:x=w-tw-20:y=100"
    cmd = ["ffmpeg", "-y", "-ss", str(start), "-t", "30", "-i", input_path, "-vf", filter_pro, "-c:a", "aac", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", output_path]
    subprocess.run(cmd)

async def terima_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in AKUN_FB:
        await update.message.reply_text(f"@{user.username} kowe durung kedafatar!")
        return
    video = update.message.video
    if not video:
        return
    file = await video.get_file()
    path = f"video_{user.id}.mp4"
    await file.download_to_drive(path)
    nunggu_judul[user.id] = path
    await update.message.reply_text(f"@{user.username} Video ketompo! Kirim JUDUL-e!")
async def terima_judul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in nunggu_judul:
        return
    judul = update.message.text
    if judul.startswith("/"):
        return
    path = nunggu_judul[user.id]
    akun = AKUN_FB[user.id]
    caption = f"{judul.upper()}\n\nPart selanjutnya udah aku upload di TELEGRAM!\nLink Telegram ada di KOMEN PERTAMA!\nFollow {akun['watermark']}!"
    await update.message.reply_text(f"Oke @{user.username}! Proses...")
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path], capture_output=True, text=True)
    try:
        durasi = float(probe.stdout.strip())
    except:
        durasi = 60
    mulai_drama = 15
    sukses = 0
    for i in range(1):
        part_ke = i + 1
        start = mulai_drama + (i * 15)
        if start >= durasi:
            break
        hasil = f"RAPI_{akun['nama']}_part{part_ke}.mp4"
        edit_pro(path, hasil, judul, akun['watermark'], part_ke, start)
        r = upload_reels(akun, hasil, caption, judul)
        try:
            os.remove(hasil)
        except:
            pass
        if r.status_code == 200 and "id" in r.json():
            sukses += 1
            video_id = r.json().get("id")
            time.sleep(3)
            requests.post(f"https://graph.facebook.com/v19.0/{video_id}/comments", data={"access_token": akun['FB_TOKEN'], "message": f"Link Telegramnya di sini ya! \n{akun['telegram_link']}"})
        else:
            await update.message.reply_text(f"GAGAL ! Token mati! {r.text[:200]}")
            break
    if sukses > 0:
        await update.message.reply_text(f"BERHASIL! {sukses} Reels ke-upload neng akun {akun['nama']}!")
    try:
        os.remove(path)
    except:
        pass
    try:
        await update.message.delete()
    except:
        pass
    del nunggu_judul[user.id]
app = Application.builder().token(TOKEN_TELEGRAM_BOT).build()
app.add_handler(MessageHandler(filters.VIDEO, terima_video))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, terima_judul))
print("Bot wes mlaku!")
app.run_polling()