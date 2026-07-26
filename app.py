import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from flask import Flask, render_template, send_file, request, jsonify

from themes import (
    RosaTheme, AzulTheme, VerdeTheme, AmareloTheme,
    LaranjaTheme, VermelhoTheme, LilasTheme, PretoTheme
)

from pdf_generator import gerar_pdf_datada, gerar_pdf_permanente

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

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


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/gerar', methods=['POST'])
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

        tema_cls = TEMAS.get(tema_nome, RosaTheme)
        tema = tema_cls()

        from styles.manager import definir as definir_estilo
        definir_estilo(estilo)

        if tipo == 'datada':
            buffer = gerar_pdf_datada(ano, tema, layout, formato)
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
    app.run(debug=True, host='0.0.0.0', port=5000)
