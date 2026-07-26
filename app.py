import sys
import os
import json
import secrets
import uuid
import threading
import queue
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from flask import Flask, render_template, send_file, request, jsonify, redirect, url_for, Response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from themes import (
    RosaTheme, AzulTheme, VerdeTheme, AmareloTheme,
    LaranjaTheme, VermelhoTheme, LilasTheme, PretoTheme
)
from pdf_generator import gerar_pdf_datada, gerar_pdf_permanente, gerar_preview
import localization

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'agendacreatorpro-secret-key-change-in-prod')

_openai_key = os.environ.get('OPENAI_API_KEY', '')
print(f"[STARTUP] OPENAI_API_KEY set: {bool(_openai_key)}, len: {len(_openai_key)}")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'agendacreatorpro@gmail.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Agenda15*')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'agendacreatorpro-webhook-secret')

USERS = {
    ADMIN_EMAIL.lower(): {
        'email': ADMIN_EMAIL.lower(),
        'password': generate_password_hash(ADMIN_PASSWORD),
        'token': '',
        'ativo': True,
    },
    'sammy.paschoalin@gmail.com': {
        'email': 'sammy.paschoalin@gmail.com',
        'password': generate_password_hash('Sammy07!'),
        'token': '',
        'ativo': True,
    },
    'strelakadente@gmail.com': {
        'email': 'strelakadente@gmail.com',
        'password': generate_password_hash('Veiga65@'),
        'token': '',
        'ativo': True,
    },
    'magaliduarte16@gmail.com': {
        'email': 'magaliduarte16@gmail.com',
        'password': generate_password_hash('Md@130370'),
        'token': '',
        'ativo': True,
    },
}


class User(UserMixin):
    def __init__(self, email):
        self.id = email


def find_user(email):
    return USERS.get(email.lower())


def find_user_by_token(token):
    for u in USERS.values():
        if u.get('token') == token and u.get('ativo'):
            return u
    return None


def create_user(email, token=None):
    key = email.lower()
    if key in USERS:
        if token:
            USERS[key]['token'] = token
        return USERS[key]
    if not token:
        token = secrets.token_urlsafe(32)
    user = {
        'email': key,
        'password': generate_password_hash(token),
        'token': token,
        'ativo': True,
    }
    USERS[key] = user
    return user


@login_manager.user_loader
def load_user(email):
    u = find_user(email)
    if u and u.get('ativo'):
        return User(email)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    if request.is_json or '/gerar' in request.path or '/preview' in request.path:
        return jsonify({'error': 'Unauthorized'}), 401
    return redirect(url_for('login_page'))


@app.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('landing.html')


@app.route('/auth')
def auth_token():
    token = request.args.get('token', '')
    if not token:
        return redirect(url_for('landing'))
    user = find_user_by_token(token)
    if user:
        login_user(User(user['email']))
        return redirect(url_for('index'))
    return redirect(url_for('login_page'))


@app.route('/login', methods=['GET'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    user = find_user(email)
    if user and user.get('ativo') and check_password_hash(user['password'], password):
        login_user(User(user['email']))
        return jsonify({'success': True, 'redirect': '/'})
    return jsonify({'success': False, 'message': 'E-mail ou senha incorretos'})


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing'))


@app.route('/app')
@login_required
def index():
    return render_template('index.html')


@app.route('/admin/users', methods=['GET'])
@login_required
def admin_users():
    return jsonify(list(USERS.values()))


@app.route('/admin/users', methods=['POST'])
@login_required
def admin_create_user():
    data = request.json
    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email obrigatorio'}), 400
    user = create_user(email)
    return jsonify({
        'email': user['email'],
        'token': user['token'],
        'link': f"{request.host_url}auth?token={user['token']}"
    })


@app.route('/webhook/cakto', methods=['POST'])
def webhook_cakto():
    auth_header = request.headers.get('Authorization', '')
    if auth_header != f"Bearer {WEBHOOK_SECRET}":
        return jsonify({'error': 'Unauthorized'}), 401
    payload = request.json
    if not payload:
        return jsonify({'error': 'Invalid payload'}), 400
    email = (
        payload.get('email') or
        payload.get('buyer_email') or
        payload.get('participant', {}).get('email') or
        payload.get('data', {}).get('email') or
        ''
    ).strip().lower()
    if not email:
        return jsonify({'error': 'Email not found'}), 400
    user = create_user(email)
    return jsonify({'success': True, 'email': user['email'], 'token': user['token']})


TEMAS = {
    "rosa": RosaTheme, "azul": AzulTheme, "verde": VerdeTheme,
    "amarelo": AmareloTheme, "laranja": LaranjaTheme,
    "vermelho": VermelhoTheme, "lilas": LilasTheme, "preto": PretoTheme,
}


@app.route('/gerar', methods=['POST'])
@login_required
def gerar_pdf():
    try:
        data = request.json
        tipo = data.get('tipo', 'datada')
        ano = int(data.get('ano', 2026))
        paginas = int(data.get('paginas', 52))
        tema_nome = data.get('tema', 'rosa')
        estilo = data.get('estilo', 'minimalista')
        formato = data.get('formato', 'A5')
        layout = data.get('layout', '1')
        com_agendamentos = data.get('agendamentos', False)
        idioma = data.get('idioma', 'pt')

        tema = TEMAS.get(tema_nome, RosaTheme)()
        from styles.manager import definir as definir_estilo
        definir_estilo(estilo)
        localization.definir_idioma(idioma)

        if tipo == 'datada':
            buffer = gerar_pdf_datada(ano, tema, layout, formato, com_agendamentos=com_agendamentos)
            nome = f"Agenda_{ano}_{tema_nome}_{formato}.pdf"
        else:
            buffer = gerar_pdf_permanente(paginas, tema, ano, formato)
            nome = f"Agenda_Permanente_{tema_nome}_{formato}.pdf"

        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/preview', methods=['POST'])
@login_required
def preview_pdf():
    try:
        data = request.json
        ano = int(data.get('ano', 2026))
        tema_nome = data.get('tema', 'rosa')
        estilo = data.get('estilo', 'minimalista')
        formato = data.get('formato', 'A5')
        layout = data.get('layout', '1')
        com_agendamentos = data.get('agendamentos', False)
        idioma = data.get('idioma', 'pt')

        tema = TEMAS.get(tema_nome, RosaTheme)()
        from styles.manager import definir as definir_estilo
        definir_estilo(estilo)
        localization.definir_idioma(idioma)

        buffer = gerar_preview(ano, tema, layout, formato, com_agendamentos=com_agendamentos)
        return send_file(buffer, mimetype='application/pdf')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


IA_TASKS = {}
IA_LOCK = threading.Lock()


@app.route('/ia')
@login_required
def ia_creator():
    return render_template('ia_creator.html')


@app.route('/api/ia/debug')
@login_required
def ia_debug():
    key = os.environ.get('OPENAI_API_KEY', '')
    masked = (key[:8] + '...' + key[-4:]) if len(key) > 12 else 'NOT SET'
    return jsonify({"key_preview": masked, "key_len": len(key)})


@app.route('/api/ia/analyze', methods=['POST'])
@login_required
def ia_analyze():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image = request.files['image']
    provider = request.form.get('provider', 'openai')

    allowed = {'image/png', 'image/jpeg', 'image/jpg', 'application/pdf'}
    if image.content_type not in allowed:
        return jsonify({"error": "Format not supported"}), 400

    image_bytes = image.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        return jsonify({"error": "File too large (max 20MB)"}), 400

    task_id = str(uuid.uuid4())[:8]
    progress_queue = queue.Queue()

    with IA_LOCK:
        IA_TASKS[task_id] = {"status": "processing", "progress_queue": progress_queue, "result": None}

    def on_progress(msg):
        progress_queue.put(msg)

    def run_analysis():
        try:
            from ai.analyzer import SmartAnalyzer
            api_key_val = os.environ.get('OPENAI_API_KEY', '')
            analyzer = SmartAnalyzer(provider_name=provider, api_key=api_key_val or None)
            result = analyzer.analyze(image_bytes, content_type=image.content_type, on_progress=on_progress)
            with IA_LOCK:
                IA_TASKS[task_id]["result"] = result.to_dict()
                IA_TASKS[task_id]["status"] = "done"
            progress_queue.put({"stage": "complete", "progress": 100, "message": "Done"})
        except Exception as e:
            import traceback
            traceback.print_exc()
            with IA_LOCK:
                IA_TASKS[task_id]["result"] = {"success": False, "error": str(e)}
                IA_TASKS[task_id]["status"] = "done"
            progress_queue.put({"stage": "error", "progress": 100, "message": str(e)})

    threading.Thread(target=run_analysis, daemon=True).start()
    return jsonify({"success": True, "task_id": task_id})


@app.route('/api/ia/stream/<task_id>')
@login_required
def ia_stream(task_id):
    with IA_LOCK:
        task = IA_TASKS.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    def generate():
        pq = task["progress_queue"]
        while True:
            try:
                msg = pq.get(timeout=30)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get("stage") in ("complete", "error"):
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'stage': 'timeout', 'progress': 0, 'message': 'Timeout'})}\n\n"
                break

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/ia/result/<task_id>')
@login_required
def ia_result(task_id):
    with IA_LOCK:
        task = IA_TASKS.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    result = task.get("result")
    if not result:
        return jsonify({"success": False, "error": "Analysis still in progress"})
    return jsonify(result)


@app.route('/api/ia/generate', methods=['POST'])
@login_required
def ia_generate():
    try:
        data = request.json
        formato = data.get('formato', 'A5')
        page_analysis = data.get('page_analysis', {})

        if not page_analysis:
            return jsonify({"error": "No analysis data"}), 400

        from themes import criar_tema_da_ia
        colors = page_analysis.get('colors', [])
        theme = criar_tema_da_ia(colors)

        page_type = page_analysis.get('page_type', '1dpp')
        ano = 2026

        from styles.manager import definir as definir_estilo
        if page_type in ('2dpp',):
            definir_estilo('minimalista')
            layout = '2'
        else:
            definir_estilo('minimalista')
            layout = '1'

        if page_type in ('semanal', 'mensal', 'calendario', 'planejamento', 'metas'):
            buffer = gerar_pdf_permanente(52, theme, ano, formato)
        else:
            buffer = gerar_pdf_datada(ano, theme, layout, formato, com_agendamentos=False)

        nome = f"IA_Agenda_{page_type}_{formato}.pdf"
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
