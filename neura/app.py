import os
from functools import wraps
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('NEURA_SECRET_KEY', 'change-this-in-production')

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://YOUR-PROJECT.supabase.co')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', 'YOUR_SUPABASE_ANON_KEY')
AI_API_URL = os.environ.get('AI_API_URL', 'https://YOUR-AI-PROVIDER.example/v1/chat/completions')
AI_API_KEY = os.environ.get('AI_API_KEY', 'YOUR_AI_API_KEY')
AI_MODEL = os.environ.get('AI_MODEL', 'YOUR_MODEL_NAME')


def configured():
    return SUPABASE_URL.startswith('http') and 'YOUR-PROJECT' not in SUPABASE_URL and 'YOUR_SUPABASE' not in SUPABASE_ANON_KEY


def supabase_request(method, path, token=None, body=None, params=None):
    headers = {'apikey': SUPABASE_ANON_KEY, 'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    r = requests.request(method, f'{SUPABASE_URL.rstrip("/")}{path}', headers=headers, json=body, params=params, timeout=15)
    if not r.ok:
        try: detail = r.json()
        except Exception: detail = r.text
        raise RuntimeError(str(detail))
    if not r.content:
        return None
    return r.json()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('access_token'):
            flash('Sign in to continue.', 'error')
            return redirect(url_for('index'))
        return view(*args, **kwargs)
    return wrapped


def current_profile():
    user = session.get('user', {})
    return {'id': user.get('id'), 'name': user.get('user_metadata', {}).get('name') or user.get('email', '').split('@')[0], 'email': user.get('email', '')}


@app.route('/')
def index():
    if session.get('access_token'):
        return redirect(url_for('home'))
    return render_template('index.html')


@app.post('/signup')
def signup():
    name = request.form.get('name', '').strip()
    email = request.form.get('signup_email', '').strip().lower()
    password = request.form.get('signup_password', '')
    if not name or not email or len(password) < 8:
        flash('Enter your name, a valid email, and a password of at least 8 characters.', 'error')
        return redirect(url_for('index'))
    if not configured():
        flash('Supabase is not configured yet. Add SUPABASE_URL and SUPABASE_ANON_KEY to .env first.', 'error')
        return redirect(url_for('index'))
    try:
        data = supabase_request('POST', '/auth/v1/signup', body={'email': email, 'password': password, 'data': {'name': name}})
        if not data.get('access_token'):
            flash('Account created. Check your email if email confirmation is enabled in Supabase.', 'success')
            return redirect(url_for('index'))
        session.clear(); session['access_token'] = data['access_token']; session['user'] = data['user']
        return redirect(url_for('home'))
    except Exception as e:
        flash('Could not create the account: ' + str(e), 'error')
        return redirect(url_for('index'))


@app.post('/login')
def login():
    email = request.form.get('email', '').strip().lower(); password = request.form.get('password', '')
    if not email or not password:
        flash('Enter your email and password.', 'error'); return redirect(url_for('index'))
    if not configured():
        flash('Supabase is not configured yet. Add the environment values in .env.', 'error'); return redirect(url_for('index'))
    try:
        data = supabase_request('POST', '/auth/v1/token', body={'email': email, 'password': password}, params={'grant_type': 'password'})
        session.clear(); session['access_token'] = data['access_token']; session['refresh_token'] = data.get('refresh_token'); session['user'] = data['user']
        return redirect(url_for('home'))
    except Exception as e:
        flash('Sign in failed. Check your email and password.', 'error'); return redirect(url_for('index'))


@app.route('/home')
@login_required
def home():
    return render_template('home.html', user=current_profile(), supabase_ready=configured())


@app.get('/api/state')
@login_required
def state():
    token = session['access_token']; uid = session['user']['id']
    try:
        moods = supabase_request('GET', '/rest/v1/mood_entries', token, params={'select':'*','user_id':f'eq.{uid}','order':'created_at.desc','limit':'30'}) or []
        tasks = supabase_request('GET', '/rest/v1/tasks', token, params={'select':'*','user_id':f'eq.{uid}','order':'created_at.desc','limit':'100'}) or []
        sessions_data = supabase_request('GET', '/rest/v1/focus_sessions', token, params={'select':'*','user_id':f'eq.{uid}','order':'started_at.desc','limit':'50'}) or []
        return jsonify({'moods': moods, 'tasks': tasks, 'sessions': sessions_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.post('/api/mood')
@login_required
def mood():
    payload = request.get_json(force=True); payload['user_id'] = session['user']['id']; payload['created_at'] = datetime.now(timezone.utc).isoformat()
    try:
        row = supabase_request('POST', '/rest/v1/mood_entries', session['access_token'], payload, params={'select':'*'})
        return jsonify(row[0] if isinstance(row, list) else row)
    except Exception as e: return jsonify({'error': str(e)}), 500


@app.post('/api/task')
@login_required
def task():
    payload = request.get_json(force=True); payload['user_id'] = session['user']['id']
    try:
        row = supabase_request('POST', '/rest/v1/tasks', session['access_token'], payload, params={'select':'*'})
        return jsonify(row[0] if isinstance(row, list) else row)
    except Exception as e: return jsonify({'error': str(e)}), 500


@app.patch('/api/task/<task_id>')
@login_required
def update_task(task_id):
    payload = request.get_json(force=True)
    try:
        row = supabase_request('PATCH', '/rest/v1/tasks', session['access_token'], payload, params={'id':f'eq.{task_id}','user_id':f'eq.{session["user"]["id"]}','select':'*'})
        return jsonify(row[0] if isinstance(row, list) and row else row)
    except Exception as e: return jsonify({'error': str(e)}), 500


@app.delete('/api/task/<task_id>')
@login_required
def delete_task(task_id):
    try:
        supabase_request('DELETE', '/rest/v1/tasks', session['access_token'], params={'id':f'eq.{task_id}','user_id':f'eq.{session["user"]["id"]}'})
        return jsonify({'ok': True})
    except Exception as e: return jsonify({'error': str(e)}), 500


@app.post('/api/focus')
@login_required
def focus():
    payload = request.get_json(force=True); payload['user_id'] = session['user']['id']; payload['started_at'] = payload.get('started_at') or datetime.now(timezone.utc).isoformat()
    try:
        row = supabase_request('POST', '/rest/v1/focus_sessions', session['access_token'], payload, params={'select':'*'})
        return jsonify(row[0] if isinstance(row, list) else row)
    except Exception as e: return jsonify({'error': str(e)}), 500


@app.post('/api/chat')
@login_required
def chat():
    message = (request.get_json(force=True).get('message') or '').strip()
    if not message: return jsonify({'reply':'Tell me what you are working on or how you feel today.'})
    if 'YOUR-AI-PROVIDER' in AI_API_URL or 'YOUR_AI_API_KEY' in AI_API_KEY:
        return jsonify({'reply': 'Neura AI is ready for integration. Add AI_API_URL, AI_API_KEY and AI_MODEL to your .env. For now, I can still help you shape a study plan from your mood and goals.'})
    try:
        headers={'Authorization':f'Bearer {AI_API_KEY}','Content-Type':'application/json'}
        body={'model':AI_MODEL,'messages':[{'role':'system','content':'You are Neura, an encouraging adaptive study and productivity copilot for students and professionals. Be concise, practical, safe, and personalize suggestions around mood, energy, workload and goals.'},{'role':'user','content':message}]}
        r=requests.post(AI_API_URL,headers=headers,json=body,timeout=30); r.raise_for_status(); data=r.json()
        return jsonify({'reply': data['choices'][0]['message']['content']})
    except Exception:
        return jsonify({'reply':'I could not reach the AI provider right now. Your planner is still available, and your saved data remains separate from the AI service.'})


@app.post('/logout')
def logout():
    token=session.get('access_token')
    if token and configured():
        try: supabase_request('POST','/auth/v1/logout',token)
        except Exception: pass
    session.clear(); return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)), debug=True)
