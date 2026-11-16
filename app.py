import os
import io
import time
import random
import sqlite3
from flask import Flask, render_template, request, jsonify
import requests
from PIL import Image

app = Flask(__name__)
DB_PATH = "game1.db"
ANIMALS_DIR = os.path.join("static", "animals")
VOICES_DIR = os.path.join("static", "voices")
os.makedirs(ANIMALS_DIR, exist_ok=True)
os.makedirs(VOICES_DIR, exist_ok=True)

DEFAULT_ANIMALS = ["lion","tiger","wolf","fox","elephant","giraffe","zebra",
                   "panda","koala","eagle","owl","dolphin","bear","cat","dog"]
WIKI_MAP = {
    "lion":"Lion","tiger":"Tiger","wolf":"Wolf","fox":"Fox",
    "elephant":"Elephant","giraffe":"Giraffe","zebra":"Zebra",
    "panda":"Giant_panda","koala":"Koala","eagle":"Eagle",
    "owl":"Owl","dolphin":"Dolphin","bear":"Bear","cat":"Cat","dog":"Dog"
}
FETCH_UA = {"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

ANIMAL_META = {
    "lion": ("أسد", "Lion", "Lion", "roar"),
    "tiger": ("نمر", "Tiger", "Tigre", "roar"),
    "wolf": ("ذئب", "Wolf", "Loup", "howl"),
    "fox": ("ثعلب", "Fox", "Renard", "bark"),
    "elephant": ("فيل", "Elephant", "Éléphant", "trumpet"),
    "giraffe": ("زرافة", "Giraffe", "Girafe", "hum"),
    "zebra": ("حمار وحشي", "Zebra", "Zèbre", "neigh"),
    "panda": ("باندا", "Panda", "Panda", "chirp"),
    "koala": ("كوالا", "Koala", "Koala", "grunt"),
    "eagle": ("نسر", "Eagle", "Aigle", "screech"),
    "owl": ("بومة", "Owl", "Hibou", "hoot"),
    "dolphin": ("دولفين", "Dolphin", "Dauphin", "click"),
    "bear": ("دب", "Bear", "Ours", "roar"),
    "cat": ("قطة", "Cat", "Chat", "meow"),
    "dog": ("كلب", "Dog", "Chien", "bark")
}

COLORS_DATA = [
    {"id": "red", "ar": "أحمر", "en": "Red", "fr": "Rouge", "hex": "#ef4444", "emoji": "🍎", "hint": "أحمر زي التفاحة"},
    {"id": "blue", "ar": "أزرق", "en": "Blue", "fr": "Bleu", "hex": "#3b82f6", "emoji": "🐳", "hint": "أزرق زي البحر"},
    {"id": "yellow", "ar": "أصفر", "en": "Yellow", "fr": "Jaune", "hex": "#eab308", "emoji": "🍌", "hint": "أصفر زي الموزة"},
    {"id": "green", "ar": "أخضر", "en": "Green", "fr": "Vert", "hex": "#22c55e", "emoji": "🐢", "hint": "أخضر زي الشجرة"},
    {"id": "orange", "ar": "برتقالي", "en": "Orange", "fr": "Orange", "hex": "#f97316", "emoji": "🍊", "hint": "برتقالي زي البرتقالة"},
    {"id": "purple", "ar": "بنفسجي", "en": "Purple", "fr": "Violet", "hex": "#a855f7", "emoji": "🍇", "hint": "بنفسجي زي العنب"},
    {"id": "pink", "ar": "وردي", "en": "Pink", "fr": "Rose", "hex": "#ec4899", "emoji": "🦩", "hint": "وردي زي الفلامنجو"},
    {"id": "brown", "ar": "بني", "en": "Brown", "fr": "Marron", "hex": "#92400e", "emoji": "🧸", "hint": "بني زي الدبدوب"}
]

NUMBERS_DATA = [
    {"num": 1, "ar": "واحد", "en": "One", "fr": "Un", "emoji": "🍎", "combo": "تفاحة واحدة"},
    {"num": 2, "ar": "اتنين", "en": "Two", "fr": "Deux", "emoji": "🐥", "combo": "اتنين كتكوت"},
    {"num": 3, "ar": "تلاتة", "en": "Three", "fr": "Trois", "emoji": "🐸", "combo": "تلات ضفادع"},
    {"num": 4, "ar": "أربعة", "en": "Four", "fr": "Quatre", "emoji": "🐟", "combo": "أربع سمكات"},
    {"num": 5, "ar": "خمسة", "en": "Five", "fr": "Cinq", "emoji": "🍊", "combo": "خمس برتقالات"},
    {"num": 6, "ar": "ستة", "en": "Six", "fr": "Six", "emoji": "🍇", "combo": "ست عنبات"},
    {"num": 7, "ar": "سبعة", "en": "Seven", "fr": "Sept", "emoji": "🌸", "combo": "سبع وردات"},
    {"num": 8, "ar": "تمانية", "en": "Eight", "fr": "Huit", "emoji": "🍓", "combo": "تمان فراولات"},
    {"num": 9, "ar": "تسعة", "en": "Nine", "fr": "Neuf", "emoji": "⭐", "combo": "تسع نجوم"},
    {"num": 10, "ar": "عشرة", "en": "Ten", "fr": "Dix", "emoji": "🍏", "combo": "عشر تفاحات"}
]

BODY_DATA = [
    {"id": "eye", "ar": "عين", "en": "Eye", "fr": "Œil", "emoji": "👁️", "desc": "دي عينينا اللي بنشوف بيها"},
    {"id": "nose", "ar": "أنف", "en": "Nose", "fr": "Nez", "emoji": "👃", "desc": "ده أنفنا اللي بنشم بيه"},
    {"id": "mouth", "ar": "فم", "en": "Mouth", "fr": "Bouche", "emoji": "👄", "desc": "ده فمنا اللي بناكل بيه"},
    {"id": "ear", "ar": "أذن", "en": "Ear", "fr": "Oreille", "emoji": "👂", "desc": "دي أذننا اللي بنسمع بيها"},
    {"id": "hand", "ar": "يد", "en": "Hand", "fr": "Main", "emoji": "✋", "desc": "دي إيدينا اللي بنسلم بيها"},
    {"id": "foot", "ar": "قدم", "en": "Foot", "fr": "Pied", "emoji": "🦶", "desc": "دي رجلينا اللي بنمشي بيها"},
    {"id": "tooth", "ar": "أسنان", "en": "Teeth", "fr": "Dents", "emoji": "🦷", "desc": "دي أسناننا اللي بنغسلها"},
    {"id": "heart", "ar": "قلب", "en": "Heart", "fr": "Cœur", "emoji": "❤️", "desc": "ده قلبنا اللي بيحب ماما وبابا"}
]

SHAPES_DATA = [
    {"id": "circle",    "ar": "دائرة",   "color": "#e63946"},
    {"id": "square",    "ar": "مربع",    "color": "#1d70b8"},
    {"id": "triangle",  "ar": "مثلث",    "color": "#2a9d8f"},
    {"id": "star",      "ar": "نجمة",    "color": "#ffd60a"},
    {"id": "heart",     "ar": "قلب",     "color": "#ff70a6"},
    {"id": "rectangle", "ar": "مستطيل",  "color": "#f77f00"},
    {"id": "diamond",   "ar": "معين",    "color": "#9b5de5"},
    {"id": "hexagon",   "ar": "سداسي",   "color": "#92400e"},
]

ENCOURAGEMENTS = [
    {"key": "enc_bravo", "cat": "تشجيع", "ar": "برافو عليكي يا حبيبتي!", "en": "Bravo!", "fr": "Bravo!"},
    {"key": "enc_smart", "cat": "تشجيع", "ar": "شاطرة جداً يا بطلة!", "en": "So smart!", "fr": "Très bien!"},
    {"key": "enc_try", "cat": "تشجيع", "ar": "قربتي خالص، جربي تاني!", "en": "Try again!", "fr": "Essaie encore!"}
]


ARABIC_LETTERS = [
    ("alif", "أ"), ("ba", "ب"), ("ta", "ت"), ("tha", "ث"),
    ("jim", "ج"), ("ha", "ح"), ("kha", "خ"), ("dal", "د"),
    ("dhal", "ذ"), ("ra", "ر"), ("zay", "ز"), ("sin", "س"),
    ("shin", "ش"), ("sad", "ص"), ("dad", "ض"), ("taa", "ط"),
    ("dhaa", "ظ"), ("ain", "ع"), ("ghain", "غ"), ("fa", "ف"),
    ("qaf", "ق"), ("kaf", "ك"), ("lam", "ل"), ("mim", "م"),
    ("nun", "ن"), ("ha2", "ه"), ("waw", "و"), ("ya", "ي")
]


def get_all_questions():
    """قائمة الأسئلة الكاملة اللي محتاجين تسجيلها (~159 سؤال)."""
    qs = []
    # تشجيع
    for enc in ENCOURAGEMENTS:
        qs.append({"key": enc["key"], "category": "encouragement",
                   "category_ar": "تشجيع", "subgroup": None,
                   "subgroup_ar": None, "text_ar": enc["ar"]})
    # حيوانات (5 أسئلة لكل حيوان)
    for aid, meta in ANIMAL_META.items():
        ar = meta[0]
        for qtype, text in [
            ("where", f"أين {ar}؟"),
            ("what", f"إيه ده؟ (صورة {ar})"),
            ("color", f"إيه لون {ar}؟"),
            ("home", f"فين يعيش {ar}؟"),
            ("sound", f"إيه صوت {ar}؟"),
        ]:
            qs.append({"key": f"ani_{aid}_{qtype}", "category": "animals",
                       "category_ar": "حيوانات", "subgroup": aid,
                       "subgroup_ar": ar, "text_ar": text})
    # ألوان
    for c in COLORS_DATA:
        for qtype, text in [
            ("where", f"أين اللون {c['ar']}؟"),
            ("what", f"إيه ده؟ (لون {c['ar']})"),
        ]:
            qs.append({"key": f"col_{c['id']}_{qtype}", "category": "colors",
                       "category_ar": "ألوان", "subgroup": c["id"],
                       "subgroup_ar": c["ar"], "text_ar": text})
    # أرقام
    for n in NUMBERS_DATA:
        for qtype, text in [
            ("howmany", f"كم عدد الأشياء؟ (العدد {n['ar']})"),
            ("where", f"أين الرقم {n['ar']}؟"),
        ]:
            qs.append({"key": f"num_{n['num']}_{qtype}", "category": "numbers",
                       "category_ar": "أرقام", "subgroup": str(n["num"]),
                       "subgroup_ar": n["ar"], "text_ar": text})
    # جسم
    for b in BODY_DATA:
        for qtype, text in [
            ("where", f"أين {b['ar']}؟"),
            ("what", f"إيه ده؟ ({b['ar']})"),
        ]:
            qs.append({"key": f"body_{b['id']}_{qtype}", "category": "body",
                       "category_ar": "جسم الإنسان", "subgroup": b["id"],
                       "subgroup_ar": b["ar"], "text_ar": text})
    # أشكال
    for s in SHAPES_DATA:
        qs.append({"key": f"shp_{s['id']}_where", "category": "shapes",
                   "category_ar": "أشكال", "subgroup": s["id"],
                   "subgroup_ar": s["ar"], "text_ar": f"أين {s['ar']}؟"})
    # أسئلة "فين راح؟"
    qs.append({"key": "dis_look", "category": "disappear", "category_ar": "لعبة فين راح؟", "subgroup": None, "subgroup_ar": None, "text_ar": "بصي كويس"})
    qs.append({"key": "dis_question", "category": "disappear", "category_ar": "لعبة فين راح؟", "subgroup": None, "subgroup_ar": None, "text_ar": "مين مش موجود؟"})
    # أسئلة "مين المختلف؟"
    qs.append({"key": "odd_question", "category": "odd", "category_ar": "لعبة مين المختلف؟", "subgroup": None, "subgroup_ar": None, "text_ar": "مين المختلف؟"})
    # حروف
    for lid, letter in ARABIC_LETTERS:
        qs.append({"key": f"let_{lid}_where", "category": "letters",
                   "category_ar": "حروف عربية", "subgroup": lid,
                   "subgroup_ar": letter, "text_ar": f"أين حرف {letter}؟"})
    return qs

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS progress (game_id TEXT PRIMARY KEY, completed INTEGER DEFAULT 0, total INTEGER DEFAULT 10, stars INTEGER DEFAULT 0)")
        c.execute("CREATE TABLE IF NOT EXISTS voices (item_key TEXT PRIMARY KEY, file_path TEXT)")
        cols = [r[1] for r in c.execute("PRAGMA table_info(voices)").fetchall()]
        for col_name, col_type in [
            ("voice_type", "TEXT"),
            ("speaker", "TEXT"),
            ("duration_ms", "INTEGER DEFAULT 0"),
            ("created_at", "TIMESTAMP"),
        ]:
            if col_name not in cols:
                c.execute(f"ALTER TABLE voices ADD COLUMN {col_name} {col_type}")
        games = [("animals", 0, 15, 0), ("colors", 0, 8, 0), ("numbers", 0, 10, 0), ("body", 0, 8, 0)]
        for g in games:
            c.execute("INSERT OR IGNORE INTO progress (game_id, completed, total, stars) VALUES (?, ?, ?, ?)", g)
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('setup_done', '0')")
        conn.commit()

def get_animals_list():
    groups = {}
    for fname in sorted(os.listdir(ANIMALS_DIR)):
        if fname.lower().endswith((".webp", ".jpg", ".jpeg", ".png")):
            eng = fname.split("_")[0].lower()
            groups.setdefault(eng, []).append(fname)

    animals = []
    for eng, files in groups.items():
        chosen = random.choice(files)
        ar, en, fr, snd = ANIMAL_META.get(eng, (eng, eng.capitalize(), eng.capitalize(), "roar"))
        animals.append({
            "id": eng, "ar": ar, "en": en, "fr": fr,
            "sound": snd, "img": f"/static/animals/{chosen}",
            "all_imgs": [f"/static/animals/{f}" for f in files]
        })
    return animals

def get_dictionary():
    items = list(ENCOURAGEMENTS)
    for a in get_animals_list():
        items.append({"key": f"ani_{a['id']}", "cat": "حيوانات", "ar": a["ar"], "en": a["en"], "fr": a["fr"]})
    for c in COLORS_DATA:
        items.append({"key": f"col_{c['id']}", "cat": "ألوان", "ar": c["ar"], "en": c["en"], "fr": c["fr"]})
    for n in NUMBERS_DATA:
        items.append({"key": f"num_{n['num']}", "cat": "أرقام", "ar": f"{n['ar']} - {n['combo']}", "en": n["en"], "fr": n["fr"]})
    for b in BODY_DATA:
        items.append({"key": f"body_{b['id']}", "cat": "جسم الإنسان", "ar": f"{b['ar']} ({b['desc']})", "en": b["en"], "fr": b["fr"]})
    for s in SHAPES_DATA:
        items.append({"key": f"shp_{s['id']}_where", "cat": "أشكال", "ar": s["ar"], "en": s["id"], "fr": s["id"]})
    for lid, letter in ARABIC_LETTERS:
        items.append({"key": f"let_{lid}_where", "cat": "حروف عربية", "ar": letter, "en": lid, "fr": lid})
    items.append({"key": "dis_look", "cat": "فين راح؟", "ar": "بصي كويس", "en": "Look", "fr": "Regarde"})
    items.append({"key": "dis_question", "cat": "فين راح؟", "ar": "مين مش موجود؟", "en": "Who is missing?", "fr": "Qui manque?"})
    items.append({"key": "odd_question", "cat": "مين المختلف؟", "ar": "مين المختلف؟", "en": "Odd one out?", "fr": "Différent?"})
    return items


def _render_game():
    """يرندر game.html مع كل المتغيرات المطلوبة."""
    animals = get_animals_list()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT item_key, file_path FROM voices").fetchall()
    voices = {k: p for k, p in rows}
    return render_template(
        "game.html",
        animals=animals,
        colors=COLORS_DATA,
        numbers=NUMBERS_DATA,
        body_parts=BODY_DATA,
        letters=ARABIC_LETTERS,
        shapes=SHAPES_DATA,
        voices=voices
    )


@app.route("/")
@app.route("/game")
def index():
    """الصفحة الرئيسية: اللعبة مباشرة."""
    return _render_game()


@app.route("/admin")
def admin():
    """لوحة الإدارة الرئيسية."""
    return render_template("admin_dashboard.html")


@app.route("/admin/images")
def admin_images():
    """جلب الصور."""
    animals = get_animals_list()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("UPDATE progress SET total=? WHERE game_id='animals'", (max(1, len(animals)),))
        conn.commit()
        setup_done = conn.execute("SELECT value FROM settings WHERE key='setup_done'").fetchone()["value"]
        prog_rows = conn.execute("SELECT * FROM progress").fetchall()
        voices_rows = conn.execute("SELECT * FROM voices").fetchall()

    progress = {r["game_id"]: dict(r) for r in prog_rows}
    recorded_voices = {r["item_key"]: r["file_path"] for r in voices_rows}

    return render_template(
        "index.html",
        setup_done=setup_done,
        progress=progress,
        animals=animals,
        colors=COLORS_DATA,
        numbers=NUMBERS_DATA,
        body_parts=BODY_DATA,
        dictionary=get_dictionary(),
        recorded_voices=recorded_voices
    )


@app.route("/admin/stats")
def admin_stats():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        progress = [dict(r) for r in conn.execute("SELECT * FROM progress").fetchall()]
        voices_count = conn.execute("SELECT COUNT(*) FROM voices").fetchone()[0]
    total_q = len(get_all_questions())
    try:
        animal_imgs = len([f for f in os.listdir(ANIMALS_DIR) if f.lower().endswith(('.webp','.jpg','.jpeg','.png'))])
    except Exception:
        animal_imgs = 0
    total_stars = sum(p['stars'] for p in progress)
    total_completed = sum(p['completed'] for p in progress)
    return render_template("admin_stats.html",
        progress=progress, voices_count=voices_count,
        total_questions=total_q, animal_images=animal_imgs,
        total_stars=total_stars, total_completed=total_completed)


@app.route("/api/progress/clear", methods=["POST"])
def api_progress_clear():
    data = request.get_json(silent=True) or {}
    game_id = data.get("game_id")
    with sqlite3.connect(DB_PATH) as conn:
        if game_id:
            conn.execute("UPDATE progress SET completed=0, stars=0 WHERE game_id=?", (game_id,))
        else:
            conn.execute("UPDATE progress SET completed=0, stars=0")
        conn.commit()
    return jsonify({"status": "success"})


@app.route("/api/recordings/clear", methods=["POST"])
def api_recordings_clear():
    removed = 0
    if os.path.exists(VOICES_DIR):
        for f in os.listdir(VOICES_DIR):
            try:
                os.remove(os.path.join(VOICES_DIR, f))
                removed += 1
            except Exception:
                pass
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM voices")
        conn.commit()
    return jsonify({"status": "success", "removed": removed})



def _fetch_wiki_image(animal):
    """جلب صورة من Wikipedia REST API."""
    title = WIKI_MAP.get(animal, animal.capitalize())
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}",
            headers=FETCH_UA, timeout=15)
        if r.status_code != 200:
            return None
        d = r.json()
        url = (d.get("originalimage") or {}).get("source") or (d.get("thumbnail") or {}).get("source")
        if not url:
            return None
        img = requests.get(url, headers=FETCH_UA, timeout=20, allow_redirects=True)
        if img.status_code == 200 and len(img.content) > 5000:
            return img.content
    except Exception:
        pass
    return None


def _save_square_webp(data, out_path):
    """يحفظ الصورة كمربع 1024x1024 بصيغة webp."""
    img = Image.open(io.BytesIO(data)).convert("RGB")
    w, h = img.size
    s = min(w, h)
    l, t = (w - s) // 2, (h - s) // 2
    img = img.crop((l, t, l + s, t + s)).resize((1024, 1024), Image.LANCZOS)
    img.save(out_path, "WEBP", quality=85)


@app.route("/api/fetch", methods=["POST"])
def api_fetch():
    data = request.get_json(silent=True) or {}
    animal = (data.get("animal") or "").strip().lower()
    try:
        count = int(data.get("count", 6))
    except (TypeError, ValueError):
        count = 6
    count = max(1, min(count, 10))

    if not animal:
        return jsonify({"status": "error", "message": "اسم الحيوان مطلوب"})

    targets = DEFAULT_ANIMALS if animal == "all_default" else [animal]
    added = 0

    for target in targets:
        existing = [f for f in os.listdir(ANIMALS_DIR)
                    if f.startswith(f"{target}_") and f.lower().endswith((".webp",".jpg",".jpeg",".png"))]
        start_idx = len(existing) + 1
        for i in range(count):
            time.sleep(0.3)
            content = _fetch_wiki_image(target)
            if not content:
                continue
            out = os.path.join(ANIMALS_DIR, f"{target}_{start_idx + i}.webp")
            try:
                _save_square_webp(content, out)
                added += 1
            except Exception:
                pass

    if added == 0:
        return jsonify({"status": "error",
                        "message": "لم نتمكن من جلب أي صورة. تحقق من الاتصال أو الاسم."})
    return jsonify({"status": "success", "added": added})

@app.route("/api/save_voice", methods=["POST"])
def save_voice():
    item_key = request.form.get("key")
    audio = request.files.get("audio")
    if not item_key or not audio:
        return jsonify({"status": "error"}), 400
    ext = request.form.get("ext", "webm")
    if ext not in ("webm", "mp4", "ogg", "wav"):
        ext = "webm"
    filename = f"{item_key}.{ext}"
    filepath = os.path.join(VOICES_DIR, filename)
    audio.save(filepath)
    web_path = f"/static/voices/{filename}"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR REPLACE INTO voices (item_key, file_path) VALUES (?, ?)", (item_key, web_path))
        conn.commit()
    return jsonify({"status": "success", "path": web_path})

@app.route("/api/update_progress", methods=["POST"])
def update_progress():
    data = request.json
    game_id = data.get("game_id")
    add_star = int(data.get("stars", 1))
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM progress WHERE game_id=?", (game_id,)).fetchone()
        if row:
            new_comp = min(row["total"], row["completed"] + 1)
            new_stars = row["stars"] + add_star
            conn.execute("UPDATE progress SET completed=?, stars=? WHERE game_id=?", (new_comp, new_stars, game_id))
        else:
            conn.execute("INSERT INTO progress (game_id, completed, total, stars) VALUES (?, 1, 5, ?)", (game_id, add_star))
        conn.commit()
        all_rows = conn.execute("SELECT * FROM progress").fetchall()
    return jsonify({"status": "success", "progress": {r["game_id"]: dict(r) for r in all_rows}})

@app.route("/api/complete_setup", methods=["POST"])
def complete_setup():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE settings SET value='1' WHERE key='setup_done'")
        conn.commit()
    return jsonify({"status": "success"})

@app.route("/favicon.ico")
def favicon():
    return "", 204

init_db()

@app.route("/recordings")
def recordings():
    return render_template("recordings.html")


@app.route("/api/voices/list")
def api_voices_list():
    questions = get_all_questions()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM voices").fetchall()
    recorded = {r["item_key"]: dict(r) for r in rows}
    for q in questions:
        if q["key"] in recorded:
            q["recorded"] = True
            q["path"] = recorded[q["key"]]["file_path"]
            q["duration_ms"] = recorded[q["key"]].get("duration_ms") or 0
        else:
            q["recorded"] = False
            q["path"] = None
            q["duration_ms"] = 0
    stats = {}
    for q in questions:
        cat = q["category"]
        if cat not in stats:
            stats[cat] = {"category_ar": q["category_ar"], "total": 0, "done": 0}
        stats[cat]["total"] += 1
        if q["recorded"]:
            stats[cat]["done"] += 1
    return jsonify({"questions": questions, "stats": stats,
                    "total": len(questions),
                    "recorded": sum(1 for q in questions if q["recorded"])})


@app.route("/api/voices/save", methods=["POST"])
def api_voices_save():
    item_key = request.form.get("key")
    speaker = request.form.get("speaker", "dad")
    try:
        duration_ms = int(request.form.get("duration_ms", 0))
    except (TypeError, ValueError):
        duration_ms = 0
    audio = request.files.get("audio")
    if not item_key or not audio:
        return jsonify({"status": "error", "message": "بيانات ناقصة"}), 400
    ext = request.form.get("ext", "webm")
    if ext not in ("webm", "mp4", "ogg", "wav"):
        ext = "webm"
    filename = f"{item_key}.{ext}"
    filepath = os.path.join(VOICES_DIR, filename)
    audio.save(filepath)
    web_path = f"/static/voices/{filename}"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO voices "
            "(item_key, file_path, voice_type, speaker, duration_ms, created_at) "
            "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (item_key, web_path, "question", speaker, duration_ms))
        conn.commit()
    return jsonify({"status": "success", "path": web_path})


@app.route("/api/voices/delete/<path:item_key>", methods=["DELETE"])
def api_voices_delete(item_key):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT file_path FROM voices WHERE item_key=?", (item_key,)).fetchone()
        if not row:
            return jsonify({"status": "error", "message": "غير موجود"}), 404
        rel_path = row[0]
        conn.execute("DELETE FROM voices WHERE item_key=?", (item_key,))
        conn.commit()
    full = os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path.lstrip("/"))
    if os.path.exists(full):
        try:
            os.remove(full)
        except OSError:
            pass
    return jsonify({"status": "success"})


@app.route("/api/voices/get/<path:item_key>")
def api_voices_get(item_key):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT file_path FROM voices WHERE item_key=?", (item_key,)).fetchone()
    if row:
        return jsonify({"found": True, "path": row[0]})
    return jsonify({"found": False})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
