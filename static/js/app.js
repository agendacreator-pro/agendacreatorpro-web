document.addEventListener('DOMContentLoaded', function() {
    var tipoRadios = document.querySelectorAll('input[name="tipo"]');
    var paginasField = document.getElementById('paginas-field');
    var formatoRadios = document.querySelectorAll('input[name="formato"]');
    var layoutField = document.getElementById('layout-field');
    var layoutRadios = document.querySelectorAll('input[name="layout"]');

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

    atualizarPaginas();
    atualizarLayout();
});

function gerar() {
    var btn = document.getElementById('btn-gerar');
    var status = document.getElementById('status');

    var tipo = document.querySelector('input[name="tipo"]:checked').value;
    var ano = document.getElementById('ano').value;
    var paginas = document.getElementById('paginas').value;
    var tema = document.querySelector('input[name="tema"]:checked') ? document.querySelector('input[name="tema"]:checked').value : 'rosa';
    var temaSelect = document.getElementById('tema');
    if (temaSelect) tema = temaSelect.value;
    var estilo = document.querySelector('input[name="estilo"]:checked').value;
    var formato = document.querySelector('input[name="formato"]:checked').value;
    var layout = document.querySelector('input[name="layout"]:checked').value;
    var logoFile = document.getElementById('logo').files[0];

    var payload = {
        tipo: tipo,
        ano: ano,
        paginas: paginas,
        tema: tema,
        estilo: estilo,
        formato: formato,
        layout: layout,
        agendamentos: document.getElementById('agendamentos').checked,
        idioma: document.getElementById('idioma').value
    };

    btn.disabled = true;
    status.textContent = 'Gerando PDF...';

    if (logoFile) {
        var formData = new FormData();
        formData.append('logo', logoFile);
        formData.append('data', JSON.stringify(payload));

        fetch('/gerar', {
            method: 'POST',
            body: formData
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
            a.download = 'Agenda_' + ano + '_' + tema + '_' + formato + '.pdf';
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
    } else {
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
            a.download = 'Agenda_' + ano + '_' + tema + '_' + formato + '.pdf';
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
}

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

function _getFetchOptions(payload) {
    var logoFile = document.getElementById('logo').files[0];
    if (logoFile) {
        var formData = new FormData();
        formData.append('logo', logoFile);
        formData.append('data', JSON.stringify(payload));
        return { method: 'POST', body: formData };
    }
    return { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) };
}

function preview() {
    var btn = document.getElementById('btn-preview');
    var status = document.getElementById('status');
    var payload = _getPayload();
    btn.disabled = true;
    status.textContent = 'Carregando previa...';

    fetch('/preview', _getFetchOptions(payload))
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
