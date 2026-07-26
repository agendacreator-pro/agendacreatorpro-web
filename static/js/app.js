document.addEventListener('DOMContentLoaded', function() {
    var tipoRadios = document.querySelectorAll('input[name="tipo"]');
    var paginasField = document.getElementById('paginas-field');
    var formatoRadios = document.querySelectorAll('input[name="formato"]');
    var layoutField = document.getElementById('layout-field');
    var layoutRadios = document.querySelectorAll('input[name="layout"]');
    var idiomaSelect = document.getElementById('idioma');

    function aplicarTraducoes() {
        var lang = idiomaSelect.value;
        var t = UI_TRANSLATIONS[lang] || UI_TRANSLATIONS['pt'];
        document.querySelectorAll('[data-i18n]').forEach(function(el) {
            var key = el.getAttribute('data-i18n');
            if (t[key]) el.textContent = t[key];
        });
        document.querySelectorAll('[data-i18n-opt]').forEach(function(opt) {
            var key = opt.getAttribute('data-i18n-opt');
            if (t[key]) opt.textContent = t[key];
        });
    }

    function atualizarPaginas() {
        var tipo = document.querySelector('input[name="tipo"]:checked');
        if (tipo) {
            paginasField.style.display = tipo.value === 'permanente' ? 'block' : 'none';
        }
    }

    function atualizarLayout() {
        var formato = document.querySelector('input[name="formato"]:checked');
        if (formato && formato.value === 'QUADRADO') {
            layoutRadios.forEach(function(r) {
                if (r.value === '2') r.disabled = true;
                else { r.checked = true; r.disabled = false; }
            });
        } else {
            layoutRadios.forEach(function(r) { r.disabled = false; });
        }
    }

    tipoRadios.forEach(function(radio) {
        radio.addEventListener('change', atualizarPaginas);
    });

    formatoRadios.forEach(function(radio) {
        radio.addEventListener('change', atualizarLayout);
    });

    idiomaSelect.addEventListener('change', aplicarTraducoes);

    atualizarPaginas();
    atualizarLayout();
    aplicarTraducoes();
});

function _getPayload() {
    var tipo = document.querySelector('input[name="tipo"]:checked').value;
    var ano = document.getElementById('ano').value;
    var paginas = document.getElementById('paginas').value;
    var tema = document.getElementById('tema') ? document.getElementById('tema').value : 'rosa';
    var estilo = document.querySelector('input[name="estilo"]:checked').value;
    var formato = document.querySelector('input[name="formato"]:checked').value;
    var layout = document.querySelector('input[name="layout"]:checked').value;
    return {
        tipo: tipo, ano: ano, paginas: paginas, tema: tema,
        estilo: estilo, formato: formato, layout: layout,
        agendamentos: document.getElementById('agendamentos').checked,
        idioma: document.getElementById('idioma').value
    };
}

function gerar() {
    var btn = document.getElementById('btn-gerar');
    var status = document.getElementById('status');
    var payload = _getPayload();

    btn.disabled = true;
    status.textContent = 'Gerando PDF...';

    fetch('/gerar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(function(response) {
        if (response.status === 401) { window.location.href = '/login'; return; }
        if (!response.ok) throw new Error('Erro ao gerar PDF');
        return response.blob();
    })
    .then(function(blob) {
        if (!blob) return;
        var url = window.URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'Agenda_' + payload.ano + '_' + payload.tema + '_' + payload.formato + '.pdf';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        status.textContent = 'PDF gerado com sucesso!';
        btn.disabled = false;
    })
    .catch(function(err) {
        status.textContent = 'Erro: ' + err.message;
        btn.disabled = false;
    });
}

function preview() {
    var btn = document.getElementById('btn-preview');
    var status = document.getElementById('status');
    var payload = _getPayload();
    btn.disabled = true;
    status.textContent = 'Carregando previa...';

    fetch('/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(function(response) {
        if (response.status === 401) { window.location.href = '/login'; return; }
        if (!response.ok) throw new Error('Erro ao gerar previa');
        return response.blob();
    })
    .then(function(blob) {
        if (!blob) return;
        var url = window.URL.createObjectURL(blob);
        document.getElementById('previewFrame').src = url;
        document.getElementById('previewModal').style.display = 'flex';
        status.textContent = '';
        btn.disabled = false;
    })
    .catch(function(err) {
        status.textContent = 'Erro: ' + err.message;
        btn.disabled = false;
    });
}

function closePreview() {
    document.getElementById('previewModal').style.display = 'none';
    document.getElementById('previewFrame').src = '';
}

function downloadFromPreview() {
    gerar();
    closePreview();
}
