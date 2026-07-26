const STAGE_MAP = {
  upload: "step-upload",
  cache: "step-cache",
  ocr: "step-ocr",
  elements: "step-elements",
  colors: "step-colors",
  structure: "step-structure",
  complete: "step-complete",
};

let selectedFile = null;
let analysisResult = null;

document.addEventListener("DOMContentLoaded", () => {
  const zone = document.getElementById("uploadZone");
  const input = document.getElementById("fileInput");
  const btnAnalyze = document.getElementById("btnAnalyze");
  const btnGenerate = document.getElementById("btnGenerate");

  zone.addEventListener("click", () => input.click());

  zone.addEventListener("dragover", e => {
    e.preventDefault();
    zone.classList.add("dragover");
  });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("dragover");
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
  });

  input.addEventListener("change", () => {
    if (input.files.length) handleFile(input.files[0]);
  });

  btnAnalyze.addEventListener("click", startAnalysis);
  btnGenerate.addEventListener("click", generateProject);
});

function handleFile(file) {
  const allowed = ["image/png", "image/jpeg", "image/jpg", "application/pdf"];
  if (!allowed.includes(file.type)) {
    alert("Formato não suportado. Use PNG, JPG ou PDF.");
    return;
  }
  if (file.size > 20 * 1024 * 1024) {
    alert("Arquivo muito grande. Máximo: 20MB.");
    return;
  }

  selectedFile = file;

  const reader = new FileReader();
  reader.onload = e => {
    const img = document.getElementById("previewImage");
    const info = document.getElementById("fileInfo");
    if (file.type === "application/pdf") {
      img.src = "/static/img/pdf-icon.png";
      img.style.maxHeight = "200px";
    } else {
      img.src = e.target.result;
      img.style.maxHeight = "400px";
    }
    info.textContent = `${file.name} — ${(file.size / 1024).toFixed(1)}KB`;
    document.getElementById("previewContainer").style.display = "block";
    document.getElementById("btnAnalyze").classList.add("active");
  };
  reader.readAsDataURL(file);
}

function startAnalysis() {
  if (!selectedFile) return;

  const provider = document.getElementById("providerSelect").value;
  const formData = new FormData();
  formData.append("image", selectedFile);
  formData.append("provider", provider);

  document.getElementById("uploadZone").style.display = "none";
  document.getElementById("previewContainer").style.display = "none";
  document.getElementById("btnAnalyze").style.display = "none";
  document.getElementById("providerSelect").parentElement.style.display = "none";
  document.getElementById("progressContainer").style.display = "block";

  fetch("/api/ia/analyze", {
    method: "POST",
    body: formData,
  }).then(res => res.json()).then(data => {
    if (!data.success) {
      showError(data.error || "Erro desconhecido");
      return;
    }

    const eventSource = new EventSource(`/api/ia/stream/${data.task_id}`);
    eventSource.onmessage = e => {
      const msg = JSON.parse(e.data);
      updateProgress(msg.progress, msg.stage, msg.message);
      if (msg.stage === "complete" || msg.progress >= 100) {
        eventSource.close();
        fetchResult(data.task_id);
      }
    };
    eventSource.onerror = () => {
      eventSource.close();
      fetchResult(data.task_id);
    };
  }).catch(err => showError(err.message));
}

function updateProgress(pct, stage, message) {
  document.getElementById("progressBar").style.width = pct + "%";
  document.getElementById("progressStage").textContent = message;

  const stepId = STAGE_MAP[stage];
  if (stepId) {
    document.getElementById(stepId).classList.add("active");
    document.querySelectorAll(".progress-step").forEach(el => {
      if (el.id !== stepId && !el.classList.contains("done")) return;
      if (el.id !== stepId) {
        el.classList.remove("active");
        el.classList.add("done");
      }
    });
  }
}

function fetchResult(taskId) {
  fetch(`/api/ia/result/${taskId}`)
    .then(r => r.json())
    .then(data => {
      if (!data.success) {
        showError(data.error || "Erro ao obter resultado");
        return;
      }
      showResult(data);
    })
    .catch(err => showError(err.message));
}

function showResult(data) {
  document.getElementById("progressContainer").style.display = "none";
  document.getElementById("resultContainer").style.display = "block";
  analysisResult = data;

  if (data.image_data_url) {
    document.getElementById("resultOriginalImage").src = data.image_data_url;
    document.getElementById("resultImageCompare").style.display = "block";
  }

  const pa = data.page_analysis;
  const badge = document.getElementById("resultBadge");
  const conf = (pa.confidence * 100).toFixed(0);
  const confClass = pa.confidence >= 0.7 ? "" : "warning";
  badge.innerHTML = `<span class="result-badge ${confClass}">${pa.page_type_label} — ${conf}% confianca</span>`;

  document.getElementById("resultDescription").textContent =
    pa.description || `Layout detectado: ${pa.page_type_label}`;

  const palette = document.getElementById("colorPalette");
  palette.innerHTML = "";
  (pa.colors || []).forEach(c => {
    const swatch = document.createElement("div");
    swatch.className = "color-swatch";
    swatch.style.backgroundColor = c.hex;
    swatch.title = `${c.name}: ${c.hex}`;
    palette.appendChild(swatch);
  });

  document.getElementById("fontsDetected").textContent =
    (pa.fonts_detected || []).join(", ") || "Nao detectado";

  const elements = pa.elements || [];
  document.getElementById("elementCount").textContent = elements.length;

  const elList = document.getElementById("elementsList");
  elList.innerHTML = "";
  elements.forEach(el => {
    const row = document.createElement("div");
    row.className = "result-element";
    const txt = el.text ? `"${el.text.substring(0,30)}"` : el.type;
    row.innerHTML = `
      <span class="type-badge">${el.type}</span>
      <span>${txt} (${el.x.toFixed(1)}, ${el.y.toFixed(1)}) ${el.w.toFixed(0)}×${el.h.toFixed(0)}mm</span>
    `;
    elList.appendChild(row);
  });

  document.getElementById("inferredPages").textContent =
    (pa.inferred_pages || []).join(", ") || "Nenhuma pagina adicional inferida";
}

function generateProject() {
  if (!analysisResult) return;
  const btn = document.getElementById("btnGenerate");
  btn.textContent = "Gerando...";
  btn.style.opacity = "0.6";
  btn.style.pointerEvents = "none";

  const pa = analysisResult.page_analysis || {};
  const formato = document.getElementById("formatSelect") ? document.getElementById("formatSelect").value : "A5";
  const payload = {
    formato: formato,
    page_analysis: pa
  };

  fetch("/api/ia/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(r => r.blob()).then(blob => {
    if (blob.size < 100) {
      blob.text().then(t => { alert(t); resetBtn(); });
      return;
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "IA_Agenda.pdf";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    resetBtn();
  }).catch(err => {
    alert("Erro: " + err.message);
    resetBtn();
  });

  function resetBtn() {
    btn.textContent = "Gerar Projeto Completo";
    btn.style.opacity = "1";
    btn.style.pointerEvents = "all";
  }
}

function resetIA() {
  selectedFile = null;
  analysisResult = null;
  document.getElementById("uploadZone").style.display = "block";
  document.getElementById("previewContainer").style.display = "none";
  document.getElementById("progressContainer").style.display = "none";
  document.getElementById("resultContainer").style.display = "none";
  document.getElementById("errorContainer").style.display = "none";
  document.getElementById("btnAnalyze").style.display = "inline-block";
  document.getElementById("btnAnalyze").classList.remove("active");
  document.getElementById("providerSelect").parentElement.style.display = "block";
  document.getElementById("fileInput").value = "";
  document.getElementById("progressBar").style.width = "0%";
  document.querySelectorAll(".progress-step").forEach(el => {
    el.classList.remove("active", "done");
  });
}

function showError(msg) {
  document.getElementById("progressContainer").style.display = "none";
  document.getElementById("errorContainer").style.display = "block";
  document.getElementById("errorMessage").textContent = msg;
}
