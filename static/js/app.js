// SnapGuard Client Application Logic

let selectedFile = null;
let currentScanData = null;
let webcamStream = null;

document.addEventListener('DOMContentLoaded', () => {
    loadAppInfo();
    setupDropzone();
});

// Tab Navigation
function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    const activeTab = document.getElementById(`tab-${tabName}`);
    if (activeTab) {
        activeTab.style.display = 'block';
    }

    const activeBtn = Array.from(document.querySelectorAll('.nav-btn')).find(b => {
        const onclickAttr = b.getAttribute('onclick');
        return onclickAttr && onclickAttr.includes(tabName);
    });
    if (activeBtn) {
        activeBtn.classList.add('active');
    }

    if (tabName !== 'scan') {
        stopWebcamStream();
    }

    if (tabName === 'history') {
        loadHistory();
    }
}

// Scan Mode Switcher (Upload vs Camera vs Demo)
function switchScanMode(mode) {
    document.getElementById('scanModeUpload').style.display = (mode === 'upload') ? 'block' : 'none';
    document.getElementById('scanModeCamera').style.display = (mode === 'camera') ? 'block' : 'none';
    document.getElementById('scanModeDemo').style.display = (mode === 'demo') ? 'block' : 'none';

    document.getElementById('btnModeUpload').className = (mode === 'upload') ? 'btn-primary' : 'btn-secondary';
    document.getElementById('btnModeCamera').className = (mode === 'camera') ? 'btn-primary' : 'btn-secondary';
    document.getElementById('btnModeDemo').className = (mode === 'demo') ? 'btn-primary' : 'btn-secondary';

    if (mode !== 'camera') {
        stopWebcamStream();
    }
}

// Live Camera Controls
async function startWebcam() {
    const video = document.getElementById('webcamVideo');
    const statusMsg = document.getElementById('cameraStatusMsg');
    const btnStart = document.getElementById('btnStartCamera');
    const btnCapture = document.getElementById('btnCapturePhoto');
    const btnReset = document.getElementById('btnResetCamera');
    const snapshotImg = document.getElementById('cameraSnapshotPreview');

    snapshotImg.style.display = 'none';

    try {
        statusMsg.innerText = "Requesting camera access...";
        let stream = null;
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 1280 }, height: { ideal: 720 } } });
        } catch (e1) {
            console.warn("Fallback to simple video constraint...", e1);
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
        }

        webcamStream = stream;
        video.srcObject = webcamStream;
        video.style.display = 'inline-block';
        statusMsg.innerText = "Camera active. Align document in frame and click 'CAPTURE & SCAN PHOTO'.";
        btnStart.style.display = 'none';
        btnCapture.style.display = 'inline-block';
        btnReset.style.display = 'inline-block';
    } catch (err) {
        console.error("Webcam error:", err);
        statusMsg.innerHTML = `<span style="color: var(--color-critical); font-weight: 600;">⚠️ Camera Stream Access Unavailable (${err.name}: ${err.message})</span><br><span style="color: var(--text-muted); font-size: 13px;">Click <strong>"📸 SNAP / UPLOAD CAMERA PHOTO"</strong> below to take or pick a camera photo directly!</span>`;
    }
}

function handleCameraFileSelect(e) {
    if (e.target.files && e.target.files.length > 0) {
        const file = e.target.files[0];
        selectedFile = file;
        const statusMsg = document.getElementById('cameraStatusMsg');
        if (statusMsg) statusMsg.innerText = `Camera photo selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB). Scanning...`;
        uploadAndScan();
    }
}

function captureWebcamFrame() {
    const video = document.getElementById('webcamVideo');
    const canvas = document.getElementById('webcamCanvas');
    const snapshotImg = document.getElementById('cameraSnapshotPreview');
    const statusMsg = document.getElementById('cameraStatusMsg');

    if (!webcamStream || video.videoWidth === 0) {
        alert("Camera stream is not ready.");
        return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL('image/png');
    snapshotImg.src = dataUrl;
    snapshotImg.style.display = 'inline-block';
    video.style.display = 'none';

    canvas.toBlob(async (blob) => {
        if (!blob) return;
        const file = new File([blob], "camera_snapshot.png", { type: "image/png" });
        selectedFile = file;
        statusMsg.innerText = "Snapshot captured! Running local AI privacy scan...";
        stopWebcamStream();
        await uploadAndScan();
    }, 'image/png');
}

function resetWebcam() {
    stopWebcamStream();
    document.getElementById('cameraSnapshotPreview').style.display = 'none';
    document.getElementById('webcamVideo').style.display = 'none';
    document.getElementById('cameraStatusMsg').innerText = "Camera reset. Click 'OPEN WEBCAM STREAM' or use 'SNAP / UPLOAD CAMERA PHOTO'.";
    document.getElementById('btnStartCamera').style.display = 'inline-block';
    document.getElementById('btnCapturePhoto').style.display = 'none';
    document.getElementById('btnResetCamera').style.display = 'none';
}

function stopWebcamStream() {
    if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
        webcamStream = null;
    }
}

// Fetch App Stats & Hardware Info
async function loadAppInfo() {
    try {
        const res = await fetch('/api/info');
        const data = await res.json();
        
        document.getElementById('metricScansToday').innerText = data.stats.scans_today || 0;
        document.getElementById('metricRisksFound').innerText = data.stats.risks_found || 0;
        document.getElementById('metricFilesProtected').innerText = data.stats.files_protected || 0;
        document.getElementById('metricTotalScans').innerText = data.stats.total_scans || 0;

        document.getElementById('hwProcessor').innerText = data.hardware.processor;
        document.getElementById('hwInference').innerText = data.hardware.inference;
        document.getElementById('hwAcceleration').innerText = data.hardware.acceleration;
        document.getElementById('hwHubReady').innerText = data.hardware.qualcomm_ai_hub_ready ? "🟢 Active & Compatible" : "⚪ Unavailable";
    } catch (e) {
        console.error('Failed to fetch info:', e);
    }
}

// Drag & Drop Handling
function setupDropzone() {
    const dz = document.getElementById('dropzone');
    if (!dz) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        dz.addEventListener(eventName, (e) => {
            e.preventDefault();
            dz.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dz.addEventListener(eventName, (e) => {
            e.preventDefault();
            dz.classList.remove('dragover');
        }, false);
    });

    dz.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

function handleFileSelect(e) {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
}

function handleFile(file) {
    selectedFile = file;
    document.getElementById('selectedFileInfo').innerText = `Selected File: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    document.getElementById('btnStartScan').disabled = false;
}

// Upload & Run Scan Pipeline
async function uploadAndScan() {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    showScanProgressAnimation();

    try {
        const res = await fetch('/api/scan', {
            method: 'POST',
            body: formData
        });
        if (!res.ok) {
            const errData = await res.json().catch(() => ({ detail: res.statusText }));
            throw new Error(errData.detail || errData.error || "Processing failed");
        }
        const data = await res.json();
        hideScanProgressAnimation();
        renderResults(data);
        showTab('results');
        loadAppInfo();
    } catch (e) {
        alert('Scan Error: ' + e.message);
        hideScanProgressAnimation();
    }
}

// Run Competition Demo Sample
async function runDemo(sampleName) {
    showTab('scan');
    showScanProgressAnimation();

    try {
        const res = await fetch(`/api/scan-demo/${sampleName}`, { method: 'POST' });
        if (!res.ok) {
            const errData = await res.json().catch(() => ({ detail: res.statusText }));
            throw new Error(errData.detail || errData.error || "Demo scan failed");
        }
        const data = await res.json();
        hideScanProgressAnimation();
        renderResults(data);
        showTab('results');
        loadAppInfo();
    } catch (e) {
        alert('Demo Scan Error: ' + e.message);
        hideScanProgressAnimation();
    }
}

function showScanProgressAnimation() {
    const card = document.getElementById('scanProgressCard');
    card.style.display = 'block';

    ['step1', 'step2', 'step3', 'step4'].forEach((stepId, idx) => {
        setTimeout(() => {
            document.querySelectorAll('.progress-step').forEach(s => s.classList.remove('active'));
            const s = document.getElementById(stepId);
            s.classList.add('active');
            if (idx > 0) {
                document.getElementById(`step${idx}`).classList.add('done');
            }
        }, idx * 600);
    });
}

function hideScanProgressAnimation() {
    document.getElementById('scanProgressCard').style.display = 'none';
}

// Render Results & Scoring
function renderResults(data) {
    currentScanData = data;

    document.getElementById('resFileName').innerText = `🛡️ SECURITY ANALYSIS: ${data.filename}`;
    document.getElementById('resMeta').innerText = `Scan duration: ${data.processing_time} sec | Items found: ${data.findings.length}`;

    const riskInfo = data.risk_analysis;
    const score = riskInfo.security_score;
    const scoreNumEl = document.getElementById('resScoreNum');
    scoreNumEl.innerText = `${score} / 100`;

    const riskBadgeEl = document.getElementById('resRiskBadge');
    riskBadgeEl.innerText = riskInfo.risk_level;
    riskBadgeEl.className = `badge badge-${riskInfo.risk_level.toLowerCase()}`;

    const scoreBoxEl = document.getElementById('resScoreBox');
    let borderColor = "#4ade80";
    if (score < 50) borderColor = "#ff4d4f";
    else if (score < 75) borderColor = "#ffa940";
    else if (score < 95) borderColor = "#ffec3d";
    scoreBoxEl.style.borderColor = borderColor;

    document.getElementById('resSummary').innerText = riskInfo.summary;

    // Display OCR text
    const ocrTextView = document.getElementById('ocrTextView');
    if (ocrTextView) {
        if (data.full_text && data.full_text.trim()) {
            ocrTextView.innerText = data.full_text;
        } else {
            ocrTextView.innerText = "No readable text detected.";
        }
    }

    renderFindingsList(data.findings);

    // Image Preview
    const imgEl = document.getElementById('previewImage');
    const noImgText = document.getElementById('noImageText');
    if (data.preview_image) {
        imgEl.src = data.preview_image;
        imgEl.style.display = 'inline-block';
        noImgText.style.display = 'none';
    } else {
        imgEl.style.display = 'none';
        noImgText.style.display = 'block';
    }

    // Before / After Code view
    if (data.findings && data.findings.length > 0) {
        const beforeStr = data.findings.map(f => `${f.title}: ${f.value}`).join('\n');
        const afterStr = data.findings.map(f => `${f.title}: ████████████`).join('\n');
        document.getElementById('codeBefore').innerText = beforeStr;
        document.getElementById('codeAfter').innerText = afterStr;
    } else {
        document.getElementById('codeBefore').innerText = data.full_text || "No sensitive content detected.";
        document.getElementById('codeAfter').innerText = data.full_text || "No sensitive content detected.";
    }

    // Automatically check if protected file was generated
    const redactRes = data.redaction_result || {};
    const dlBtn = document.getElementById('btnDownload');
    if (redactRes.is_valid && redactRes.protected_filename) {
        dlBtn.href = `/api/download/${redactRes.protected_filename}`;
        dlBtn.innerText = `⬇️ DOWNLOAD ${redactRes.protected_filename}`;
        dlBtn.style.display = 'inline-flex';
    } else {
        dlBtn.style.display = 'none';
    }
}

function renderFindingsList(findings) {
    const container = document.getElementById('findingsContainer');
    container.innerHTML = '';

    if (!findings || findings.length === 0) {
        container.innerHTML = '<div class="glass-card" style="color: var(--color-safe);">🛡️ Perfect Security Score! No sensitive items detected.</div>';
        return;
    }

    findings.forEach(item => {
        const div = document.createElement('div');
        div.className = `finding-item ${item.severity.toLowerCase()}`;
        div.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <strong style="font-size: 15px; color: var(--text-main);">${item.title}</strong>
                <span class="badge badge-${item.severity.toLowerCase()}">${item.severity} • Conf: ${item.confidence} • Page ${item.page}</span>
            </div>
            <div style="font-family: monospace; color: var(--accent-cyan); font-size: 14px; margin-bottom: 6px;">
                Match: ${item.masked_value}
            </div>
            <div style="font-size: 13px; color: var(--text-muted);">
                <strong>Why Sensitive:</strong> ${item.explanation}
            </div>
            <div style="font-size: 13px; color: var(--color-safe); margin-top: 2px;">
                <strong>Action:</strong> ${item.recommendation}
            </div>
        `;
        container.appendChild(div);
    });
}

function filterFindings(sev) {
    if (!currentScanData) return;
    if (sev === 'ALL') {
        renderFindingsList(currentScanData.findings);
    } else {
        const filtered = currentScanData.findings.filter(f => f.severity === sev);
        renderFindingsList(filtered);
    }
}

// Execute Redaction
async function executeRedaction() {
    if (!currentScanData) return;

    try {
        const res = await fetch('/api/redact', { method: 'POST' });
        if (!res.ok) {
            const errData = await res.json().catch(() => ({ detail: res.statusText }));
            throw new Error(errData.detail || errData.error || "Redaction failed");
        }
        const data = await res.json();
        
        if (data.status === 'success') {
            const dlBtn = document.getElementById('btnDownload');
            dlBtn.href = data.download_url;
            dlBtn.innerText = `⬇️ DOWNLOAD ${data.protected_filename}`;
            dlBtn.style.display = 'inline-flex';
            alert(`✅ Safe Protected Copy Created: ${data.protected_filename}`);
            loadAppInfo();
        }
    } catch (e) {
        alert('Redaction Error: ' + e.message);
    }
}

// Load Scan History
async function loadHistory() {
    try {
        const res = await fetch('/api/history');
        const data = await res.json();
        
        const tbody = document.getElementById('historyTableBody');
        tbody.innerHTML = '';

        if (!data.history || data.history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">No scan history recorded.</td></tr>';
            return;
        }

        data.history.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>#${row.id}</td>
                <td>${row.timestamp}</td>
                <td><strong>${row.filename}</strong></td>
                <td>${row.file_type}</td>
                <td><span class="badge badge-${row.risk_level.toLowerCase()}">${row.risk_level}</span></td>
                <td>${row.security_score}/100</td>
                <td>${row.findings_count} items</td>
                <td>${row.processing_time}s</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error('Failed to load history:', e);
    }
}

async function clearHistory() {
    if (confirm("Are you sure you want to clear all scan history?")) {
        await fetch('/api/history/delete', { method: 'POST' });
        loadHistory();
        loadAppInfo();
    }
}
