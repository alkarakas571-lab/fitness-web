import os
import html
import re

from dotenv import load_dotenv
load_dotenv()
from datetime import date
from io import BytesIO

from supabase import create_client, Client
from flask import Flask, request, redirect, url_for, send_file, session, jsonify

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("Bitte Pillow installieren: sudo apt install python3-pil python3-pil.imagetk")


APP_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = APP_DIR

BASE_IMAGE_NAME = "base_front.png"

LAYER_FILES = {
    "schulter_vorne": "schulter_vorne2.png",
    "schulter_hinten": "schulter_hinten2.png",
    "brust_vorne": "brust_vorne2.png",
    "abs_vorne": "abs_vorne2.png",
    "tricep_vorne": "tricep_vorne2.png",
    "tricep_hinten": "tricep_hinten2.png",
    "bicep_vorne": "bicep_vorne2.png",
    "lat_vorne": "lat_vorne.png2",
    "lat_hinten": "lat_hinten2.png",
    "nacken_vorne": "nacken_vorne2.png",
    "nacken_hinten": "nacken_hinten2.png",
    "oberschenkel_vorne": "oberschenkel_vorne2.png",
    "oberschenkel_hinten": "oberschenkel_hinten2.png",
    "po_hinten": "po_hinten2.png",
    "waden_vorne": "waden_vorne2.png",
    "waden_hinten": "waden_hinten2.png",
    "unterarm_vorne": "unterarm_vorne2.png",
    "unterarm_hinten": "unterarm_hinten2.png",
    "rhomboid_hinten": "rhomboid_hinten2.png",
    "ruckenstrecker_hinten": "ruckenstrecker_hinten2.png",
    "schienbeinmuskel_vorne": "schienbeinmuskel_vorne2.png",
    "sideabs_vorne": "sideabs_vorne2.png",
    "sideabs_hinten": "sideabs_hinten2.png",
    "trapez_hinten": "trapez_hinten2.png",
}

PLAN_DATA = {
    "Montag": [
        "🔵 SCHULTERN, BRUST, BIZEPS & BAUCH",
        "1. CAT COW (Warm-up) | 5 Runden",
        "2. DECLINE PRESS (Stuhl) | 3 x 12",
        "3. FRONT RAISES (Vorn) | 3 x 15",
        "4. SIDE RAISES (Seite) | 3 x 15",
        "5. SHOULDER PRESS | 3 x 12",
        "6. TRICEPS | 3 x 12",
        "7. CHEST PRESS / DIPS | 3 x 12",
        "8. RUSSIAN TWIST | 3 x 20",
        "9. SIDE BENDS | 3 x 15",
    ],
    "Dienstag": [
        "🟢 BEINE & CORE",
        "1. CAT COW (Warm-up) | 5 Runden",
        "2. STEP UP | 3 Bahnen",
        "3. HIP THRUSTS | 3 x 12",
        "4. LEG CURLS | 3 x 10",
        "5. WADENHEBEN | 3 x 15",
        "6. CRUNCH | 3 x 20",
        "7. LEG RAISES | 3 x 15",
    ],
    "Mittwoch": [
        "🔴 RÜCKEN & BIZEPS",
        "1. CAT COW (Warm-up) | 5 Runden",
        "2. RUDERN (Schrägbank)",
        "3. STANDING ROWS",
        "4. BICEP / HAMMER CURLS",
        "5. RUSSIAN TWIST",
        "6. SIDE BENDS",
    ],
    "Donnerstag": [
        "🟠 LOWER BACK & CORE",
        "1. CAT COW (Warm-up) | 5 Runden",
        "2. DEADLIFT",
        "3. BACK EXTENSION",
        "4. CRUNCH | 3 x 20",
        "5. LEG RAISES | 3 x 15",
    ],
}

DAY_TO_LAYERS = {
    "Montag": [
        "schulter_vorne",
        "schulter_hinten",
        "brust_vorne",
        "tricep_vorne",
        "tricep_hinten",
        "sideabs_vorne",
        "sideabs_hinten",
    ],
    "Dienstag": [
        "oberschenkel_vorne",
        "oberschenkel_hinten",
        "po_hinten",
        "waden_vorne",
        "waden_hinten",
        "abs_vorne",
    ],
    "Mittwoch": [
        "lat_hinten",
        "rhomboid_hinten",
        "bicep_vorne",
        "trapez_hinten",
        "unterarm_vorne",
        "unterarm_hinten",
    ],
    "Donnerstag": [
        "ruckenstrecker_hinten",
        "abs_vorne",
        "sideabs_vorne",
        "sideabs_hinten",
    ],
}

UEBUNGEN_A_Z = {
    "A": {
        "name": "Kniebeugen (Squats)",
        "anleitung": (
            "KORREKTE AUSFÜHRUNG:\n\n"
            "1. Füße schulterbreit, Zehen leicht nach außen.\n"
            "2. Rücken gerade, Brust raus, Kopf in Verlängerung.\n"
            "3. Beuge die Knie, Po nach hinten schieben.\n"
            "4. Unterkörper senken, bis Oberschenkel etwa parallel zum Boden.\n"
            "5. Kontrolliert wieder hochdrücken."
        ),
    },
    "B": {
        "name": "Liegestütze (Push-Ups)",
        "anleitung": (
            "KORREKTE AUSFÜHRUNG:\n\n"
            "1. Körper in einer Linie halten.\n"
            "2. Hände schulterbreit unter den Schultern.\n"
            "3. Brust Richtung Boden senken.\n"
            "4. Wieder hochdrücken, ohne ins Hohlkreuz zu gehen."
        ),
    },
    "C": {
        "name": "Crunches",
        "anleitung": (
            "KORREKTE AUSFÜHRUNG:\n\n"
            "1. Auf dem Rücken liegen, Knie gebeugt.\n"
            "2. Hände locker hinter dem Kopf.\n"
            "3. Oberkörper leicht anheben.\n"
            "4. Bauchspannung halten."
        ),
    },
    "D": {
        "name": "Plank",
        "anleitung": (
            "KORREKTE AUSFÜHRUNG:\n\n"
            "1. Auf die Unterarme stützen.\n"
            "2. Ellbogen unter den Schultern.\n"
            "3. Körper gerade halten.\n"
            "4. Bauch und Po anspannen."
        ),
    },
}


def get_week_key() -> str:
    today = date.today()
    iso_year, iso_week, _ = today.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def default_status():
    return {
        "week_key": get_week_key(),
        "completed_days": {},
        "active_layers": [],
    }


def get_current_user_id():
    return session.get("user_id")


def create_profile_for_user(user_id, email, display_name=""):
    supabase.table("profiles").upsert({
        "id": user_id,
        "email": email,
        "display_name": display_name or email.split("@")[0]
    }).execute()


def create_training_status_for_user(user_id):
    existing = supabase.table("training_status").select("user_id").eq("user_id", user_id).execute()
    if not existing.data:
        supabase.table("training_status").insert({
            "user_id": user_id,
            "week_key": get_week_key(),
            "completed_days": {},
            "active_layers": []
        }).execute()


def ensure_workout_settings_for_user(user_id):
    existing = supabase.table("workout_settings").select("user_id").eq("user_id", user_id).execute()
    if not existing.data:
        supabase.table("workout_settings").insert({
            "user_id": user_id,
            "exercise_memory": {}
        }).execute()


def load_user_status():
    user_id = get_current_user_id()

    if not user_id:
        return default_status()

    result = supabase.table("training_status").select("*").eq("user_id", user_id).execute()

    if not result.data:
        data = default_status()
        supabase.table("training_status").insert({
            "user_id": user_id,
            "week_key": data["week_key"],
            "completed_days": data["completed_days"],
            "active_layers": data["active_layers"]
        }).execute()
        return data

    row = result.data[0]

    data = {
        "week_key": row.get("week_key") or get_week_key(),
        "completed_days": row.get("completed_days") or {},
        "active_layers": row.get("active_layers") or [],
    }

    if data["week_key"] != get_week_key():
        data = default_status()
        save_user_status(data)

    return data


def save_user_status(data):
    user_id = get_current_user_id()

    if not user_id:
        return

    data["week_key"] = get_week_key()

    supabase.table("training_status").upsert({
        "user_id": user_id,
        "week_key": data["week_key"],
        "completed_days": data["completed_days"],
        "active_layers": data["active_layers"]
    }).execute()


def parse_default_rounds(line: str) -> int:
    match = re.search(r"\|\s*(\d+)\s*(Runden|Bahnen|x)", line, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r"\b(\d+)\s*x\s*\d+\b", line, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0


def clean_exercise_name(line: str) -> str:
    text = re.sub(r"^\d+\.\s*", "", line).strip()
    if "|" in text:
        text = text.split("|", 1)[0].strip()
    return text


def get_training_header(tag: str) -> str:
    lines = PLAN_DATA.get(tag, [])
    if lines:
        return lines[0]
    return tag


def get_training_exercises(tag: str):
    lines = PLAN_DATA.get(tag, [])
    exercises = []

    for idx, line in enumerate(lines):
        if idx == 0:
            continue
        exercises.append({
            "id": f"ex_{idx}",
            "label": line,
            "name": clean_exercise_name(line),
            "default_rounds": parse_default_rounds(line),
        })

    return exercises


def get_ordered_training_exercises(tag: str):
    exercises = get_training_exercises(tag)
    memory = load_exercise_memory()
    tag_memory = memory.get(tag, {}) if isinstance(memory, dict) else {}
    saved_order = tag_memory.get("__order__", [])

    if not isinstance(saved_order, list) or not saved_order:
        return exercises

    by_id = {exercise["id"]: exercise for exercise in exercises}
    ordered = [by_id[ex_id] for ex_id in saved_order if ex_id in by_id]

    for exercise in exercises:
        if exercise["id"] not in saved_order:
            ordered.append(exercise)

    return ordered


def load_exercise_memory():
    user_id = get_current_user_id()
    if not user_id:
        return {}

    ensure_workout_settings_for_user(user_id)
    result = supabase.table("workout_settings").select("exercise_memory").eq("user_id", user_id).execute()

    if not result.data:
        return {}

    memory = result.data[0].get("exercise_memory") or {}
    if isinstance(memory, dict):
        return memory
    return {}


def save_exercise_memory(memory: dict):
    user_id = get_current_user_id()
    if not user_id:
        return

    ensure_workout_settings_for_user(user_id)
    supabase.table("workout_settings").upsert({
        "user_id": user_id,
        "exercise_memory": memory
    }).execute()


def get_saved_values_for_tag(tag: str):
    memory = load_exercise_memory()
    tag_memory = memory.get(tag, {})

    exercises = get_ordered_training_exercises(tag)
    result = {}

    for ex in exercises:
        item = tag_memory.get(ex["id"], {})
        sets = normalize_sets(item, ex["default_rounds"])
        result[ex["id"]] = {
            "sets": sets,
            "rounds": sets[0]["rounds"],
            "weight": sets[0]["weight"],
        }

    return result


def save_values_for_tag(tag: str, values: dict):
    memory = load_exercise_memory()
    tag_memory = memory.setdefault(tag, {})

    existing_order = tag_memory.get("__order__", [])
    valid_ids = [exercise["id"] for exercise in get_training_exercises(tag)]
    normalized_order = [ex_id for ex_id in existing_order if ex_id in valid_ids]
    for ex_id in valid_ids:
        if ex_id not in normalized_order:
            normalized_order.append(ex_id)
    tag_memory["__order__"] = normalized_order

    for exercise in get_training_exercises(tag):
        ex_id = exercise["id"]
        incoming = values.get(ex_id, {})
        sets = normalize_sets(incoming, exercise["default_rounds"])

        tag_memory[ex_id] = {
            "name": exercise["name"],
            "rounds": sets[0]["rounds"],
            "weight": sets[0]["weight"],
            "sets": sets,
        }

    memory[tag] = tag_memory
    save_exercise_memory(memory)


def save_order_for_tag(tag: str, exercise_ids: list):
    memory = load_exercise_memory()
    tag_memory = memory.setdefault(tag, {})
    valid_ids = [exercise["id"] for exercise in get_training_exercises(tag)]
    valid_set = set(valid_ids)

    cleaned = []
    for ex_id in exercise_ids:
        if ex_id in valid_set and ex_id not in cleaned:
            cleaned.append(ex_id)

    for ex_id in valid_ids:
        if ex_id not in cleaned:
            cleaned.append(ex_id)

    tag_memory["__order__"] = cleaned
    memory[tag] = tag_memory
    save_exercise_memory(memory)


def add_history_entry(tag: str, duration_seconds: int, values: dict):
    user_id = get_current_user_id()
    if not user_id:
        return

    exercises = []
    for exercise in get_training_exercises(tag):
        ex_id = exercise["id"]
        incoming = values.get(ex_id, {})
        sets = normalize_sets(incoming, exercise["default_rounds"])

        exercises.append({
            "id": ex_id,
            "name": exercise["name"],
            "label": exercise["label"],
            "rounds": sets[0]["rounds"],
            "weight": sets[0]["weight"],
            "sets": sets,
        })

    supabase.table("training_history").insert({
        "user_id": user_id,
        "category": "Trainingsverlauf",
        "training_day": tag,
        "title": get_training_header(tag),
        "training_date": date.today().isoformat(),
        "duration_seconds": max(0, int(duration_seconds)),
        "exercises": exercises
    }).execute()


def load_history_entries():
    user_id = get_current_user_id()
    if not user_id:
        return []

    result = (
        supabase.table("training_history")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return result.data or []


def load_history_entry(entry_id: int):
    user_id = get_current_user_id()
    if not user_id:
        return None

    result = (
        supabase.table("training_history")
        .select("*")
        .eq("user_id", user_id)
        .eq("id", entry_id)
        .limit(1)
        .execute()
    )

    if result.data:
        return result.data[0]
    return None


def format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    minutes = seconds // 60
    rest = seconds % 60
    return f"{minutes:02d}:{rest:02d}"


def format_weight(value) -> str:
    try:
        value = max(0.0, round(float(value), 1))
    except Exception:
        value = 0.0
    return f"{value:.1f}".replace(".", ",")


def normalize_sets(item: dict, default_rounds: int):
    if not isinstance(item, dict):
        item = {}

    raw_sets = item.get("sets")
    if not isinstance(raw_sets, list) or len(raw_sets) != 3:
        raw_sets = [
            {"rounds": item.get("rounds", default_rounds), "weight": item.get("weight", 0.0)},
            {"rounds": item.get("rounds", default_rounds), "weight": item.get("weight", 0.0)},
            {"rounds": item.get("rounds", default_rounds), "weight": item.get("weight", 0.0)},
        ]

    normalized = []
    for s in raw_sets[:3]:
        if not isinstance(s, dict):
            s = {}
        try:
            rounds = max(0, int(s.get("rounds", default_rounds)))
        except Exception:
            rounds = default_rounds
        try:
            weight = max(0.0, round(float(s.get("weight", 0.0)), 1))
        except Exception:
            weight = 0.0
        normalized.append({"rounds": rounds, "weight": weight})

    while len(normalized) < 3:
        normalized.append({"rounds": default_rounds, "weight": 0.0})

    return normalized


def create_fallback_body_image():
    img = Image.new("RGBA", (700, 700), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    body_fill = (225, 225, 225, 255)
    body_outline = (120, 120, 120, 255)

    draw.ellipse((290, 40, 410, 160), fill=body_fill, outline=body_outline, width=4)
    draw.rounded_rectangle((265, 160, 435, 390), radius=60, fill=body_fill, outline=body_outline, width=4)
    draw.rounded_rectangle((215, 180, 285, 380), radius=35, fill=body_fill, outline=body_outline, width=4)
    draw.rounded_rectangle((415, 180, 485, 380), radius=35, fill=body_fill, outline=body_outline, width=4)
    draw.rounded_rectangle((285, 385, 345, 645), radius=30, fill=body_fill, outline=body_outline, width=4)
    draw.rounded_rectangle((355, 385, 415, 645), radius=30, fill=body_fill, outline=body_outline, width=4)

    draw.text((235, 665), "Muskelstatus", fill=(90, 90, 90, 255))
    return img


def compose_body_image():
    base_path = os.path.join(ASSET_DIR, BASE_IMAGE_NAME)
    if os.path.exists(base_path):
        try:
            composed = Image.open(base_path).convert("RGBA")
        except Exception:
            composed = create_fallback_body_image()
    else:
        composed = create_fallback_body_image()

    status = load_user_status()
    active_layers = status.get("active_layers", [])

    for layer_name in active_layers:
        filename = LAYER_FILES.get(layer_name)
        if not filename:
            continue
        path = os.path.join(ASSET_DIR, filename)
        if not os.path.exists(path):
            continue
        try:
            layer_img = Image.open(path).convert("RGBA")
            if layer_img.size != composed.size:
                layer_img = layer_img.resize(composed.size)
            composed = Image.alpha_composite(composed, layer_img)
        except Exception:
            pass

    preview = composed.copy()
    preview.thumbnail((700, 700))

    buf = BytesIO()
    preview.save(buf, format="PNG")
    buf.seek(0)
    return buf


def html_page(title: str, content: str):
    return f"""
    <!doctype html>
    <html lang="de">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{title}</title>
        <style>
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f3f3f3;
                color: #222;
            }}
            .wrap {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            .top {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .layout {{
                display: grid;
                grid-template-columns: 1.7fr 1fr;
                gap: 20px;
            }}
            .card {{
                background: white;
                border-radius: 16px;
                padding: 20px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            }}
            h1, h2, h3 {{ margin-top: 0; }}
            .menu a, .menu button {{
                display: block;
                width: 100%;
                margin-bottom: 10px;
                text-decoration: none;
                text-align: center;
                border: none;
                border-radius: 12px;
                padding: 14px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }}
            .green {{ background: #4CAF50; color: white; }}
            .blue {{ background: #2196F3; color: white; }}
            .orange {{ background: #FF9800; color: white; }}
            .red {{ background: #FF5722; color: white; }}
            .gray {{ background: #607D8B; color: white; }}
            .darkred {{ background: #f44336; color: white; }}
            .status-ok {{
                color: #b00020;
                font-weight: bold;
            }}
            .status-open {{
                color: #333;
            }}
            select {{
                width: 100%;
                padding: 12px;
                border-radius: 12px;
                border: 1px solid #ccc;
                font-size: 16px;
                margin-bottom: 12px;
            }}
            img {{
                max-width: 100%;
                height: auto;
                display: block;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 12px;
            }}
            .muted {{
                color: #666;
            }}
            .listbox a {{
                display: block;
                padding: 12px;
                margin-bottom: 8px;
                background: #f7f7f7;
                border-radius: 10px;
                color: #111;
                text-decoration: none;
            }}
            pre {{
                white-space: pre-wrap;
                background: #fafafa;
                padding: 15px;
                border-radius: 12px;
                overflow-x: auto;
            }}
            ul {{
                padding-left: 20px;
            }}
            .center {{
                text-align: center;
            }}
            .loginbar {{
                margin-bottom: 18px;
                padding: 12px 14px;
                background: white;
                border-radius: 14px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);
                text-align: center;
            }}
            .loginbar a {{
                text-decoration: none;
                font-weight: bold;
                color: #2196F3;
                margin: 0 8px;
            }}
            .training-head {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 20px;
                margin-bottom: 18px;
            }}
            .timer-box {{
                background: white;
                border-radius: 12px;
                padding: 10px 14px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);
                min-width: 120px;
                text-align: center;
            }}
            .timer-value {{
                font-size: 24px;
                font-weight: bold;
            }}
            .exercise-block {{
                margin-bottom: 14px;
                background: #f7f7f7;
                border-radius: 12px;
                padding: 14px;
                overflow-x: auto;
                cursor: grab;
                transition: transform 0.12s ease, box-shadow 0.12s ease, background 0.12s ease;
            }}
            .exercise-block:active {{
                cursor: grabbing;
            }}
            .exercise-block.dragging {{
                opacity: 0.65;
                transform: scale(0.995);
                box-shadow: 0 10px 22px rgba(0,0,0,0.12);
            }}
            .exercise-block.drag-over {{
                background: #e8e8e8;
                outline: 2px dashed #7a7a7a;
                outline-offset: 1px;
            }}
            .exercise-row-head {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 12px;
                margin-bottom: 10px;
            }}
            .exercise-title {{
                font-weight: bold;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                flex: 1;
                margin-bottom: 0;
            }}
            .order-buttons {{
                display: inline-flex;
                gap: 6px;
                flex-shrink: 0;
                align-items: center;
            }}
            .drag-hint {{
                font-size: 12px;
                color: #555;
                font-weight: bold;
                background: #e1e1e1;
                border: 1px solid #a0a0a0;
                border-radius: 8px;
                padding: 6px 8px;
                user-select: none;
            }}
            .order-btn {{
                border: none;
                border-radius: 8px;
                width: 34px;
                height: 30px;
                background: #6a6a6a;
                color: white;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                line-height: 1;
            }}
            .order-btn:hover {{
                background: #585858;
            }}
            .exercise-controls {{
                display: flex;
                flex-wrap: nowrap;
                gap: 10px;
                align-items: center;
                min-width: fit-content;
            }}
            .control-group {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                background: #d6d6d6;
                border: 1px solid #8a8a8a;
                border-radius: 10px;
                padding: 6px 8px;
                white-space: nowrap;
            }}
            .mini-label {{
                font-weight: bold;
                font-size: 13px;
                color: #2f2f2f;
                min-width: auto;
            }}
            .set-badge {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background: #b8b8b8;
                border: 1px solid #8d8d8d;
                border-radius: 7px;
                padding: 4px 7px;
                font-size: 12px;
                font-weight: bold;
                color: #222;
                margin-right: 2px;
            }}
            .stepper {{
                display: inline-flex;
                align-items: center;
                gap: 5px;
            }}
            .stepper button {{
                border: none;
                border-radius: 8px;
                width: 28px;
                height: 28px;
                font-size: 16px;
                font-weight: bold;
                background: #5f5f5f;
                color: white;
                cursor: pointer;
                line-height: 1;
                padding: 0;
                opacity: 1;
            }}
            .stepper-value {{
                min-width: 44px;
                text-align: center;
                background: #ffffff;
                border-radius: 8px;
                padding: 6px 8px;
                border: 1px solid #8f8f8f;
                font-weight: bold;
                font-size: 14px;
                color: #222222;
            }}
            .stepper button:hover {{
                background: #4f4f4f;
            }}
            .stepper button:active {{
                transform: scale(0.98);
            }}

            .exercise-controls.disabled .control-group {{
                background: #d9d9d9;
                border-color: #b3b3b3;
            }}
            .exercise-controls.disabled .stepper-value {{
                background: #efefef;
                color: #5f5f5f;
            }}
            .exercise-controls.disabled button {{
                background: #9d9d9d;
                color: #ffffff;
                cursor: not-allowed;
            }}
            .save-note {{
                color: #666;
                font-size: 14px;
                margin-top: 8px;
            }}
            .history-folder {{
                display: block;
                padding: 14px;
                margin-bottom: 10px;
                background: #f7f7f7;
                border-radius: 12px;
                color: #111;
                text-decoration: none;
                font-weight: bold;
            }}
            .history-item {{
                display: block;
                padding: 14px;
                margin-bottom: 10px;
                background: #f7f7f7;
                border-radius: 12px;
                color: #111;
                text-decoration: none;
            }}
            @media (max-width: 900px) {{
                .layout {{
                    grid-template-columns: 1fr;
                }}
                .training-head {{
                    flex-direction: column;
                    align-items: stretch;
                }}
                .exercise-block {{
                    padding: 12px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="wrap">
            {content}
        </div>
    </body>
    </html>
    """


app = Flask(__name__)
app.secret_key = "irgendein_langes_geheimes_ding_12345"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route("/")
def home():
    status = load_user_status()
    tage = list(PLAN_DATA.keys())
    aktiver_tag = request.args.get("tag", tage[0])

    if aktiver_tag not in tage:
        aktiver_tag = tage[0]

    completed = status.get("completed_days", {})
    active = status.get("active_layers", [])

    if active:
        status_text = "Aktive Muskel-Layer diese Woche: " + ", ".join(active)
    else:
        status_text = "Diese Woche noch kein Training abgeschlossen. Körper ist auf Basisbild zurückgesetzt."

    day_options = "\n".join(
        f'<option value="{tag}" {"selected" if tag == aktiver_tag else ""}>{tag}</option>'
        for tag in tage
    )

    day_status_html = ""
    for tag in tage:
        if completed.get(tag):
            day_status_html += f'<div class="status-ok">{tag}: erledigt ✅</div>'
        else:
            day_status_html += f'<div class="status-open">{tag}: offen</div>'

    user_email = session.get("user_email")
    if user_email:
        login_box = f"""
        <div class="loginbar">
            Eingeloggt als: <b>{html.escape(user_email)}</b>
            <a href="/logout">Logout</a>
        </div>
        """
    else:
        login_box = """
        <div class="loginbar">
            <a href="/login">Login</a>
            <a href="/register">Registrieren</a>
        </div>
        """

    content = f"""
    {login_box}

    <div class="top">
        <h1>Fitness App mit Muskel-Layern 💪</h1>
        <p class="muted">Browser-Version</p>
    </div>

    <div class="layout">
        <div class="card">
            <h2>Dein Muskelstatus</h2>
            <img src="/body_image.png?v=1" alt="Muskelbild">
            <p class="center">{html.escape(status_text)}</p>
        </div>

        <div class="card menu">
            <h2>Menü</h2>

            <form method="get" action="/">
                <label for="tag"><b>Trainingstag auswählen</b></label>
                <select name="tag" id="tag" onchange="this.form.submit()">
                    {day_options}
                </select>
            </form>

            <a class="green" href="/training/{aktiver_tag}">Training starten</a>
            <a class="green" href="/uebungen">Übungen A–Z</a>
            <a class="red" href="/formanalyse">Formanalyse</a>
            <a class="orange" href="/ernaehrung">Ernährungsberater</a>
            <a class="gray" href="/history">History</a>
            <a class="gray" href="/reset_week" onclick="return confirm('Woche wirklich zurücksetzen?')">Woche zurücksetzen</a>

            <h3>Trainingsstatus</h3>
            {day_status_html}
        </div>
    </div>
    """
    return html_page("Fitness App", content)


@app.route("/body_image.png")
def body_image():
    return send_file(compose_body_image(), mimetype="image/png")


@app.route("/training/<tag>")
def training(tag):
    if tag not in PLAN_DATA:
        return redirect(url_for("home"))

    if "user_id" not in session:
        return redirect(url_for("login"))

    saved_values = get_saved_values_for_tag(tag)
    exercises = get_ordered_training_exercises(tag)

    exercise_html = []
    for exercise in exercises:
        saved = saved_values.get(exercise["id"], {})
        sets = saved.get("sets") or normalize_sets({}, exercise["default_rounds"])

        control_groups = []
        for set_index, set_values in enumerate(sets, start=1):
            set_rounds = set_values.get("rounds", exercise["default_rounds"])
            set_weight = set_values.get("weight", 0.0)
            control_groups.append(f"""
                <div class="control-group">
                    <div class="set-badge">Satz {set_index}</div>
                    <div class="mini-label">Runden</div>
                    <div class="stepper">
                        <button type="button" onclick="changeRounds('{exercise["id"]}', {set_index - 1}, -1)">-</button>
                        <div class="stepper-value" id="rounds_display_{exercise["id"]}_{set_index - 1}">{set_rounds}</div>
                        <button type="button" onclick="changeRounds('{exercise["id"]}', {set_index - 1}, 1)">+</button>
                    </div>
                    <div class="mini-label">Kilo</div>
                    <div class="stepper">
                        <button type="button" onclick="changeWeight('{exercise["id"]}', {set_index - 1}, -0.1)">-</button>
                        <div class="stepper-value" id="weight_display_{exercise["id"]}_{set_index - 1}">{format_weight(set_weight)}</div>
                        <button type="button" onclick="changeWeight('{exercise["id"]}', {set_index - 1}, 0.1)">+</button>
                    </div>
                </div>
            """)

        hidden_inputs = []
        for set_index, set_values in enumerate(sets, start=1):
            hidden_inputs.append(f'<input type="hidden" name="rounds_{exercise["id"]}_{set_index}" id="rounds_{exercise["id"]}_{set_index - 1}" value="{set_values.get("rounds", exercise["default_rounds"])}">')
            hidden_inputs.append(f'<input type="hidden" name="weight_{exercise["id"]}_{set_index}" id="weight_{exercise["id"]}_{set_index - 1}" value="{set_values.get("weight", 0.0)}">')

        exercise_html.append(f"""
        <div class="exercise-block" data-exercise-id="{exercise["id"]}" draggable="true">
            <div class="exercise-row-head">
                <div class="exercise-title">{html.escape(exercise["name"])}</div>
                <div class="order-buttons">
                    <div class="drag-hint" title="Mit der Maus halten und verschieben">⇅ ziehen</div>
                    <button type="button" class="order-btn" onclick="moveExercise('{exercise["id"]}', -1)">↑</button>
                    <button type="button" class="order-btn" onclick="moveExercise('{exercise["id"]}', 1)">↓</button>
                </div>
            </div>
            <div class="exercise-controls">
                {''.join(control_groups)}
            </div>

            {''.join(hidden_inputs)}
        </div>
        """)

    save_url = f"/save_training_values/{tag}"
    order_save_url = f"/save_training_order/{tag}"

    content = f"""
    <div class="card">
        <div class="training-head">
            <div>
                <h1>{tag.upper()}</h1>
                <h3>Trainingsplan</h3>
            </div>
            <div class="timer-box">
                <div class="muted">Zeit</div>
                <div class="timer-value" id="timer">00:00</div>
            </div>
        </div>

        <form method="post" action="/complete_training/{tag}" id="trainingForm">
            <input type="hidden" name="duration_seconds" id="duration_seconds" value="0">
            {''.join(exercise_html)}
            <div class="save-note" id="save_note">Änderungen werden automatisch gespeichert.</div>

            <p>
                <button class="green" style="display:inline-block; width:auto; padding:14px 20px;" type="submit">
                    ✅ FERTIG MIT TRAINING
                </button>
            </p>

            <p>
                <a class="gray" style="display:inline-block; width:auto; padding:14px 20px;" href="/">
                    Zurück
                </a>
            </p>
        </form>
    </div>

    <script>
        let savedSeconds = localStorage.getItem("training_seconds");
let seconds = savedSeconds ? parseInt(savedSeconds) : 0;
        let saveTimeout = null;

        function formatTime(totalSeconds) {{
            const mins = Math.floor(totalSeconds / 60);
            const secs = totalSeconds % 60;
            return String(mins).padStart(2, '0') + ':' + String(secs).padStart(2, '0');
        }}

        function tickTimer() {{
    seconds += 1;
    document.getElementById('timer').textContent = formatTime(seconds);
    document.getElementById('duration_seconds').value = String(seconds);
    localStorage.setItem("training_seconds", seconds);
}}

        setInterval(tickTimer, 1000);

        function displayWeight(value) {{
            return value.toFixed(1).replace('.', ',');
        }}

        function changeRounds(exerciseId, setIndex, delta) {{
            const input = document.getElementById('rounds_' + exerciseId + '_' + setIndex);
            let value = parseInt(input.value || '0', 10);
            value = Math.max(0, value + delta);
            input.value = String(value);
            const display = document.getElementById('rounds_display_' + exerciseId + '_' + setIndex);
            if (display) {{
                display.textContent = String(value);
            }}
            queueSave();
        }}

        function changeWeight(exerciseId, setIndex, delta) {{
            const input = document.getElementById('weight_' + exerciseId + '_' + setIndex);
            let value = parseFloat(input.value || '0');
            value = Math.max(0, Math.round((value + delta) * 10) / 10);
            input.value = value.toFixed(1);
            const display = document.getElementById('weight_display_' + exerciseId + '_' + setIndex);
            if (display) {{
                display.textContent = displayWeight(value);
            }}
            queueSave();
        }}

        function collectValues() {{
            const data = {{}};
            document.querySelectorAll('[data-exercise-id]').forEach(function(block) {{
                const exId = block.getAttribute('data-exercise-id');
                data[exId] = {{
                    sets: [0, 1, 2].map(function(setIndex) {{
                        return {{
                            rounds: parseInt(document.getElementById('rounds_' + exId + '_' + setIndex).value || '0', 10),
                            weight: parseFloat(document.getElementById('weight_' + exId + '_' + setIndex).value || '0')
                        }};
                    }})
                }};
            }});
            return data;
        }}

        function collectOrder() {{
            return Array.from(document.querySelectorAll('[data-exercise-id]')).map(function(block) {{
                return block.getAttribute('data-exercise-id');
            }});
        }}

        function saveOrder() {{
            const note = document.getElementById('save_note');
            note.textContent = 'Reihenfolge gespeichert ...';

            fetch({order_save_url!r}, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{ order: collectOrder() }})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.ok) {{
                    note.textContent = 'Reihenfolge gespeichert.';
                }} else {{
                    note.textContent = 'Reihenfolge speichern fehlgeschlagen.';
                }}
            }})
            .catch(() => {{
                note.textContent = 'Reihenfolge speichern fehlgeschlagen.';
            }});
        }}

        function moveExercise(exerciseId, direction) {{
            const form = document.getElementById('trainingForm');
            const block = form.querySelector('[data-exercise-id="' + exerciseId + '"]');
            if (!block) {{
                return;
            }}

            if (direction < 0) {{
                const previous = block.previousElementSibling;
                if (previous && previous.hasAttribute('data-exercise-id')) {{
                    form.insertBefore(block, previous);
                    saveOrder();
                }}
            }} else {{
                const next = block.nextElementSibling;
                if (next && next.hasAttribute('data-exercise-id')) {{
                    form.insertBefore(next, block);
                    saveOrder();
                }}
            }}
        }}

        function initDragAndDrop() {{
            const form = document.getElementById('trainingForm');
            let draggedBlock = null;

            form.querySelectorAll('[data-exercise-id]').forEach(function(block) {{
                block.addEventListener('dragstart', function() {{
                    draggedBlock = block;
                    block.classList.add('dragging');
                }});

                block.addEventListener('dragend', function() {{
                    block.classList.remove('dragging');
                    form.querySelectorAll('[data-exercise-id]').forEach(function(item) {{
                        item.classList.remove('drag-over');
                    }});
                    if (draggedBlock) {{
                        saveOrder();
                    }}
                    draggedBlock = null;
                }});

                block.addEventListener('dragover', function(event) {{
                    event.preventDefault();
                    if (!draggedBlock || draggedBlock === block) {{
                        return;
                    }}
                    block.classList.add('drag-over');
                }});

                block.addEventListener('dragleave', function() {{
                    block.classList.remove('drag-over');
                }});

                block.addEventListener('drop', function(event) {{
                    event.preventDefault();
                    block.classList.remove('drag-over');
                    if (!draggedBlock || draggedBlock === block) {{
                        return;
                    }}

                    const rect = block.getBoundingClientRect();
                    const dropAfter = (event.clientY - rect.top) > (rect.height / 2);

                    if (dropAfter) {{
                        form.insertBefore(draggedBlock, block.nextElementSibling);
                    }} else {{
                        form.insertBefore(draggedBlock, block);
                    }}
                }});
            }});
        }}

        function queueSave() {{
            const note = document.getElementById('save_note');
            note.textContent = 'Speichert ...';

            if (saveTimeout) {{
                clearTimeout(saveTimeout);
            }}

            saveTimeout = setTimeout(function() {{
                fetch({save_url!r}, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{ values: collectValues() }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.ok) {{
                        note.textContent = 'Änderungen gespeichert.';
                    }} else {{
                        note.textContent = 'Speichern fehlgeschlagen.';
                    }}
                }})
                .catch(() => {{
                    note.textContent = 'Speichern fehlgeschlagen.';
                }});
            }}, 250);
        }}

        document.getElementById('trainingForm').addEventListener('submit', function() {{
            document.getElementById('duration_seconds').value = String(seconds);
        }});

        initDragAndDrop();
    </script>
    """
    return html_page(f"{tag} Training", content)


@app.route("/save_training_values/<tag>", methods=["POST"])
def save_training_values(tag):
    if "user_id" not in session:
        return jsonify({"ok": False, "error": "not_logged_in"}), 401

    if tag not in PLAN_DATA:
        return jsonify({"ok": False, "error": "invalid_day"}), 400

    data = request.get_json(silent=True) or {}
    values = data.get("values", {})

    if not isinstance(values, dict):
        values = {}

    save_values_for_tag(tag, values)
    return jsonify({"ok": True})


@app.route("/save_training_order/<tag>", methods=["POST"])
def save_training_order(tag):
    if "user_id" not in session:
        return jsonify({"ok": False, "error": "not_logged_in"}), 401

    if tag not in PLAN_DATA:
        return jsonify({"ok": False, "error": "invalid_day"}), 400

    data = request.get_json(silent=True) or {}
    order = data.get("order", [])

    if not isinstance(order, list):
        order = []

    save_order_for_tag(tag, order)
    return jsonify({"ok": True})


@app.route("/complete_training/<tag>", methods=["POST"])
def complete_training(tag):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if tag not in PLAN_DATA:
        return redirect(url_for("home"))

    values = {}
    for exercise in get_training_exercises(tag):
        ex_id = exercise["id"]
        sets = []

        for set_index in range(1, 4):
            try:
                rounds = max(0, int(request.form.get(f"rounds_{ex_id}_{set_index}", exercise["default_rounds"])))
            except Exception:
                rounds = exercise["default_rounds"]

            try:
                weight = max(0.0, round(float(request.form.get(f"weight_{ex_id}_{set_index}", "0.0")), 1))
            except Exception:
                weight = 0.0

            sets.append({
                "rounds": rounds,
                "weight": weight,
            })

        values[ex_id] = {
            "rounds": sets[0]["rounds"],
            "weight": sets[0]["weight"],
            "sets": sets,
        }

    try:
        duration_seconds = max(0, int(request.form.get("duration_seconds", "0")))
    except Exception:
        duration_seconds = 0

    save_values_for_tag(tag, values)
    add_history_entry(tag, duration_seconds, values)

    status = load_user_status()
    neue_layer = DAY_TO_LAYERS.get(tag, [])
    aktive = set(status.get("active_layers", []))
    aktive.update(neue_layer)

    completed = status.get("completed_days", {})
    completed[tag] = True
    status["completed_days"] = completed
    status["active_layers"] = sorted(aktive)
    save_user_status(status)

    return redirect(url_for("history"))


@app.route("/history")
def history():
    if "user_id" not in session:
        return redirect(url_for("login"))

    content = """
    <div class="card">
        <h1>History</h1>
        <a class="history-folder" href="/history/trainingsverlauf">📁 Trainingsverlauf</a>
        <p><a class="gray" style="display:inline-block; width:auto; padding:14px 20px;" href="/">Zurück</a></p>
    </div>
    """
    return html_page("History", content)


@app.route("/history/trainingsverlauf")
def history_trainingsverlauf():
    if "user_id" not in session:
        return redirect(url_for("login"))

    entries = load_history_entries()

    items = []
    for item in entries:
        items.append(
            f'<a class="history-item" href="/history/detail/{item["id"]}"><b>{html.escape(item.get("training_day", ""))}</b><br>{html.escape(item.get("title", ""))}<br><span class="muted">{html.escape(str(item.get("training_date", "")))} • {format_duration(item.get("duration_seconds", 0))}</span></a>'
        )

    items_html = "".join(items) if items else '<div class="history-item">Noch keine gespeicherten Trainingstage vorhanden.</div>'

    content = f"""
    <div class="card">
        <h1>Trainingsverlauf</h1>
        {items_html}
        <p><a class="gray" style="display:inline-block; width:auto; padding:14px 20px;" href="/history">Zurück</a></p>
    </div>
    """
    return html_page("Trainingsverlauf", content)


@app.route("/history/detail/<int:entry_id>")
def history_detail(entry_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    entry = load_history_entry(entry_id)
    if not entry:
        return redirect(url_for("history_trainingsverlauf"))

    exercises = entry.get("exercises") or []
    exercise_html = []

    for exercise in exercises:
        exercise_html.append(f"""
        <div class="exercise-block">
            <div class="exercise-title">{html.escape(exercise.get('name', 'Übung'))}</div>
            <div class="exercise-controls disabled">
                <div class="control-group">
                    <div class="mini-label">Runden</div>
                    <div class="stepper">
                        <button type="button" disabled>-</button>
                        <div class="stepper-value">{int(exercise.get('rounds', 0))}</div>
                        <button type="button" disabled>+</button>
                    </div>
                    <div class="mini-label">Kilo</div>
                    <div class="stepper">
                        <button type="button" disabled>-</button>
                        <div class="stepper-value">{format_weight(exercise.get('weight', 0.0))}</div>
                        <button type="button" disabled>+</button>
                    </div>
                </div>
                <div class="control-group">
                    <div class="mini-label">Runden</div>
                    <div class="stepper">
                        <button type="button" disabled>-</button>
                        <div class="stepper-value">{int(exercise.get('rounds', 0))}</div>
                        <button type="button" disabled>+</button>
                    </div>
                    <div class="mini-label">Kilo</div>
                    <div class="stepper">
                        <button type="button" disabled>-</button>
                        <div class="stepper-value">{format_weight(exercise.get('weight', 0.0))}</div>
                        <button type="button" disabled>+</button>
                    </div>
                </div>
                <div class="control-group">
                    <div class="mini-label">Runden</div>
                    <div class="stepper">
                        <button type="button" disabled>-</button>
                        <div class="stepper-value">{int(exercise.get('rounds', 0))}</div>
                        <button type="button" disabled>+</button>
                    </div>
                    <div class="mini-label">Kilo</div>
                    <div class="stepper">
                        <button type="button" disabled>-</button>
                        <div class="stepper-value">{format_weight(exercise.get('weight', 0.0))}</div>
                        <button type="button" disabled>+</button>
                    </div>
                </div>
            </div>
        </div>
        """)

    content = f"""
    <div class="card">
        <div class="training-head">
            <div>
                <h1>{html.escape(entry.get('training_day', ''))}</h1>
                <h3>{html.escape(entry.get('title', ''))}</h3>
                <p class="muted">Datum: {html.escape(str(entry.get('training_date', '')))}</p>
            </div>
            <div class="timer-box">
                <div class="muted">Zeit</div>
                <div class="timer-value">{format_duration(entry.get('duration_seconds', 0))}</div>
            </div>
        </div>

        {''.join(exercise_html)}

        <p><a class="gray" style="display:inline-block; width:auto; padding:14px 20px;" href="/history/trainingsverlauf">Zurück</a></p>
    </div>
    """
    return html_page("History Detail", content)


@app.route("/complete/<tag>")
def complete(tag):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if tag not in PLAN_DATA:
        return redirect(url_for("home"))

    status = load_user_status()
    neue_layer = DAY_TO_LAYERS.get(tag, [])
    aktive = set(status.get("active_layers", []))
    aktive.update(neue_layer)

    completed = status.get("completed_days", {})
    completed[tag] = True
    status["completed_days"] = completed
    status["active_layers"] = sorted(aktive)
    save_user_status(status)

    return redirect(url_for("home", tag=tag))


@app.route("/reset_week")
def reset_week():
    if "user_id" not in session:
        return redirect(url_for("login"))

    status = default_status()
    save_user_status(status)
    return redirect(url_for("home"))


@app.route("/uebungen")
def uebungen():
    items = []
    for buchstabe in sorted(UEBUNGEN_A_Z.keys()):
        u = UEBUNGEN_A_Z[buchstabe]
        items.append(
            f'<a href="/uebung/{buchstabe}"><b>{buchstabe}) {html.escape(u["name"])}</b></a>'
        )

    content = f"""
    <div class="card">
        <h1>🏋️ Übungen A–Z</h1>
        <div class="listbox">
            {''.join(items)}
        </div>
        <p><a class="gray" style="display:inline-block; width:auto; padding:14px 20px;" href="/">Zurück</a></p>
    </div>
    """
    return html_page("Übungen A-Z", content)


@app.route("/uebung/<buchstabe>")
def uebung_detail(buchstabe):
    u = UEBUNGEN_A_Z.get(buchstabe.upper())
    if not u:
        return redirect(url_for("uebungen"))

    content = f"""
    <div class="card">
        <h1>{html.escape(u["name"])}</h1>
        <pre>{html.escape(u["anleitung"])}</pre>
        <p><a class="gray" style="display:inline-block; width:auto; padding:14px 20px;" href="/uebungen">Zurück</a></p>
    </div>
    """
    return html_page(u["name"], content)


@app.route("/ernaehrung")
def ernaehrung():
    text = """ERGEBNIS DES ERNÄHRUNGSBERATERS:

Gute Punkte:
• Ausreichend Wasser trinken
• Viel Gemüse und Salat

Korrigieren:
• Weniger Zucker
• Mehr Eiweiß
• Mehr Ballaststoffe

Tipps:
1. 3 Mahlzeiten + 2 Snacks.
2. In jede Mahlzeit Eiweiß einbauen.
3. Viel Wasser trinken.
4. Süßes nur in kleinen Mengen."""
    content = f"""
    <div class="card">
        <h1>😋 Ernährungsberater</h1>
        <pre>{html.escape(text)}</pre>
        <p><a class="gray" style="display:inline-block; width:auto; padding:14px 20px;" href="/">Zurück</a></p>
    </div>
    """
    return html_page("Ernährungsberater", content)


@app.route("/formanalyse", methods=["GET", "POST"])
def formanalyse():
    result_html = ""
    file_info = "Noch kein Foto geladen."

    if request.method == "POST":
        f = request.files.get("foto")
        if f and f.filename:
            file_info = f"Geladen: {html.escape(f.filename)}"
            result_text = """FORM ANALYSE ERGEBNIS:

Gute Punkte:
• Schultern symmetrisch
• Becken stabil

Korrigieren:
• Rücken leicht gekrümmt
• Knie leicht nach innen

Training Fokus:
1. PLANK
2. DEADLIFT mit geradem Rücken
3. Schulter-Mobilität

SCORE: 82/100"""
            result_html = f"<h3>ANALYSE FERTIG!</h3><pre>{html.escape(result_text)}</pre>"
        else:
            result_html = "<p style='color:red;'><b>Bitte zuerst ein Foto laden.</b></p>"

    content = f"""
    <div class="card">
        <h1>Formanalyse</h1>
        <p>{file_info}</p>

        <form method="post" enctype="multipart/form-data">
            <p><input type="file" name="foto" accept=".jpg,.jpeg,.png"></p>
            <p><button class="red" type="submit">Analyse</button></p>
        </form>

        {result_html}

        <p><a class="gray" style="display:inline-block; width:auto; padding:14px 20px;" href="/">Zurück</a></p>
    </div>
    """
    return html_page("Formanalyse", content)


@app.route("/register", methods=["GET", "POST"])
def register():
    fehler = ""

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            fehler = "Bitte alles ausfüllen."
        else:
            try:
                auth_response = supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                })

                user = auth_response.user

                if user:
                    session["user_email"] = email
                    session["user_id"] = user.id

                    create_profile_for_user(user.id, email)
                    create_training_status_for_user(user.id)
                    ensure_workout_settings_for_user(user.id)

                    return redirect(url_for("home"))
                else:
                    fehler = "Registrierung erfolgreich, aber kein User zurückgegeben."
            except Exception as e:
                fehler = f"Registrierung fehlgeschlagen: {e}"

    content = f"""
    <div class="card" style="max-width:500px; margin:40px auto;">
        <h1>Registrieren</h1>
        <p style="color:red;">{html.escape(fehler)}</p>
        <form method="post">
            <label>Email</label><br>
            <input name="email" type="email" style="width:100%; padding:10px;"><br><br>

            <label>Passwort</label><br>
            <input name="password" type="password" style="width:100%; padding:10px;"><br><br>

            <button type="submit" style="padding:12px 18px;">Account erstellen</button>
        </form>
        <br>
        <a href="/login">Schon Account? Login</a>
    </div>
    """
    return html_page("Registrieren", content)


@app.route("/login", methods=["GET", "POST"])
def login():
    fehler = ""

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            fehler = "Bitte Email und Passwort eingeben."
        else:
            try:
                auth_response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })

                user = auth_response.user

                if user:
                    session["user_email"] = email
                    session["user_id"] = user.id

                    create_profile_for_user(user.id, email)
                    create_training_status_for_user(user.id)
                    ensure_workout_settings_for_user(user.id)

                    return redirect(url_for("home"))
                else:
                    fehler = "Login ok, aber Userdaten fehlen."
            except Exception as e:
                fehler = f"Login fehlgeschlagen: {e}"

    content = f"""
    <div class="card" style="max-width:500px; margin:40px auto;">
        <h1>Login</h1>
        <p style="color:red;">{html.escape(fehler)}</p>
        <form method="post">
            <label>Email</label><br>
            <input name="email" type="email" style="width:100%; padding:10px;"><br><br>

            <label>Passwort</label><br>
            <input name="password" type="password" style="width:100%; padding:10px;"><br><br>

            <button type="submit" style="padding:12px 18px;">Einloggen</button>
        </form>
        <br>
        <a href="/register">Noch keinen Account? Registrieren</a>
    </div>
    """
    return html_page("Login", content)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/test")
def test():
    return "Supabase verbunden!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
