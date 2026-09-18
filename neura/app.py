import os
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from supabase import create_client, Client


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(
    dotenv_path=os.path.join(
        os.path.dirname(__file__),
        ".env"
    ),
    override=True
)


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "NEURA_SECRET_KEY",
    "neura-development-secret"
)


# ============================================================
# SUPABASE CONFIGURATION
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL:
    raise ValueError(
        "SUPABASE_URL is missing in .env"
    )

if not SUPABASE_ANON_KEY:
    raise ValueError(
        "SUPABASE_ANON_KEY is missing in .env"
    )

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_ANON_KEY
)


# ============================================================
# LOCAL NEURA AI
# ============================================================

from ai_engine import (
    generate_study_recommendation,
    generate_chat_response,
)


# ============================================================
# LOGIN REQUIRED
# ============================================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user" not in session:

            return jsonify({
                "success": False,
                "error": "Login required"
            }), 401

        return function(*args, **kwargs)

    return wrapper


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/")
def index():

    if "user" in session:

        return redirect(
            url_for("home")
        )

    return render_template(
        "index.html"
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/home")
@login_required
def home():

    return render_template(
        "home.html"
    )


# ============================================================
# SIGNUP
# ============================================================

@app.post("/api/signup")
def signup():

    data = request.get_json(
        silent=True
    ) or {}

    email = (
        data.get("email") or ""
    ).strip()

    password = (
        data.get("password") or ""
    )

    if not email or not password:

        return jsonify({
            "success": False,
            "error": "Email and password are required"
        }), 400

    try:

        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        if response.user:

            session["user"] = {
                "id": response.user.id,
                "email": response.user.email
            }

        return jsonify({
            "success": True,
            "message": (
                "Account created successfully. "
                "Please check your email if confirmation is required."
            )
        })

    except Exception as e:

        print(
            "Signup error:",
            e
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


# ============================================================
# LOGIN
# ============================================================

@app.post("/api/login")
def login():

    data = request.get_json(
        silent=True
    ) or {}

    email = (
        data.get("email") or ""
    ).strip()

    password = (
        data.get("password") or ""
    )

    if not email or not password:

        return jsonify({
            "success": False,
            "error": "Email and password are required"
        }), 400

    try:

        response = (
            supabase
            .auth
            .sign_in_with_password({
                "email": email,
                "password": password
            })
        )

        if not response.user:

            return jsonify({
                "success": False,
                "error": "Invalid login"
            }), 401

        session["user"] = {
            "id": response.user.id,
            "email": response.user.email
        }

        return jsonify({
            "success": True,
            "message": "Login successful"
        })

    except Exception as e:

        print(
            "Login error:",
            e
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 401


# ============================================================
# LOGOUT
# ============================================================

@app.post("/api/logout")
def logout():

    try:

        supabase.auth.sign_out()

    except Exception:

        pass

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    })


# ============================================================
# CURRENT USER
# ============================================================

@app.get("/api/me")
@login_required
def current_user():

    user = session.get(
        "user"
    )

    return jsonify({
        "success": True,
        "user": user
    })


# ============================================================
# DASHBOARD STATE
# ============================================================

@app.get("/api/state")
@login_required
def get_state():

    user_id = session["user"]["id"]

    try:

        mood_response = (
            supabase
            .table("mood_entries")
            .select("*")
            .eq("user_id", user_id)
            .order(
                "created_at",
                desc=True
            )
            .limit(20)
            .execute()
        )

        task_response = (
            supabase
            .table("tasks")
            .select("*")
            .eq("user_id", user_id)
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )

        focus_response = (
            supabase
            .table("focus_sessions")
            .select("*")
            .eq("user_id", user_id)
            .order(
                "created_at",
                desc=True
            )
            .limit(20)
            .execute()
        )

        return jsonify({
            "success": True,
            "moods": mood_response.data or [],
            "tasks": task_response.data or [],
            "focus_sessions": (
                focus_response.data or []
            )
        })

    except Exception as e:

        print(
            "State error:",
            e
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# SAVE MOOD
# ============================================================

@app.post("/api/mood")
@login_required
def save_mood():

    data = request.get_json(
        silent=True
    ) or {}

    user_id = session["user"]["id"]

    mood = (
        data.get("mood") or ""
    ).strip()

    energy = data.get(
        "energy",
        50
    )

    note = (
        data.get("note") or ""
    ).strip()

    if not mood:

        return jsonify({
            "success": False,
            "error": "Mood is required"
        }), 400

    try:

        energy = int(
            energy
        )

    except (
        TypeError,
        ValueError
    ):

        energy = 50

    energy = max(
        0,
        min(100, energy)
    )

    try:

        response = (
            supabase
            .table("mood_entries")
            .insert({
                "user_id": user_id,
                "mood": mood,
                "energy": energy,
                "note": note
            })
            .execute()
        )

        return jsonify({
            "success": True,
            "data": response.data
        })

    except Exception as e:

        print(
            "Mood error:",
            e
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# GET TASKS
# ============================================================

@app.get("/api/tasks")
@login_required
def get_tasks():

    user_id = session["user"]["id"]

    try:

        response = (
            supabase
            .table("tasks")
            .select("*")
            .eq("user_id", user_id)
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )

        return jsonify({
            "success": True,
            "tasks": response.data or []
        })

    except Exception as e:

        print(
            "Get tasks error:",
            e
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# CREATE TASK
# ============================================================

@app.post("/api/tasks")
@login_required
def create_task():

    data = request.get_json(
        silent=True
    ) or {}

    user_id = session["user"]["id"]

    title = (
        data.get("title") or ""
    ).strip()

    priority = (
        data.get("priority")
        or "Normal"
    ).strip()

    if not title:

        return jsonify({
            "success": False,
            "error": "Task title is required"
        }), 400

    try:

        response = (
            supabase
            .table("tasks")
            .insert({
                "user_id": user_id,
                "title": title,
                "priority": priority,
                "completed": False
            })
            .execute()
        )

        return jsonify({
            "success": True,
            "task": (
                response.data[0]
                if response.data
                else None
            )
        })

    except Exception as e:

        print(
            "Create task error:",
            e
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# UPDATE TASK
# ============================================================

@app.put("/api/tasks/<task_id>")
@login_required
def update_task(task_id):

    data = request.get_json(
        silent=True
    ) or {}

    user_id = session["user"]["id"]

    update_data = {}

    if "title" in data:

        update_data["title"] = (
            data.get("title") or ""
        ).strip()

    if "priority" in data:

        update_data["priority"] = (
            data.get("priority")
            or "Normal"
        )

    if "completed" in data:

        update_data["completed"] = bool(
            data.get("completed")
        )

    if not update_data:

        return jsonify({
            "success": False,
            "error": "No task data provided"
        }), 400

    try:

        response = (
            supabase
            .table("tasks")
            .update(update_data)
            .eq("id", task_id)
            .eq("user_id", user_id)
            .execute()
        )

        return jsonify({
            "success": True,
            "task": (
                response.data[0]
                if response.data
                else None
            )
        })

    except Exception as e:

        print(
            "Update task error:",
            e
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# DELETE TASK
# ============================================================

@app.delete("/api/tasks/<task_id>")
@login_required
def delete_task(task_id):

    user_id = session["user"]["id"]

    try:

        response = (
            supabase
            .table("tasks")
            .delete()
            .eq("id", task_id)
            .eq("user_id", user_id)
            .execute()
        )

        return jsonify({
            "success": True,
            "data": response.data
        })

    except Exception as e:

        print(
            "Delete task error:",
            e
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# SAVE FOCUS SESSION
# ============================================================

@app.post("/api/focus")
@login_required
def save_focus_session():

    data = request.get_json(
        silent=True
    ) or {}

    user_id = session["user"]["id"]

    duration = data.get(
        "duration",
        0
    )

    task = (
        data.get("task") or ""
    ).strip()

    try:

        duration = int(
            duration
        )

    except (
        TypeError,
        ValueError
    ):

        duration = 0

    duration = max(
        0,
        duration
    )

    try:

        response = (
            supabase
            .table("focus_sessions")
            .insert({
                "user_id": user_id,
                "duration_minutes": duration,
                "task": task
            })
            .execute()
        )

        return jsonify({
            "success": True,
            "data": response.data
        })

    except Exception as e:

        print(
            "Focus session error:",
            e
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# NEXT BEST ACTION — AI
# ============================================================

@app.post("/api/next-best-action")
@login_required
def next_best_action():

    payload = request.get_json(
        silent=True
    ) or {}

    mood_value = (
        payload.get("mood")
        or "Calm"
    )

    energy_value = payload.get(
        "energy",
        50
    )

    task_value = (
        payload.get("task")
        or "Review your study notes"
    )

    priority_value = (
        payload.get("priority")
        or "Normal"
    )

    try:

        energy_value = int(
            energy_value
        )

    except (
        TypeError,
        ValueError
    ):

        energy_value = 50

    energy_value = max(
        0,
        min(100, energy_value)
    )

    try:

        recommendation = (
            generate_study_recommendation(
                mood=mood_value,
                energy=energy_value,
                task=task_value,
                priority=priority_value
            )
        )

        return jsonify({
            "success": True,
            "mood": mood_value,
            "energy": energy_value,
            "task": task_value,
            "priority": priority_value,
            "recommendation": recommendation
        })

    except Exception as e:

        print(
            "Next Best Action error:",
            e
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# NEURA COPILOT — LOCAL QWEN AI
# ============================================================

@app.post("/api/chat")
@login_required
def chat():

    data = request.get_json(
        silent=True
    ) or {}

    message = (
        data.get("message") or ""
    ).strip()

    if not message:

        return jsonify({
            "reply": (
                "Tell me what you are working on "
                "or what you would like to learn."
            )
        })

    try:

        reply = generate_chat_response(
            message
        )

        return jsonify({
            "reply": reply
        })

    except Exception as e:

        print(
            "Neura Copilot error:",
            e
        )

        return jsonify({
            "reply": (
                "I'm having trouble generating a response "
                "right now. Please try again."
            )
        })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return jsonify({
        "status": "ok",
        "app": "NEURA",
        "ai": "Qwen local"
    })


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):

    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
