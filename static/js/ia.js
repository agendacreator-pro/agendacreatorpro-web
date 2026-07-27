let selectedFile = null;
let extractedPalette = null;
let imageDataUrl = null;

document.addEventListener("DOMContentLoaded", () => {
  const zone = document.getElementById("uploadZone");
  const input = document.getElementById("fileInput");
  const btnGenerate = document.getElementById("btnGenerate");

  zone.addEventListener("click", () => input.click());
  zone.addEventListener("dragover", e => { e.preventDefault(); zone.classList.add("dragover"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("dragover");
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
  });
  input.addEventListener("change", () => { if (input.files.length) handleFile(input.files[0]); });
  btnGenerate.addEventListener("click", generateProject);
});

function handleFile(file) {
  const allowed = ["image/png", "image/jpeg", "image/jpg"];
  if (!allowed.includes(file.type)) {
    alert("Formato nao suportado. Use PNG ou JPG.");
    return;
  }
  if (file.size > 20 * 1024 * 1024) {
    alert("Arquivo muito grande. Maximo: 20MB.");
    return;
  }
  selectedFile = file;

  const reader = new FileReader();
  reader.onload = e => {
    document.getElementById("previewImage").src = e.target.result;
    document.getElementById("fileInfo").textContent = `${file.name} — ${(file.size / 1024).toFixed(1)}KB`;
    document.getElementById("previewContainer").style.display = "block";
    document.getElementById("btnAnalyze").classList.add("active");
  };
  reader.readAsDataURL(file);
}

function startAnalysis() {
  if (!selectedFile) return;

  document.getElementById("uploadZone").style.display = "none";
  document.getElementById("previewContainer").style.display = "none";
  document.getElementById("btnAnalyze").style.display = "none";
  document.getElementById("providerSelect").parentElement.style.display = "none";
  document.getElementById("progressContainer").style.display = "block";
  document.getElementById("progressBar").style.width = "30%";
  document.getElementById("progressStage").textContent = "Extraindo cores da imagem...";

  const formData = new FormData();
  formData.append("image", selectedFile);

  fetch("/api/ia/analyze", {
    method: "POST",
    body: formData,
  }).then(r => r.json()).then(data => {
    if (!data.success) {
      showError(data.error || "Erro ao extrair cores");
      return;
    }
    extractedPalette = data.palette;
    imageDataUrl = data.image_data_url;
    document.getElementById("progressBar").style.width = "100%";
    document.getElementById("progressStage").textContent = "Cores extraidas!";
    setTimeout(() => showColorResult(data), 500);
  }).catch(err => showError(err.message));
}

function showColorResult(data) {
  document.getElementById("progressContainer").style.display = "none";
  document.getElementById("resultContainer").style.display = "block";

  if (data.image_data_url) {
    document.getElementById("resultOriginalImage").src = data.image_data_url;
    document.getElementById("resultImageCompare").style.display = "block";
  }

  const palette = data.palette;
  const paletteDiv = document.getElementById("colorPalette");
  paletteDiv.innerHTML = "";
  const labels = {
    accent: "Destaque", primary: "Principal", text: "Texto",
    border: "Borda", highlight: "Fundo destaque", secondary: "Secundario", background: "Fundo"
  };
  for (const [key, hex] of Object.entries(palette)) {
    const swatch = document.createElement("div");
    swatch.style.cssText = "text-align:center;";
    swatch.innerHTML = `
      <div style="width:40px;height:40px;border-radius:8px;border:2px solid #eee;background:${hex};margin:0 auto 4px;"></div>
      <div style="font-size:0.7rem;color:#666;">${labels[key] || key}</div>
      <div style="font-size:0.65rem;color:#999;font-family:monospace;">${hex}</div>
    `;
    paletteDiv.appendChild(swatch);
  }

  document.getElementById("resultDescription").textContent = "Cores extraidas da sua imagem. Escolha o formato e gere sua agenda!";

  if (data.image_info) {
    const info = document.getElementById("imageInfo");
    if (info) info.textContent = `${data.image_info.width}x${data.image_info.height}px`;
  }
}

function generateProject() {
  if (!extractedPalette) return;
  const btn = document.getElementById("btnGenerate");
  btn.textContent = "Gerando...";
  btn.style.opacity = "0.6";
  btn.style.pointerEvents = "none";

  const formato = document.getElementById("formatSelect").value;
  const numPages = parseInt(document.getElementById("numPages").value) || 30;
  const layout = document.getElementById("layoutSelect").value;

  fetch("/api/ia/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      formato: formato,
      num_pages: numPages,
      layout: layout,
      palette: extractedPalette,
    }),
  }).then(r => r.blob()).then(blob => {
    if (blob.size < 100) {
      blob.text().then(t => { alert(t); resetBtn(); });
      return;
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Agenda_${layout.toUpperCase()}_${formato}.pdf`;
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
    btn.textContent = "Gerar Agenda";
    btn.style.opacity = "1";
    btn.style.pointerEvents = "all";
  }
}

function resetIA() {
  selectedFile = null;
  extractedPalette = null;
  imageDataUrl = null;
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
}

function showError(msg) {
  document.getElementById("progressContainer").style.display = "none";
  document.getElementById("errorContainer").style.display = "block";
  document.getElementById("errorMessage").textContent = msg;
}
