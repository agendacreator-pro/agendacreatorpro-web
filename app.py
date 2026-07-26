import sys
import os
import json
import uuid
import secrets
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from flask import Flask, render_template, send_file, request, jsonify, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from themes import (
    RosaTheme, AzulTheme, VerdeTheme, AmareloTheme,
    LaranjaTheme, VermelhoTheme, LilasTheme, PretoTheme
)

from pdf_generator import gerar_pdf_datada, gerar_pdf_permanente

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'agendacreatorpro-secret-key-change-in-prod')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'agendacreatorpro-webhook-secret')


def load_users_data():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": []}


def save_users_data(data):
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def find_user(email):
    data = load_users_data()
    for u in data['users']:
        if u['email'].lower() == email.lower():
            return u
    return None


def find_user_by_token(token):
    data = load_users_data()
    for u in data['users']:
        if u.get('access_token') == token and u.get('ativo', True):
            return u
    return None


def create_user(email, token=None):
    data = load_users_data()
    existing = [u for u in data['users'] if u['email'].lower() == email.lower()]
    if existing:
        if token:
            existing[0]['access_token'] = token
            save_users_data(data)
        return existing[0]

    if not token:
        token = secrets.token_urlsafe(32)

    user = {
        'email': email,
        'password': generate_password_hash(token),
        'access_token': token,
        'ativo': True,
        'criado_em': datetime.now().isoformat()
    }
    data['users'].append(user)
    save_users_data(data)
    return user


class User(UserMixin):
    def __init__(self, email):
        self.id = email
        self.email = email


@login_manager.user_loader
def load_user(email):
    user = find_user(email)
    if user and user.get('ativo', True):
        return User(email)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    if request.is_json or request.path == '/gerar':
        return jsonify({'error': 'Acesso nao autorizado'}), 401
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
    if user and user.get('ativo', True):
        if check_password_hash(user['password'], password):
            login_user(User(user['email']))
            return jsonify({'success': True, 'redirect': '/'})
        else:
            return jsonify({'success': False, 'message': 'Senha incorreta'})
    return jsonify({'success': False, 'message': 'E-mail nao encontrado'})


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing'))


@app.route('/app')
@login_required
def index():
    return render_template('index.html')


@app.route('/admin/users')
@login_required
def admin_users():
    data = load_users_data()
    return jsonify(data['users'])


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
        'token': user['access_token'],
        'link': f"{request.host_url}auth?token={user['access_token']}"
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
        return jsonify({'error': 'Email not found in payload'}), 400

    user = create_user(email)

    return jsonify({
        'success': True,
        'email': user['email'],
        'token': user['access_token']
    })


TEMAS = {
    "rosa": RosaTheme,
    "azul": AzulTheme,
    "verde": VerdeTheme,
    "amarelo": AmareloTheme,
    "laranja": LaranjaTheme,
    "vermelho": VermelhoTheme,
    "lilas": LilasTheme,
    "preto": PretoTheme,
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

        tema_cls = TEMAS.get(tema_nome, RosaTheme)
        tema = tema_cls()

        from styles.manager import definir as definir_estilo
        definir_estilo(estilo)

        if tipo == 'datada':
            buffer = gerar_pdf_datada(ano, tema, layout, formato, com_agendamentos=com_agendamentos)
            nome = f"Agenda_{ano}_{tema_nome}_{formato}.pdf"
        else:
            buffer = gerar_pdf_permanente(paginas, tema, ano, formato)
            nome = f"Agenda_Permanente_{tema_nome}_{formato}.pdf"

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=nome
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
