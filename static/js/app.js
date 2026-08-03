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
            var isJuridica = tipo.value === 'juridica';
            var isCrista = tipo.value === 'crista';
            paginasField.style.display = (tipo.value === 'permanente') ? 'block' : 'none';
            var juridicaField = document.getElementById('juridica-field');
            if (juridicaField) {
                juridicaField.style.display = isJuridica ? 'block' : 'none';
            }
            var cristaField = document.getElementById('crista-field');
            if (cristaField) {
                cristaField.style.display = isCrista ? 'block' : 'none';
            }
            var layoutFieldEl = document.getElementById('layout-field');
            if (layoutFieldEl) layoutFieldEl.style.display = isJuridica ? 'none' : 'block';
            var estiloField = document.querySelector('.field input[name="estilo"]') ?
                document.getElementById('estilo-field') : null;
            if (estiloField) estiloField.style.display = (isJuridica || isCrista) ? 'none' : 'block';
            var bindingField = document.getElementById('binding-group');
            if (bindingField) bindingField.style.display = 'flex';
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
    var payload = {
        tipo: tipo, ano: ano, paginas: paginas, tema: tema,
        estilo: estilo, formato: formato, layout: layout,
        agendamentos: document.getElementById('agendamentos').checked,
        idioma: document.getElementById('idioma').value
    };
    if (tipo === 'juridica') {
        payload.estilo = 'juridico';
        var layoutEl = document.querySelector('input[name="juridica_layout"]:checked');
        payload.juridica_layout = layoutEl ? layoutEl.value : 'diaria';
        payload.juridica_agendamentos = document.getElementById('juridica_agendamentos') ? document.getElementById('juridica_agendamentos').checked : false;
        payload.juridica_maximas = document.getElementById('juridica_maximas') ? document.getElementById('juridica_maximas').checked : true;
        payload.juridica_anual = document.getElementById('juridica_anual') ? document.getElementById('juridica_anual').checked : true;
        payload.juridica_mensais = document.getElementById('juridica_mensais') ? document.getElementById('juridica_mensais').checked : true;
        payload.juridica_semanais = document.getElementById('juridica_semanais') ? document.getElementById('juridica_semanais').checked : true;
        payload.juridica_diarias = document.getElementById('juridica_diarias') ? document.getElementById('juridica_diarias').checked : true;
        payload.juridica_secoes_paginas = document.getElementById('juridica_secoes_paginas') ? document.getElementById('juridica_secoes_paginas').value : 2;
        var secoes = [];
        document.querySelectorAll('.juridica-secao:checked').forEach(function(cb) {
            secoes.push(cb.value);
        });
        payload.juridica_secoes = secoes;
    }
    if (tipo === 'crista') {
        payload.estilo = 'crista';
        payload.crista_agendamentos = document.getElementById('crista_agendamentos') ? document.getElementById('crista_agendamentos').checked : false;
    }
    payload.binding = _binding();
    return payload;
}

function _binding() {
    var el = document.querySelector('input[name="binding"]:checked');
    return el ? el.value : 'espiral';
}

function gerar() {
    var btn = document.getElementById('btn-gerar');
    var status = document.getElementById('status');
    var payload = _getPayload();
    var binding = _binding();
    var url;
    var suffix = '';
    if (payload.tipo === 'juridica') {
        if (binding === 'copta') { url = '/api/gerar-copta-juridica'; suffix = '_Juridica_Copta'; }
        else { url = '/gerar-juridica'; suffix = '_Juridica'; }
    } else if (payload.tipo === 'crista') {
        if (binding === 'copta') { url = '/api/gerar-copta-crista'; suffix = '_Crista_Copta'; }
        else { url = '/gerar-crista'; suffix = '_Crista'; }
    } else if (binding === 'copta') {
        url = '/api/gerar-copta';
        suffix = '_Copta';
    } else {
        url = '/gerar';
    }

    btn.disabled = true;
    status.textContent = 'Gerando PDF...';

    fetch(url, {
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
        a.download = 'Agenda' + suffix + '_' + payload.ano + '_' + payload.tema + '_' + payload.formato + '.pdf';
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
    var binding = _binding();
    var url;
    if (payload.tipo === 'juridica') {
        if (binding === 'copta') { url = '/api/preview-copta-juridica'; }
        else { url = '/preview-juridica'; }
    } else if (payload.tipo === 'crista') {
        if (binding === 'copta') { url = '/api/preview-copta-crista'; }
        else { url = '/preview-crista'; }
    } else if (binding === 'copta') {
        url = '/api/preview-copta';
    } else {
        url = '/preview';
    }
    btn.disabled = true;
    status.textContent = 'Carregando previa...';

    fetch(url, {
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
