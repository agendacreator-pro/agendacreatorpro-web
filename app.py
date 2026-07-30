import sys
import os
import json
import secrets
import base64

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from flask import Flask, render_template, send_file, request, jsonify, redirect, url_for
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
    'aline.277@hotmail.com': {
        'email': 'aline.277@hotmail.com',
        'password': generate_password_hash('Matheus13'),
        'token': '',
        'ativo': True,
    },
    'meellcriativa@gmail.com': {
        'email': 'meellcriativa@gmail.com',
        'password': generate_password_hash('Gean3691*'),
        'token': '',
        'ativo': True,
    },
    'somarisil@gmail.com': {
        'email': 'somarisil@gmail.com',
        'password': generate_password_hash('12345678'),
        'token': '',
        'ativo': True,
    },
    'auristelaferreira924@gmail.com': {
        'email': 'auristelaferreira924@gmail.com',
        'password': generate_password_hash('35407010'),
        'token': '',
        'ativo': True,
    },
}

_users_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.json')
if os.path.exists(_users_file):
    try:
        with open(_users_file, 'r', encoding='utf-8') as f:
            _data = json.load(f)
        for u in _data.get('users', []):
            key = u['email'].lower()
            if u.get('ativo') and 'password' in u:
                USERS[key] = u
        print(f"[STARTUP] Loaded {len(USERS)} users from users.json")
        print(f"[STARTUP] Users: {list(USERS.keys())}")
    except Exception as e:
        print(f"[STARTUP] Could not load users.json: {e}")


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
    print(f"[LOGIN FAIL] email={email} found={user is not None} active={user.get('ativo') if user else '-'}")
    return jsonify({'success': False, 'message': 'E-mail ou senha incorretos'})


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing'))


@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.json
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    confirm = data.get('confirm', '')

    user = find_user(current_user.id)
    if not user:
        return jsonify({'success': False, 'message': 'Usuario nao encontrado'})

    if not check_password_hash(user['password'], old_password):
        return jsonify({'success': False, 'message': 'Senha atual incorreta'})

    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'Nova senha deve ter no minimo 6 caracteres'})

    if new_password != confirm:
        return jsonify({'success': False, 'message': 'As senhas nao coincidem'})

    user['password'] = generate_password_hash(new_password)
    _save_users()
    return jsonify({'success': True, 'message': 'Senha alterada com sucesso'})


def _save_users():
    path = os.path.join(os.path.dirname(__file__), 'users.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'users': list(USERS.values())}, f, indent=2, ensure_ascii=False)


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
            buffer = gerar_pdf_permanente(paginas, tema, ano, formato, com_agendamentos=com_agendamentos)
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


@app.route('/ia')
@login_required
def ia_creator():
    return render_template('ia_creator.html')


@app.route('/api/ia/analyze', methods=['POST'])
@login_required
def ia_analyze():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image = request.files['image']

    allowed = {'image/png', 'image/jpeg', 'image/jpg', 'application/pdf'}
    if image.content_type not in allowed:
        return jsonify({"error": "Format not supported"}), 400

    image_bytes = image.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        return jsonify({"error": "File too large (max 20MB)"}), 400

    try:
        from ai.color_extractor import extract_image_info
        info = extract_image_info(image_bytes)
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        ct = image.content_type or "image/png"
        return jsonify({
            "success": True,
            "palette": info["palette"],
            "image_info": {
                "width": info["width"],
                "height": info["height"],
                "aspect_ratio": info["aspect_ratio"],
            },
            "image_data_url": f"data:{ct};base64,{image_b64}",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/ia/generate', methods=['POST'])
@login_required
def ia_generate():
    try:
        data = request.json
        formato = data.get('formato', 'A5')
        num_pages = int(data.get('num_pages', 7) or 7)
        layout = data.get('layout', '2dpp')
        style = data.get('style', 'minimalista')
        palette = data.get('palette', {})

        if not palette:
            return jsonify({"error": "No palette data"}), 400

        from ai.blueprint_generator import gerar_pdf_blueprint
        from datetime import date
        base = date(2026, 1, 1)

        blueprint = {
            "page_type": layout,
            "style": style,
            "palette": palette,
            "editable_objects": [],
            "sections": [],
        }

        buffer = gerar_pdf_blueprint(blueprint, formato=formato, num_pages=num_pages, base_date=base)
        nome = f"Agenda_{layout.upper()}_{formato}.pdf"
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=nome)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
