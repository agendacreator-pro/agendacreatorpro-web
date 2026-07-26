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
    var tema = document.getElementById('tema').value;
    var estilo = document.querySelector('input[name="estilo"]:checked').value;
    var formato = document.querySelector('input[name="formato"]:checked').value;
    var layout = document.querySelector('input[name="layout"]:checked').value;

    var payload = {
        tipo: tipo,
        ano: ano,
        paginas: paginas,
        tema: tema,
        estilo: estilo,
        formato: formato,
        layout: layout
    };

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
