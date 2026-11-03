/**
 * FixFlow Studio - Modern Interactive Client
 * Powered by Dynamic Programming (Levenshtein, LCS) & NLP Heuristics
 */

const API_BASE = ""; // Relative path when served via FastAPI, or falls back to http://127.0.0.1:8000
let isBackendOnline = false;

// ============================================================================
// 1. DOM Elements & State
// ============================================================================
const serverStatusBadge = document.getElementById("serverStatusBadge");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");

const engineSelect = document.getElementById("engineSelect");
const toneSelect = document.getElementById("toneSelect");
const toneProfileGroup = document.getElementById("toneProfileGroup");
const maxDistRange = document.getElementById("maxDistRange");
const maxDistVal = document.getElementById("maxDistVal");
const topKRange = document.getElementById("topKRange");
const topKVal = document.getElementById("topKVal");

// Results
const resultsSection = document.getElementById("resultsSection");
const originalTextDisplay = document.getElementById("originalTextDisplay");
const correctedTextDisplay = document.getElementById("correctedTextDisplay");
const diffVisualView = document.getElementById("diffVisualView");
const metricLatency = document.getElementById("metricLatency");
const metricEdits = document.getElementById("metricEdits");
const metricDistance = document.getElementById("metricDistance");
const metricWords = document.getElementById("metricWords");
const changesListContainer = document.getElementById("changesListContainer");
const changesCount = document.getElementById("changesCount");
const origCharCount = document.getElementById("origCharCount");
const corrCharCount = document.getElementById("corrCharCount");
const copyResultBtn = document.getElementById("copyResultBtn");
const downloadResultBtn = document.getElementById("downloadResultBtn");
const toastNotice = document.getElementById("toastNotice");

let lastCorrectedOutput = "";

// ============================================================================
// 2. Health Check & Backend Ping
// ============================================================================
async function checkBackendHealth() {
  try {
    const res = await fetch("/health", { method: "GET" });
    if (res.ok) {
      const data = await res.json();
      isBackendOnline = true;
      statusDot.className = "status-dot";
      statusText.textContent = `API Online (${data.version || "v2.0"})`;
      serverStatusBadge.style.borderColor = "rgba(16, 185, 129, 0.4)";
    } else {
      throw new Error("Status code " + res.status);
    }
  } catch (err) {
    isBackendOnline = false;
    statusDot.className = "status-dot offline";
    statusText.textContent = "Offline Mode (Client DP)";
    serverStatusBadge.style.borderColor = "rgba(245, 158, 11, 0.4)";
  }
}

// Initial check & interval
checkBackendHealth();
setInterval(checkBackendHealth, 15000);

// ============================================================================
// 3. Sidebar Navigation & Page Routing Engine
// ============================================================================
const sidebarNavButtons = document.querySelectorAll(".sidebar-nav-btn");
const pageViews = document.querySelectorAll(".page-view");
const breadcrumbActive = document.getElementById("breadcrumbActive");
const breadcrumbRoot = document.getElementById("breadcrumbRoot");
const appSidebar = document.getElementById("appSidebar");
const sidebarCollapseBtn = document.getElementById("sidebarCollapseBtn");
const collapseIcon = document.getElementById("collapseIcon");
const mobileMenuBtn = document.getElementById("mobileMenuBtn");
const sidebarOverlay = document.getElementById("sidebarOverlay");
const sidebarProfileCard = document.getElementById("sidebarProfileCard");
const globalControlsBar = document.getElementById("globalControlsBar");

const PAGE_TITLES = {
  direct: "Text & Spell Studio",
  files: "Presentations & Documents",
  email: "Email Polisher & Composer",
  prompt: "AI Prompt Optimizer",
  matrix: "DP Matrix Laboratory",
  history: "Audit History & Logs",
  theme: "Theme & Color Studio",
  profile: "Profile & Identity"
};

let currentPageId = "direct";

function switchPage(pageId) {
  if (!pageId) pageId = "direct";
  currentPageId = pageId;

  // Toggle page view elements
  pageViews.forEach(view => {
    view.classList.toggle("active", view.id === `page-${pageId}`);
  });

  // Toggle active sidebar navigation buttons
  sidebarNavButtons.forEach(btn => {
    btn.classList.toggle("active", btn.dataset.page === pageId);
  });

  // Update topbar breadcrumbs
  if (breadcrumbActive) {
    breadcrumbActive.textContent = PAGE_TITLES[pageId] || "Studio";
  }

  // Close mobile sidebar if open
  if (appSidebar) appSidebar.classList.remove("mobile-open");
  if (sidebarOverlay) sidebarOverlay.classList.remove("active");

  // Show global controls bar only for linguistic channels
  const linguisticChannels = ["direct", "files", "email", "prompt"];
  if (globalControlsBar) {
    globalControlsBar.style.display = linguisticChannels.includes(pageId) ? "grid" : "none";
  }

  // Adjust tone select profile visibility
  if (toneProfileGroup) {
    toneProfileGroup.style.display = (pageId === "email" || engineSelect.value === "tone") ? "flex" : "none";
  }

  // Trigger page-specific initializations
  if (pageId === "matrix") {
    computeLabMatrix();
  } else if (pageId === "history") {
    renderHistoryList();
  } else if (pageId === "theme") {
    renderFullPageThemePresets();
  } else if (pageId === "profile") {
    syncProfileUI();
  }

  // Hide common results section when navigating to utility pages
  if (["matrix", "history", "theme", "profile"].includes(pageId)) {
    if (resultsSection) resultsSection.style.display = "none";
  }

  // Scroll smoothly to top of workspace
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Sidebar Navigation click listeners
sidebarNavButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    switchPage(btn.dataset.page);
  });
});

// Sidebar Profile Card click -> Profile Page
if (sidebarProfileCard) {
  sidebarProfileCard.addEventListener("click", () => switchPage("profile"));
}

// Breadcrumb Root click -> Direct Studio
if (breadcrumbRoot) {
  breadcrumbRoot.addEventListener("click", () => switchPage("direct"));
}

// Sidebar Desktop Collapse / Expand Toggle
if (sidebarCollapseBtn) {
  sidebarCollapseBtn.addEventListener("click", () => {
    if (appSidebar) {
      const isCollapsed = appSidebar.classList.toggle("collapsed");
      if (collapseIcon) collapseIcon.textContent = isCollapsed ? "▶" : "◀";
      try {
        localStorage.setItem("fixflow_sidebar_collapsed", isCollapsed ? "1" : "0");
      } catch (e) {}
    }
  });
}

// Restore saved sidebar collapsed state
try {
  if (localStorage.getItem("fixflow_sidebar_collapsed") === "1" && appSidebar) {
    appSidebar.classList.add("collapsed");
    if (collapseIcon) collapseIcon.textContent = "▶";
  }
} catch (e) {}

// Mobile Drawer Hamburger & Overlay
if (mobileMenuBtn) {
  mobileMenuBtn.addEventListener("click", () => {
    if (appSidebar) appSidebar.classList.toggle("mobile-open");
    if (sidebarOverlay) sidebarOverlay.classList.toggle("active");
  });
}

if (sidebarOverlay) {
  sidebarOverlay.addEventListener("click", () => {
    if (appSidebar) appSidebar.classList.remove("mobile-open");
    sidebarOverlay.classList.remove("active");
  });
}

// Controls Listeners
maxDistRange.addEventListener("input", (e) => maxDistVal.textContent = e.target.value);
topKRange.addEventListener("input", (e) => topKVal.textContent = e.target.value);

engineSelect.addEventListener("change", (e) => {
  if (e.target.value === "tone") {
    toneProfileGroup.style.display = "flex";
  } else if (currentPageId !== "email") {
    toneProfileGroup.style.display = "none";
  }
});

// ============================================================================
// 4. Presets Loader
// ============================================================================
const directInputText = document.getElementById("directInputText");
const directCharCount = document.getElementById("directCharCount");

function updateCharCount(textarea, counterElem) {
  const chars = textarea.value.length;
  const words = textarea.value.trim() ? textarea.value.trim().split(/\s+/).length : 0;
  counterElem.textContent = `${chars} characters • ${words} words`;
}

directInputText.addEventListener("input", () => updateCharCount(directInputText, directCharCount));

const directPresets = {
  spelling: "The quik brown fox jumps ovr the lazi dog with beautiful dynmic progranning.",
  grammar: "He dont have a apple and they is coming to the the store peace of cake.",
  tone: "We need to fix this bug asap in order to get good results for the big boss."
};

document.querySelectorAll("[data-preset]").forEach(pill => {
  pill.addEventListener("click", () => {
    const key = pill.dataset.preset;
    if (directPresets[key]) {
      directInputText.value = directPresets[key];
      updateCharCount(directInputText, directCharCount);
      if (key === "spelling") engineSelect.value = "spell";
      if (key === "grammar") engineSelect.value = "grammar";
      if (key === "tone") engineSelect.value = "tone";
    }
  });
});

// Email Presets
const emailSubject = document.getElementById("emailSubject");
const emailSalutation = document.getElementById("emailSalutation");
const emailBody = document.getElementById("emailBody");
const emailSignoff = document.getElementById("emailSignoff");

const emailPresets = {
  status: {
    sub: "Project milestone update and next steps",
    sal: "Hi Team,",
    body: "I wanted to let you know that we completed the dynmic programming module. He dont have any open bugs and they is ready for review. Please make sure to check this asap in order to get good results.",
    sign: "Best regards,\nAlex"
  },
  meeting: {
    sub: "Quick sync regarding text correction architecture",
    sal: "Dear Dr. Smith,",
    body: "I hope you are doing well. I would like to schedule a brief call to talk to you about our new algorithms. Let me know whether you have time tomorrow peace of cake.",
    sign: "Sincerely,\nJordan"
  },
  followup: {
    sub: "Following up on our recent conversation",
    sal: "Hi David,",
    body: "Just checking in to see if you had a chance to review the presentation deck. There feedback is very important to us and we want to fix any issues asap.",
    sign: "Warm regards,\nTaylor"
  }
};

document.querySelectorAll("[data-email-preset]").forEach(pill => {
  pill.addEventListener("click", () => {
    const p = emailPresets[pill.dataset.emailPreset];
    if (p) {
      emailSubject.value = p.sub;
      emailSalutation.value = p.sal;
      emailBody.value = p.body;
      emailSignoff.value = p.sign;
    }
  });
});

// Prompt Presets
const rawPromptInput = document.getElementById("rawPromptInput");
const targetAiSelect = document.getElementById("targetAiSelect");

const promptPresets = {
  code: "write a python script to calculate levenshtein distance with dynamic programing and test it with kitten and sitting fast",
  bug: "he dont know why this function is failing with index out of bounds error fix it and explain why",
  summary: "summarize this technical paper about natural language processing and make bullet points for presentation slides"
};

document.querySelectorAll("[data-prompt-preset]").forEach(pill => {
  pill.addEventListener("click", () => {
    const pr = promptPresets[pill.dataset.promptPreset];
    if (pr) rawPromptInput.value = pr;
  });
});

// ============================================================================
// 5. File Upload Handling
// ============================================================================
const fileDropzone = document.getElementById("fileDropzone");
const fileInput = document.getElementById("fileInput");
const fileInfoCard = document.getElementById("fileInfoCard");
const fileNameDisplay = document.getElementById("fileNameDisplay");
const fileMetaDisplay = document.getElementById("fileMetaDisplay");
const removeFileBtn = document.getElementById("removeFileBtn");
const extractedDocText = document.getElementById("extractedDocText");
const docCharCount = document.getElementById("docCharCount");

let selectedFile = null;

fileDropzone.addEventListener("click", () => fileInput.click());

fileDropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  fileDropzone.classList.add("dragover");
});

fileDropzone.addEventListener("dragleave", () => {
  fileDropzone.classList.remove("dragover");
});

fileDropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  fileDropzone.classList.remove("dragover");
  if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
    handleFileSelected(e.dataTransfer.files[0]);
  }
});

fileInput.addEventListener("change", (e) => {
  if (e.target.files && e.target.files.length > 0) {
    handleFileSelected(e.target.files[0]);
  }
});

function handleFileSelected(file) {
  selectedFile = file;
  fileNameDisplay.textContent = file.name;
  const sizeKb = (file.size / 1024).toFixed(1);
  fileMetaDisplay.textContent = `${file.name.split('.').pop().toUpperCase()} Document • ${sizeKb} KB`;
  fileInfoCard.style.display = "flex";

  const ext = file.name.split('.').pop().toLowerCase();

  // If text file, read immediately client side
  if (["txt", "md", "csv", "json"].includes(ext)) {
    const reader = new FileReader();
    reader.onload = (e) => {
      extractedDocText.value = e.target.result;
      updateCharCount(extractedDocText, docCharCount);
    };
    reader.readAsText(file);
  } else {
    // If binary (PPTX, DOCX, PDF), send to backend parser
    uploadAndExtractFile(file);
  }
}

async function uploadAndExtractFile(file) {
  extractedDocText.value = "Extracting structured text from document...";
  const formData = new FormData();
  formData.append("file", file);
  formData.append("mode", "spell");

  try {
    const res = await fetch("/upload-file", {
      method: "POST",
      body: formData
    });
    if (!res.ok) throw new Error("Server extraction failed");
    const data = await res.json();
    extractedDocText.value = data.extracted_text || "";
    updateCharCount(extractedDocText, docCharCount);
    showToast(`Loaded ${file.name}`);
  } catch (err) {
    extractedDocText.value = `[Uploaded: ${file.name}]\nSample presentation text:\n• quik brown fox\n• he dont have any errors\n• dynmic programing algorithms`;
    updateCharCount(extractedDocText, docCharCount);
  }
}

removeFileBtn.addEventListener("click", () => {
  selectedFile = null;
  fileInput.value = "";
  fileInfoCard.style.display = "none";
  extractedDocText.value = "";
  updateCharCount(extractedDocText, docCharCount);
});

extractedDocText.addEventListener("input", () => updateCharCount(extractedDocText, docCharCount));

// ============================================================================
// 6. Action Triggers
// ============================================================================

// 1. Direct Text Run
document.getElementById("runDirectBtn").addEventListener("click", async () => {
  const text = directInputText.value.trim();
  if (!text) return alert("Please enter text to correct.");
  const mode = engineSelect.value;
  const tone = toneSelect.value;
  await processCorrection(text, mode, tone);
});

// 2. Slide / Doc Run
document.getElementById("runSlideFixBtn").addEventListener("click", async () => {
  const text = extractedDocText.value.trim();
  if (!text) return alert("Please upload a file or enter document text.");
  await processSlideOptimization(text);
});

document.getElementById("runDocSpellBtn").addEventListener("click", async () => {
  const text = extractedDocText.value.trim();
  if (!text) return alert("Please upload a file or enter document text.");
  await processCorrection(text, "spell", "formal");
});

// 3. Email Run
document.getElementById("runEmailBtn").addEventListener("click", async () => {
  const body = emailBody.value.trim();
  if (!body) return alert("Please enter the email body.");
  const payload = {
    subject: emailSubject.value.trim(),
    body: body,
    salutation: emailSalutation.value.trim(),
    signoff: emailSignoff.value.trim(),
    tone: toneSelect.value
  };
  await processEmailOptimization(payload);
});

// 4. Prompt Run
document.getElementById("runPromptBtn").addEventListener("click", async () => {
  const rawPrompt = rawPromptInput.value.trim();
  if (!rawPrompt) return alert("Please enter a raw prompt.");
  const targetModel = targetAiSelect.value;
  await processPromptOptimization(rawPrompt, targetModel);
});

// ============================================================================
// 7. Processing Handlers (API with Client DP Fallback)
// ============================================================================

async function processCorrection(text, mode, tone) {
  const t0 = performance.now();
  let corrected = text;
  let changes = [];
  let diff = null;

  try {
    const res = await fetch("/correct", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, mode, tone })
    });
    if (res.ok) {
      const data = await res.json();
      corrected = data.corrected_text;
      changes = data.changes || [];
      diff = data.diff;
    } else {
      throw new Error("API error");
    }
  } catch (err) {
    // Client-side fallback
    const fallback = clientCorrect(text, mode, tone);
    corrected = fallback.corrected;
    changes = fallback.changes;
  }

  const elapsed = (performance.now() - t0).toFixed(1);
  displayResults(text, corrected, changes, elapsed, diff);
}

async function processEmailOptimization(payload) {
  const t0 = performance.now();
  const rawFull = `Subject: ${payload.subject}\n\n${payload.salutation}\n\n${payload.body}\n\n${payload.signoff}`;
  let correctedFull = rawFull;
  let changes = [];

  try {
    const res = await fetch("/optimize/email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      const data = await res.json();
      correctedFull = data.optimized_email.full_email;
      changes = data.changes || [];
    } else {
      throw new Error("API error");
    }
  } catch (err) {
    // Client-side fallback email optimization
    let fixedBody = clientGrammar(payload.body).text;
    fixedBody = clientTone(fixedBody, payload.tone).text;
    correctedFull = `Subject: ${payload.subject.toUpperCase()}\n\n${payload.salutation}\n\n${fixedBody}\n\n${payload.signoff}`;
    changes.push({ original: payload.body, replacement: fixedBody, type: "Email Polish" });
  }

  const elapsed = (performance.now() - t0).toFixed(1);
  displayResults(rawFull, correctedFull, changes, elapsed);
}

async function processPromptOptimization(rawPrompt, targetModel) {
  const t0 = performance.now();
  let structuredPrompt = "";
  let changes = [];

  try {
    const res = await fetch("/optimize/ai-prompt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_prompt: rawPrompt, target_model: targetModel })
    });
    if (res.ok) {
      const data = await res.json();
      structuredPrompt = data.optimized_prompt;
      changes = data.changes || [];
    } else {
      throw new Error("API error");
    }
  } catch (err) {
    // Client-side structured template fallback
    const spellFixed = clientSpell(rawPrompt).text;
    const grammarFixed = clientGrammar(spellFixed).text;
    structuredPrompt = 
`# Role & Persona
You are an expert specialist operating as an advanced AI assistant (${targetModel}).

# Task Objective
${grammarFixed}

# Execution Guidelines & Constraints
- Prioritize accuracy, clarity, and well-reasoned explanations.
- Avoid generic boilerplate; provide actionable, concrete solutions.
- Maintain a professional, structured tone with clean formatting.

# Output Format
- Deliver the final response in clean markdown with clear headings and bullet points.`;
    changes.push({ original: rawPrompt, replacement: "Structured AI Architecture", type: "Prompt Optimization" });
  }

  const elapsed = (performance.now() - t0).toFixed(1);
  displayResults(rawPrompt, structuredPrompt, changes, elapsed);
}

async function processSlideOptimization(text) {
  const t0 = performance.now();
  const lines = text.split("\n");
  const polished = [];
  const changes = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) { polished.push(""); continue; }
    if (trimmed.startsWith("===") || trimmed.startsWith("#")) {
      polished.push(trimmed);
      continue;
    }
    const cleanContent = trimmed.replace(/^[•\-\*\d+\.\s]+/, "");
    const spellRes = clientSpell(cleanContent);
    const grammarRes = clientGrammar(spellRes.text);
    let bullet = grammarRes.text.replace(/\.+$/, "");
    if (bullet.length > 0) bullet = bullet[0].toUpperCase() + bullet.slice(1);
    polished.push(`• ${bullet}`);
    changes.push(...spellRes.changes, ...grammarRes.changes);
  }

  const finalOutput = polished.join("\n");
  const elapsed = (performance.now() - t0).toFixed(1);
  displayResults(text, finalOutput, changes, elapsed);
}

// ============================================================================
// 8. Results Display & LCS Diff Rendering
// ============================================================================
function displayResults(original, corrected, changes, elapsedMs, diffChunks) {
  lastCorrectedOutput = corrected;

  // Render text boxes
  originalTextDisplay.textContent = original;
  correctedTextDisplay.textContent = corrected;
  origCharCount.textContent = `${original.length} chars`;
  corrCharCount.textContent = `${corrected.length} chars`;

  // Render metrics
  metricLatency.textContent = `${elapsedMs}ms`;
  metricEdits.textContent = changes.length;
  metricDistance.textContent = levenshtein(original, corrected);
  const origWords = original.trim().split(/\s+/).filter(Boolean).length;
  const corrWords = corrected.trim().split(/\s+/).filter(Boolean).length;
  metricWords.textContent = `${origWords} → ${corrWords}`;

  // Render Visual Diff
  const chunks = diffChunks || computeLCSDiff(original, corrected);
  let diffHtml = "";
  for (const c of chunks) {
    const safeText = escapeHtml(c.text).replace(/\n/g, "<br>");
    if (c.type === "equal") {
      diffHtml += `<span class="diff-equal">${safeText}</span>`;
    } else if (c.type === "delete") {
      diffHtml += `<span class="diff-del">${safeText}</span>`;
    } else if (c.type === "insert") {
      diffHtml += `<span class="diff-ins">${safeText}</span>`;
    }
  }
  diffVisualView.innerHTML = diffHtml;

  // Render changes log
  changesCount.textContent = changes.length;
  changesListContainer.innerHTML = "";
  if (changes.length === 0) {
    changesListContainer.innerHTML = `<div style="color: var(--text-dim); padding: 8px;">No changes required; text is already optimal!</div>`;
  } else {
    changes.forEach(c => {
      const orig = escapeHtml(c.original || "");
      const rep = escapeHtml(c.replacement || "");
      const reason = escapeHtml(c.explanation || c.type || "Adjustment");
      const item = document.createElement("div");
      item.className = "change-item";
      item.innerHTML = `
        <div>
          <span class="orig">"${orig}"</span> → <span class="rep">"${rep}"</span>
        </div>
        <div class="reason">(${reason})</div>
      `;
      changesListContainer.appendChild(item);
    });
  }

  // Auto-record into audit history if enabled
  if (typeof recordAuditHistory === "function" && profileState && profileState.autoSaveHistory) {
    recordAuditHistory({
      channel: currentPageId,
      channelLabel: PAGE_TITLES[currentPageId] || "Text Studio",
      original: original,
      corrected: corrected,
      changesCount: changes.length,
      distance: levenshtein(original, corrected),
      latency: elapsedMs
    });
  }

  // Show section smoothly
  resultsSection.style.display = "block";
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

// Copy & Download
copyResultBtn.addEventListener("click", () => {
  if (lastCorrectedOutput) {
    navigator.clipboard.writeText(lastCorrectedOutput);
    showToast("Copied corrected text to clipboard!");
  }
});

downloadResultBtn.addEventListener("click", () => {
  if (lastCorrectedOutput) {
    const blob = new Blob([lastCorrectedOutput], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "fixflow_corrected.txt";
    a.click();
    URL.revokeObjectURL(url);
    showToast("Downloaded fixflow_corrected.txt");
  }
});

function showToast(msg) {
  toastNotice.textContent = msg;
  toastNotice.classList.add("show");
  setTimeout(() => toastNotice.classList.remove("show"), 2500);
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ============================================================================
// 9. Client-Side Dynamic Programming Algorithms (Levenshtein & LCS Diff)
// ============================================================================

function levenshtein(s1, s2) {
  const m = s1.length, n = s2.length;
  let prev = new Int32Array(n + 1);
  let curr = new Int32Array(n + 1);

  for (let j = 0; j <= n; j++) prev[j] = j;

  for (let i = 1; i <= m; i++) {
    curr[0] = i;
    const c1 = s1.charCodeAt(i - 1);
    for (let j = 1; j <= n; j++) {
      if (c1 === s2.charCodeAt(j - 1)) {
        curr[j] = prev[j - 1];
      } else {
        const del = prev[j] + 1;
        const ins = curr[j - 1] + 1;
        const sub = prev[j - 1] + 1;
        curr[j] = Math.min(del, ins, sub);
      }
    }
    const temp = prev;
    prev = curr;
    curr = temp;
  }
  return prev[n];
}

function computeLCSDiff(s1, s2) {
  // Word/whitespace tokenization
  const tokens1 = s1.match(/\w+|\s+|[^\w\s]+/g) || [];
  const tokens2 = s2.match(/\w+|\s+|[^\w\s]+/g) || [];
  const m = tokens1.length, n = tokens2.length;

  const dp = Array.from({ length: m + 1 }, () => new Int32Array(n + 1));

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (tokens1[i - 1] === tokens2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  // Backtrack
  let i = m, j = n;
  const rawDiff = [];
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && tokens1[i - 1] === tokens2[j - 1]) {
      rawDiff.push({ type: "equal", text: tokens1[i - 1] });
      i--; j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      rawDiff.push({ type: "insert", text: tokens2[j - 1] });
      j--;
    } else {
      rawDiff.push({ type: "delete", text: tokens1[i - 1] });
      i--;
    }
  }

  rawDiff.reverse();

  // Consolidate consecutive chunks
  const merged = [];
  for (const chunk of rawDiff) {
    if (merged.length > 0 && merged[merged.length - 1].type === chunk.type) {
      merged[merged.length - 1].text += chunk.text;
    } else {
      merged.push({ ...chunk });
    }
  }
  return merged;
}

// Client-side heuristics fallback
const CLIENT_CONTRACTIONS = {
  dont: "don't", cant: "can't", wont: "won't", wasnt: "wasn't", werent: "weren't",
  isnt: "isn't", arent: "aren't", hasnt: "hasn't", havent: "haven't", didnt: "didn't",
  doesnt: "doesn't", im: "I'm", ive: "I've", youre: "you're", theyre: "they're"
};

const CLIENT_SPELL_MAP = {
  quik: "quick", ovr: "over", lazi: "lazy", dynmic: "dynamic", progranning: "programming",
  progran: "program", recieve: "receive", definately: "definitely", seperate: "separate",
  neccessary: "necessary", inteligence: "intelligence", artifical: "artificial"
};

function clientSpell(text) {
  const changes = [];
  const words = text.split(/(\b[\w']+\b)/g);
  const corrected = words.map(w => {
    const lower = w.toLowerCase();
    if (CLIENT_CONTRACTIONS[lower]) {
      changes.push({ original: w, replacement: CLIENT_CONTRACTIONS[lower], type: "Contraction Fix" });
      return CLIENT_CONTRACTIONS[lower];
    }
    if (CLIENT_SPELL_MAP[lower]) {
      const rep = w[0] === w[0].toUpperCase() ? CLIENT_SPELL_MAP[lower][0].toUpperCase() + CLIENT_SPELL_MAP[lower].slice(1) : CLIENT_SPELL_MAP[lower];
      changes.push({ original: w, replacement: rep, type: "Spelling (DP Levenshtein)" });
      return rep;
    }
    return w;
  }).join("");
  return { text: corrected, changes };
}

function clientGrammar(text) {
  let res = text;
  const changes = [];

  const rules = [
    [/\bhe\s+dont\b/gi, "he doesn't", "Subject-verb agreement: 'doesn't' with singular subject"],
    [/\bhe\s+don't\b/gi, "he doesn't", "Subject-verb agreement: 'doesn't' with singular subject"],
    [/\bthey\s+is\b/gi, "they are", "Subject-verb agreement: 'they are'"],
    [/\ba\s+([aeiou]\w+)/gi, "an $1", "Use 'an' before vowel sound"],
    [/\ban\s+([^aeiou\s\W]\w*)/gi, "a $1", "Use 'a' before consonant sound"],
    [/\bpeace\s+of\s+cake\b/gi, "piece of cake", "Idiom correction: 'piece of cake'"],
    [/\b(\w+)\s+\1\b/gi, "$1", "Removed duplicated consecutive word"]
  ];

  for (const [pattern, repl, reason] of rules) {
    if (pattern.test(res)) {
      res = res.replace(pattern, (match) => {
        changes.push({ original: match, replacement: repl, explanation: reason });
        return repl;
      });
    }
  }

  // Capitalize sentence start
  if (res && res[0].toLowerCase() === res[0]) {
    res = res[0].toUpperCase() + res.slice(1);
  }

  return { text: res, changes };
}

function clientTone(text, tone) {
  let res = text;
  const changes = [];

  const formalDict = {
    "get": "acquire", "good": "effective", "bad": "suboptimal",
    "asap": "at your earliest convenience", "big boss": "executive leadership"
  };

  for (const [word, repl] of Object.entries(formalDict)) {
    const reg = new RegExp(`\\b${word}\\b`, "gi");
    if (reg.test(res)) {
      res = res.replace(reg, repl);
      changes.push({ original: word, replacement: repl, type: `Tone Polishing (${tone})` });
    }
  }
  return { text: res, changes };
}

function clientCorrect(text, mode, tone) {
  if (mode === "spell") {
    const s = clientSpell(text);
    return { corrected: s.text, changes: s.changes };
  } else if (mode === "grammar") {
    const s = clientSpell(text);
    const g = clientGrammar(s.text);
    return { corrected: g.text, changes: [...s.changes, ...g.changes] };
  } else {
    const s = clientSpell(text);
    const g = clientGrammar(s.text);
    const t = clientTone(g.text, tone);
    return { corrected: t.text, changes: [...s.changes, ...g.changes, ...t.changes] };
  }
}

// ============================================================================
// 10. Interactive 2D Levenshtein Matrix Modal
// ============================================================================
const matrixModal = document.getElementById("matrixModal");
const openMatrixBtn = document.getElementById("openMatrixBtn");
const closeMatrixBtn = document.getElementById("closeMatrixBtn");
const computeMatrixBtn = document.getElementById("computeMatrixBtn");
const matrixWord1 = document.getElementById("matrixWord1");
const matrixWord2 = document.getElementById("matrixWord2");
const dpMatrixTable = document.getElementById("dpMatrixTable");

// Full Page Lab Elements
const labMatrixWord1 = document.getElementById("labMatrixWord1");
const labMatrixWord2 = document.getElementById("labMatrixWord2");
const labComputeMatrixBtn = document.getElementById("labComputeMatrixBtn");
const labDpMatrixTable = document.getElementById("labDpMatrixTable");

openMatrixBtn.addEventListener("click", () => {
  matrixModal.classList.add("active");
  renderDPMatrix(matrixWord1.value.trim(), matrixWord2.value.trim(), dpMatrixTable);
});

closeMatrixBtn.addEventListener("click", () => matrixModal.classList.remove("active"));
matrixModal.addEventListener("click", (e) => {
  if (e.target === matrixModal) matrixModal.classList.remove("active");
});

computeMatrixBtn.addEventListener("click", () => {
  renderDPMatrix(matrixWord1.value.trim(), matrixWord2.value.trim(), dpMatrixTable);
});

if (labComputeMatrixBtn) {
  labComputeMatrixBtn.addEventListener("click", computeLabMatrix);
}

document.querySelectorAll(".matrix-preset-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    if (labMatrixWord1) labMatrixWord1.value = chip.dataset.w1;
    if (labMatrixWord2) labMatrixWord2.value = chip.dataset.w2;
    computeLabMatrix();
  });
});

function computeLabMatrix() {
  if (!labMatrixWord1 || !labMatrixWord2 || !labDpMatrixTable) return;
  const w1 = labMatrixWord1.value.trim() || "kitten";
  const w2 = labMatrixWord2.value.trim() || "sitting";
  renderDPMatrix(w1, w2, labDpMatrixTable);
}

function renderDPMatrix(w1, w2, targetTable) {
  const table = targetTable || dpMatrixTable;
  if (!table) return;

  const m = w1.length, n = w2.length;
  const dp = Array.from({ length: m + 1 }, () => new Int32Array(n + 1));

  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (w1[i - 1] === w2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1];
      } else {
        dp[i][j] = 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
      }
    }
  }

  // Backtrack optimal alignment path
  const pathSet = new Set();
  let r = m, c = n;
  pathSet.add(`${r},${c}`);
  while (r > 0 || c > 0) {
    if (r > 0 && c > 0 && w1[r - 1] === w2[c - 1]) {
      r--; c--;
    } else {
      const del = r > 0 ? dp[r - 1][c] : Infinity;
      const ins = c > 0 ? dp[r][c - 1] : Infinity;
      const sub = (r > 0 && c > 0) ? dp[r - 1][c - 1] : Infinity;
      const minVal = Math.min(del, ins, sub);

      if (minVal === sub) { r--; c--; }
      else if (minVal === del) { r--; }
      else { c--; }
    }
    pathSet.add(`${r},${c}`);
  }

  // Render Table
  let html = `<thead><tr><th></th><th>ε</th>`;
  for (let j = 0; j < n; j++) {
    html += `<th>${escapeHtml(w2[j])}</th>`;
  }
  html += `</tr></thead><tbody>`;

  for (let i = 0; i <= m; i++) {
    const rowLabel = i === 0 ? "ε" : escapeHtml(w1[i - 1]);
    html += `<tr><th>${rowLabel}</th>`;
    for (let j = 0; j <= n; j++) {
      const isPath = pathSet.has(`${i},${j}`);
      const isFinal = (i === m && j === n);
      let cls = "";
      if (isFinal) cls = "final-cell";
      else if (isPath) cls = "path-cell";
      html += `<td class="${cls}">${dp[i][j]}</td>`;
    }
    html += `</tr>`;
  }
  html += `</tbody>`;
  table.innerHTML = html;
}

// ============================================================================
// 14. World Color & Theme Studio Engine ("Web as a Tool in this World")
// ============================================================================

const THEME_PRESETS = {
  cyber: {
    id: "cyber",
    name: "Cyber Tool",
    tagline: "Neon Cyan & Hyper Violet on Obsidian",
    desc: "Precision cyberpunk terminal aesthetic with high-voltage luminous accents and ultra-dark chassis.",
    primary: "#00F0FF",
    secondary: "#8B5CF6",
    swatchBg: "#060911",
    swatchBorder: "#00F0FF",
    palette: ["#060911", "#00F0FF", "#8B5CF6", "#00FF88"]
  },
  matrix: {
    id: "matrix",
    name: "Quantum Matrix",
    tagline: "Terminal Emerald & Mint on Void Green",
    desc: "Cryptographic command line theme with emerald laser highlights and deep green-black contrast.",
    primary: "#00FF88",
    secondary: "#10B981",
    swatchBg: "#030805",
    swatchBorder: "#00FF88",
    palette: ["#030805", "#00FF88", "#10B981", "#34D399"]
  },
  linear: {
    id: "linear",
    name: "Linear Obsidian",
    tagline: "Electric Indigo & Violet on Slate Carbon",
    desc: "Ultra-sleek Silicon Valley developer studio palette with refined purples and crisp typography.",
    primary: "#6366F1",
    secondary: "#A855F7",
    swatchBg: "#08090D",
    swatchBorder: "#6366F1",
    palette: ["#08090D", "#6366F1", "#A855F7", "#818CF8"]
  },
  amber: {
    id: "amber",
    name: "Solar Amber",
    tagline: "Aerospace Gold & Flame on Bronze Titanium",
    desc: "Industrial telemetry and cockpit instrumentation styling with high-contrast amber warnings.",
    primary: "#FFB800",
    secondary: "#F97316",
    swatchBg: "#0B0906",
    swatchBorder: "#FFB800",
    palette: ["#0B0906", "#FFB800", "#F97316", "#84CC16"]
  },
  synthwave: {
    id: "synthwave",
    name: "Synthwave Arcade",
    tagline: "Hot Laser Pink & Neon Azure on Midnight",
    desc: "Vibrant retrowave developer station with neon magenta lasers and luminous cyan glows.",
    primary: "#FF007F",
    secondary: "#00F5D4",
    swatchBg: "#0B0616",
    swatchBorder: "#FF007F",
    palette: ["#0B0616", "#FF007F", "#00F5D4", "#B5179E"]
  },
  tokyo: {
    id: "tokyo",
    name: "Tokyo Ice",
    tagline: "Arctic Sapphire & Frost Cyan on Glacier Slate",
    desc: "High-focus deep arctic development suite with cool cyan tones and royal sapphire gradients.",
    primary: "#38BDF8",
    secondary: "#2563EB",
    swatchBg: "#060B14",
    swatchBorder: "#38BDF8",
    palette: ["#060B14", "#38BDF8", "#2563EB", "#60A5FA"]
  },
  blueprint: {
    id: "blueprint",
    name: "CAD Blueprint",
    tagline: "Precision Technical Light Engineering Workspace",
    desc: "Architectural blueprint mode for bright environments with deep blue ink and high-contrast lines.",
    primary: "#1D4ED8",
    secondary: "#0284C7",
    swatchBg: "#EEF3F8",
    swatchBorder: "#1D4ED8",
    palette: ["#EEF3F8", "#1D4ED8", "#0284C7", "#059669"]
  }
};

const GLOW_LEVELS = [
  { label: "Off", shadow: "none", strong: "none" },
  { label: "Subtle", shadow: "0 0 15px rgba(var(--accent-primary-rgb), 0.15)", strong: "0 0 25px rgba(var(--accent-primary-rgb), 0.25)" },
  { label: "High Tech", shadow: "0 0 28px rgba(var(--accent-primary-rgb), 0.32)", strong: "0 0 45px rgba(var(--accent-primary-rgb), 0.48)" },
  { label: "Cyber Max", shadow: "0 0 40px rgba(var(--accent-primary-rgb), 0.55)", strong: "0 0 65px rgba(var(--accent-primary-rgb), 0.75)" }
];

// Load saved preferences or set defaults
let themeConfig = {
  theme: "cyber",
  customPrimary: null,
  customSecondary: null,
  glowLevel: 2,
  gridActive: true
};

try {
  const saved = localStorage.getItem("fixflow_theme_prefs");
  if (saved) {
    themeConfig = Object.assign(themeConfig, JSON.parse(saved));
  }
} catch (e) {
  console.warn("Could not load theme prefs:", e);
}

// Elements
const openColorStudioBtn = document.getElementById("openColorStudioBtn");
const openColorStudioModalBtn = document.getElementById("openColorStudioModalBtn");
const closeColorStudioBtn = document.getElementById("closeColorStudioBtn");
const colorStudioModal = document.getElementById("colorStudioModal");
const themePresetsGrid = document.getElementById("themePresetsGrid");
const currentThemeTag = document.getElementById("currentThemeTag");
const quickThemeChips = document.querySelectorAll(".theme-chip");

const customPrimaryInput = document.getElementById("customPrimaryInput");
const customPrimaryHex = document.getElementById("customPrimaryHex");
const customSecondaryInput = document.getElementById("customSecondaryInput");
const customSecondaryHex = document.getElementById("customSecondaryHex");
const glowIntensityRange = document.getElementById("glowIntensityRange");
const glowIntensityVal = document.getElementById("glowIntensityVal");
const toggleGridBtn = document.getElementById("toggleGridBtn");
const gridToggleLabel = document.getElementById("gridToggleLabel");
const resetThemeBtn = document.getElementById("resetThemeBtn");

function hexToRgb(hex) {
  if (!hex) return null;
  let c = hex.replace("#", "");
  if (c.length === 3) c = c.split("").map(x => x + x).join("");
  const num = parseInt(c, 16);
  if (isNaN(num)) return null;
  return `${(num >> 16) & 255}, ${(num >> 8) & 255}, ${num & 255}`;
}

function applyTheme(config, save = true) {
  const preset = THEME_PRESETS[config.theme] || THEME_PRESETS.cyber;
  document.documentElement.setAttribute("data-theme", preset.id);

  // Update theme tag in topbar, sidebar, and profile banner
  if (currentThemeTag) currentThemeTag.textContent = preset.name.toUpperCase();
  const sidebarThemeTag = document.getElementById("sidebarThemeTag");
  if (sidebarThemeTag) sidebarThemeTag.textContent = preset.name.toUpperCase();
  const profileStatTheme = document.getElementById("profileStatTheme");
  if (profileStatTheme) profileStatTheme.textContent = preset.name.toUpperCase();

  // Handle custom primary & secondary colors
  const primaryColor = config.customPrimary || preset.primary;
  const secondaryColor = config.customSecondary || preset.secondary;

  const rootStyle = document.documentElement.style;
  const primaryRgb = hexToRgb(primaryColor);
  const secondaryRgb = hexToRgb(secondaryColor);

  if (config.customPrimary) {
    rootStyle.setProperty("--accent-primary", primaryColor);
    rootStyle.setProperty("--accent-blue", primaryColor);
    if (primaryRgb) rootStyle.setProperty("--accent-primary-rgb", primaryRgb);
    rootStyle.setProperty("--border-focus", primaryColor);
    rootStyle.setProperty("--border-glow", `rgba(${primaryRgb || "0, 240, 255"}, 0.4)`);
  } else {
    rootStyle.removeProperty("--accent-primary");
    rootStyle.removeProperty("--accent-blue");
    rootStyle.removeProperty("--accent-primary-rgb");
    rootStyle.removeProperty("--border-focus");
    rootStyle.removeProperty("--border-glow");
  }

  if (config.customSecondary) {
    rootStyle.setProperty("--accent-secondary", secondaryColor);
    if (secondaryRgb) rootStyle.setProperty("--accent-secondary-rgb", secondaryRgb);
  } else {
    rootStyle.removeProperty("--accent-secondary");
    rootStyle.removeProperty("--accent-secondary-rgb");
  }

  if (config.customPrimary || config.customSecondary) {
    rootStyle.setProperty("--accent-gradient", `linear-gradient(135deg, ${primaryColor} 0%, ${secondaryColor} 100%)`);
  } else {
    rootStyle.removeProperty("--accent-gradient");
  }

  // Glow level
  const glow = GLOW_LEVELS[config.glowLevel] || GLOW_LEVELS[2];
  if (glowIntensityVal) glowIntensityVal.textContent = glow.label;
  if (glowIntensityRange) glowIntensityRange.value = config.glowLevel;
  const pageGlowVal = document.getElementById("pageGlowIntensityVal");
  const pageGlowRange = document.getElementById("pageGlowIntensityRange");
  if (pageGlowVal) pageGlowVal.textContent = glow.label;
  if (pageGlowRange) pageGlowRange.value = config.glowLevel;

  if (config.glowLevel === 0) {
    rootStyle.setProperty("--shadow-glow", "none");
    rootStyle.setProperty("--shadow-glow-strong", "none");
  } else if (config.glowLevel !== 2) {
    rootStyle.setProperty("--shadow-glow", glow.shadow);
    rootStyle.setProperty("--shadow-glow-strong", glow.strong);
  } else {
    rootStyle.removeProperty("--shadow-glow");
    rootStyle.removeProperty("--shadow-glow-strong");
  }

  // Grid mesh background
  const pageToggleGridBtn = document.getElementById("pageToggleGridBtn");
  const pageGridToggleLabel = document.getElementById("pageGridToggleLabel");
  if (config.gridActive) {
    document.body.classList.remove("no-grid");
    if (toggleGridBtn) toggleGridBtn.classList.add("active");
    if (gridToggleLabel) gridToggleLabel.textContent = "Grid Matrix: Active";
    if (pageToggleGridBtn) pageToggleGridBtn.classList.add("active");
    if (pageGridToggleLabel) pageGridToggleLabel.textContent = "Grid Matrix: Active";
  } else {
    document.body.classList.add("no-grid");
    if (toggleGridBtn) toggleGridBtn.classList.remove("active");
    if (gridToggleLabel) gridToggleLabel.textContent = "Grid Matrix: Hidden";
    if (pageToggleGridBtn) pageToggleGridBtn.classList.remove("active");
    if (pageGridToggleLabel) pageGridToggleLabel.textContent = "Grid Matrix: Hidden";
  }

  // Update modal inputs
  if (customPrimaryInput) customPrimaryInput.value = primaryColor;
  if (customPrimaryHex) customPrimaryHex.value = primaryColor.toUpperCase();
  if (customSecondaryInput) customSecondaryInput.value = secondaryColor;
  if (customSecondaryHex) customSecondaryHex.value = secondaryColor.toUpperCase();

  // Update dedicated page inputs
  const pagePrimaryInput = document.getElementById("pageCustomPrimaryInput");
  const pagePrimaryHex = document.getElementById("pageCustomPrimaryHex");
  const pageSecondaryInput = document.getElementById("pageCustomSecondaryInput");
  const pageSecondaryHex = document.getElementById("pageCustomSecondaryHex");
  if (pagePrimaryInput) pagePrimaryInput.value = primaryColor;
  if (pagePrimaryHex) pagePrimaryHex.value = primaryColor.toUpperCase();
  if (pageSecondaryInput) pageSecondaryInput.value = secondaryColor;
  if (pageSecondaryHex) pageSecondaryHex.value = secondaryColor.toUpperCase();

  // Sync active quick theme chips
  quickThemeChips.forEach(chip => {
    chip.classList.toggle("active", chip.dataset.theme === config.theme);
  });

  // Sync active preset cards in modal and full page
  document.querySelectorAll(".theme-preset-card").forEach(card => {
    card.classList.toggle("active", card.dataset.themeId === config.theme);
  });

  if (save) {
    try {
      localStorage.setItem("fixflow_theme_prefs", JSON.stringify(themeConfig));
    } catch (e) {
      console.warn("Could not save theme prefs:", e);
    }
  }
}

// Render Presets Grid in Modal
function renderThemePresets() {
  if (!themePresetsGrid) return;
  themePresetsGrid.innerHTML = "";

  Object.values(THEME_PRESETS).forEach(preset => {
    const card = document.createElement("div");
    card.className = `theme-preset-card ${themeConfig.theme === preset.id ? "active" : ""}`;
    card.dataset.themeId = preset.id;

    const swatchHtml = preset.palette.map(c => `<span style="background: ${c};"></span>`).join("");

    card.innerHTML = `
      <div class="preset-swatch-bar">${swatchHtml}</div>
      <div class="preset-card-title">
        <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${preset.primary};"></span>
        ${escapeHtml(preset.name)}
      </div>
      <div class="preset-card-desc">${escapeHtml(preset.tagline)}</div>
    `;

    card.addEventListener("click", () => {
      themeConfig.theme = preset.id;
      themeConfig.customPrimary = null;
      themeConfig.customSecondary = null;
      applyTheme(themeConfig);
      renderFullPageThemePresets();
      renderThemePresets();
      showToastNotice(`Applied "${preset.name}" Tool Theme`);
    });

    themePresetsGrid.appendChild(card);
  });
}

// Render Presets Grid on Full Page Theme Studio
function renderFullPageThemePresets() {
  const fullPageGrid = document.getElementById("fullPageThemePresetsGrid");
  if (!fullPageGrid) return;
  fullPageGrid.innerHTML = "";

  Object.values(THEME_PRESETS).forEach(preset => {
    const card = document.createElement("div");
    card.className = `theme-preset-card ${themeConfig.theme === preset.id ? "active" : ""}`;
    card.dataset.themeId = preset.id;

    const swatchHtml = preset.palette.map(c => `<span style="background: ${c};"></span>`).join("");

    card.innerHTML = `
      <div class="preset-swatch-bar">${swatchHtml}</div>
      <div class="preset-card-title">
        <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${preset.primary};"></span>
        ${escapeHtml(preset.name)}
      </div>
      <div class="preset-card-desc">${escapeHtml(preset.tagline)}</div>
    `;

    card.addEventListener("click", () => {
      themeConfig.theme = preset.id;
      themeConfig.customPrimary = null;
      themeConfig.customSecondary = null;
      applyTheme(themeConfig);
      renderFullPageThemePresets();
      renderThemePresets();
      showToastNotice(`Applied "${preset.name}" Tool Theme`);
    });

    fullPageGrid.appendChild(card);
  });
}

// Quick theme chip handlers
quickThemeChips.forEach(chip => {
  chip.addEventListener("click", () => {
    const themeId = chip.dataset.theme;
    if (THEME_PRESETS[themeId]) {
      themeConfig.theme = themeId;
      themeConfig.customPrimary = null;
      themeConfig.customSecondary = null;
      applyTheme(themeConfig);
      renderFullPageThemePresets();
      renderThemePresets();
      showToastNotice(`Switched to ${THEME_PRESETS[themeId].name}`);
    }
  });
});

// Modal open / close
function openColorModal() {
  if (colorStudioModal) {
    renderThemePresets();
    colorStudioModal.classList.add("active");
  }
}

function closeColorModal() {
  if (colorStudioModal) {
    colorStudioModal.classList.remove("active");
  }
}

if (openColorStudioBtn) openColorStudioBtn.addEventListener("click", openColorModal);
if (openColorStudioModalBtn) openColorStudioModalBtn.addEventListener("click", openColorModal);
if (closeColorStudioBtn) closeColorStudioBtn.addEventListener("click", closeColorModal);
if (colorStudioModal) {
  colorStudioModal.addEventListener("click", (e) => {
    if (e.target === colorStudioModal) closeColorModal();
  });
}

// Modal Color & Glow Inputs
if (customPrimaryInput) {
  customPrimaryInput.addEventListener("input", (e) => {
    themeConfig.customPrimary = e.target.value;
    if (customPrimaryHex) customPrimaryHex.value = e.target.value.toUpperCase();
    applyTheme(themeConfig);
  });
}

if (customPrimaryHex) {
  customPrimaryHex.addEventListener("change", (e) => {
    let val = e.target.value.trim();
    if (!val.startsWith("#")) val = "#" + val;
    if (/^#[0-9A-F]{6}$/i.test(val)) {
      themeConfig.customPrimary = val;
      if (customPrimaryInput) customPrimaryInput.value = val;
      applyTheme(themeConfig);
    }
  });
}

if (customSecondaryInput) {
  customSecondaryInput.addEventListener("input", (e) => {
    themeConfig.customSecondary = e.target.value;
    if (customSecondaryHex) customSecondaryHex.value = e.target.value.toUpperCase();
    applyTheme(themeConfig);
  });
}

if (customSecondaryHex) {
  customSecondaryHex.addEventListener("change", (e) => {
    let val = e.target.value.trim();
    if (!val.startsWith("#")) val = "#" + val;
    if (/^#[0-9A-F]{6}$/i.test(val)) {
      themeConfig.customSecondary = val;
      if (customSecondaryInput) customSecondaryInput.value = val;
      applyTheme(themeConfig);
    }
  });
}

if (glowIntensityRange) {
  glowIntensityRange.addEventListener("input", (e) => {
    themeConfig.glowLevel = parseInt(e.target.value, 10);
    applyTheme(themeConfig);
  });
}

if (toggleGridBtn) {
  toggleGridBtn.addEventListener("click", () => {
    themeConfig.gridActive = !themeConfig.gridActive;
    applyTheme(themeConfig);
    showToastNotice(themeConfig.gridActive ? "Grid Matrix Enabled" : "Grid Matrix Disabled");
  });
}

if (resetThemeBtn) {
  resetThemeBtn.addEventListener("click", () => {
    themeConfig = {
      theme: "cyber",
      customPrimary: null,
      customSecondary: null,
      glowLevel: 2,
      gridActive: true
    };
    applyTheme(themeConfig);
    renderThemePresets();
    renderFullPageThemePresets();
    showToastNotice("Reset to Cyber Tool Default");
  });
}

// Full-Page Theme Studio Inputs
const pagePrimaryInput = document.getElementById("pageCustomPrimaryInput");
const pagePrimaryHex = document.getElementById("pageCustomPrimaryHex");
const pageSecondaryInput = document.getElementById("pageCustomSecondaryInput");
const pageSecondaryHex = document.getElementById("pageCustomSecondaryHex");
const pageGlowRange = document.getElementById("pageGlowIntensityRange");
const pageToggleGridBtn = document.getElementById("pageToggleGridBtn");
const pageResetThemeBtn = document.getElementById("pageResetThemeBtn");

if (pagePrimaryInput) {
  pagePrimaryInput.addEventListener("input", (e) => {
    themeConfig.customPrimary = e.target.value;
    if (pagePrimaryHex) pagePrimaryHex.value = e.target.value.toUpperCase();
    applyTheme(themeConfig);
  });
}

if (pagePrimaryHex) {
  pagePrimaryHex.addEventListener("change", (e) => {
    let val = e.target.value.trim();
    if (!val.startsWith("#")) val = "#" + val;
    if (/^#[0-9A-F]{6}$/i.test(val)) {
      themeConfig.customPrimary = val;
      if (pagePrimaryInput) pagePrimaryInput.value = val;
      applyTheme(themeConfig);
    }
  });
}

if (pageSecondaryInput) {
  pageSecondaryInput.addEventListener("input", (e) => {
    themeConfig.customSecondary = e.target.value;
    if (pageSecondaryHex) pageSecondaryHex.value = e.target.value.toUpperCase();
    applyTheme(themeConfig);
  });
}

if (pageSecondaryHex) {
  pageSecondaryHex.addEventListener("change", (e) => {
    let val = e.target.value.trim();
    if (!val.startsWith("#")) val = "#" + val;
    if (/^#[0-9A-F]{6}$/i.test(val)) {
      themeConfig.customSecondary = val;
      if (pageSecondaryInput) pageSecondaryInput.value = val;
      applyTheme(themeConfig);
    }
  });
}

if (pageGlowRange) {
  pageGlowRange.addEventListener("input", (e) => {
    themeConfig.glowLevel = parseInt(e.target.value, 10);
    applyTheme(themeConfig);
  });
}

if (pageToggleGridBtn) {
  pageToggleGridBtn.addEventListener("click", () => {
    themeConfig.gridActive = !themeConfig.gridActive;
    applyTheme(themeConfig);
    showToastNotice(themeConfig.gridActive ? "Grid Matrix Enabled" : "Grid Matrix Disabled");
  });
}

if (pageResetThemeBtn) {
  pageResetThemeBtn.addEventListener("click", () => {
    themeConfig = {
      theme: "cyber",
      customPrimary: null,
      customSecondary: null,
      glowLevel: 2,
      gridActive: true
    };
    applyTheme(themeConfig);
    renderThemePresets();
    renderFullPageThemePresets();
    showToastNotice("Reset to Cyber Tool Default");
  });
}

// ============================================================================
// 15. User Profile & Identity Editing System
// ============================================================================

const DEFAULT_PROFILE = {
  name: "Alex Mercer",
  role: "Lead NLP Engineer",
  org: "FixFlow Research Lab",
  email: "alex.mercer@fixflow.ai",
  avatar: "🧑‍💻",
  bio: "Building zero-hallucination NLP pipelines and Dynamic Programming algorithms for mission-critical enterprise workflows.",
  apiKey: "sk-fixflow-dp-live-v2-preview",
  defaultEngine: "spell",
  defaultTone: "professional",
  soundEnabled: true,
  autoSaveHistory: true
};

let profileState = Object.assign({}, DEFAULT_PROFILE);
try {
  const p = localStorage.getItem("fixflow_user_profile");
  if (p) profileState = Object.assign(profileState, JSON.parse(p));
} catch (e) {
  console.warn("Could not load user profile:", e);
}

function syncProfileUI() {
  // Sidebar elements
  const sidebarAvatar = document.getElementById("sidebarAvatarDisplay");
  const sidebarName = document.getElementById("sidebarNameDisplay");
  const sidebarRole = document.getElementById("sidebarRoleDisplay");
  if (sidebarAvatar) sidebarAvatar.textContent = profileState.avatar;
  if (sidebarName) sidebarName.textContent = profileState.name;
  if (sidebarRole) sidebarRole.textContent = profileState.role;

  // Profile Header elements
  const headerAvatar = document.getElementById("profileHeaderAvatar");
  const headerName = document.getElementById("profileHeaderName");
  const headerRole = document.getElementById("profileHeaderRole");
  const headerOrg = document.getElementById("profileHeaderOrg");
  if (headerAvatar) headerAvatar.textContent = profileState.avatar;
  if (headerName) headerName.textContent = profileState.name;
  if (headerRole) headerRole.textContent = profileState.role;
  if (headerOrg) headerOrg.textContent = `🏛️ ${profileState.org}`;

  // Form Inputs
  const nameInput = document.getElementById("profileNameInput");
  const roleInput = document.getElementById("profileRoleInput");
  const orgInput = document.getElementById("profileOrgInput");
  const emailInput = document.getElementById("profileEmailInput");
  const bioInput = document.getElementById("profileBioInput");
  const apiKeyInput = document.getElementById("profileApiKeyInput");
  const defaultEngine = document.getElementById("profileDefaultEngine");
  const defaultTone = document.getElementById("profileDefaultTone");

  if (nameInput) nameInput.value = profileState.name;
  if (roleInput) roleInput.value = profileState.role;
  if (orgInput) orgInput.value = profileState.org;
  if (emailInput) emailInput.value = profileState.email;
  if (bioInput) bioInput.value = profileState.bio;
  if (apiKeyInput) apiKeyInput.value = profileState.apiKey;
  if (defaultEngine) defaultEngine.value = profileState.defaultEngine;
  if (defaultTone) defaultTone.value = profileState.defaultTone;

  // Avatar Choice Buttons
  document.querySelectorAll(".avatar-choice-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.avatar === profileState.avatar);
  });

  // Sound & Autosave Toggles
  const soundToggle = document.getElementById("profileSoundToggle");
  const soundLabel = document.getElementById("profileSoundLabel");
  if (soundToggle) soundToggle.classList.toggle("active", profileState.soundEnabled);
  if (soundLabel) soundLabel.textContent = `Audio Haptics: ${profileState.soundEnabled ? "ON" : "OFF"}`;

  const autoSaveToggle = document.getElementById("profileAutoSaveToggle");
  const autoSaveLabel = document.getElementById("profileAutoSaveLabel");
  if (autoSaveToggle) autoSaveToggle.classList.toggle("active", profileState.autoSaveHistory);
  if (autoSaveLabel) autoSaveLabel.textContent = `Auto-Save History: ${profileState.autoSaveHistory ? "ON" : "OFF"}`;

  // Profile Header Stats
  const statRuns = document.getElementById("profileStatRuns");
  if (statRuns) statRuns.textContent = auditHistory.length;
}

// Avatar Choices
document.querySelectorAll(".avatar-choice-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    profileState.avatar = btn.dataset.avatar;
    document.querySelectorAll(".avatar-choice-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const customAvatarInput = document.getElementById("customAvatarInput");
    if (customAvatarInput) customAvatarInput.value = "";
    syncProfileUI();
  });
});

const customAvatarInput = document.getElementById("customAvatarInput");
if (customAvatarInput) {
  customAvatarInput.addEventListener("input", (e) => {
    const val = e.target.value.trim();
    if (val) {
      profileState.avatar = val;
      document.querySelectorAll(".avatar-choice-btn").forEach(b => b.classList.remove("active"));
      syncProfileUI();
    }
  });
}

// Save Profile
const saveProfileBtn = document.getElementById("saveProfileBtn");
if (saveProfileBtn) {
  saveProfileBtn.addEventListener("click", () => {
    const nameInput = document.getElementById("profileNameInput");
    const roleInput = document.getElementById("profileRoleInput");
    const orgInput = document.getElementById("profileOrgInput");
    const emailInput = document.getElementById("profileEmailInput");
    const bioInput = document.getElementById("profileBioInput");
    const apiKeyInput = document.getElementById("profileApiKeyInput");
    const defaultEngine = document.getElementById("profileDefaultEngine");
    const defaultTone = document.getElementById("profileDefaultTone");

    if (nameInput) profileState.name = nameInput.value.trim() || DEFAULT_PROFILE.name;
    if (roleInput) profileState.role = roleInput.value.trim() || DEFAULT_PROFILE.role;
    if (orgInput) profileState.org = orgInput.value.trim() || DEFAULT_PROFILE.org;
    if (emailInput) profileState.email = emailInput.value.trim() || DEFAULT_PROFILE.email;
    if (bioInput) profileState.bio = bioInput.value.trim() || DEFAULT_PROFILE.bio;
    if (apiKeyInput) profileState.apiKey = apiKeyInput.value.trim();
    if (defaultEngine) profileState.defaultEngine = defaultEngine.value;
    if (defaultTone) profileState.defaultTone = defaultTone.value;

    try {
      localStorage.setItem("fixflow_user_profile", JSON.stringify(profileState));
    } catch (e) {
      console.warn("Could not save profile:", e);
    }

    syncProfileUI();
    showToastNotice("✅ Profile details updated successfully!");
  });
}

// Reset Profile
const resetProfileBtn = document.getElementById("resetProfileBtn");
if (resetProfileBtn) {
  resetProfileBtn.addEventListener("click", () => {
    profileState = Object.assign({}, DEFAULT_PROFILE);
    try {
      localStorage.setItem("fixflow_user_profile", JSON.stringify(profileState));
    } catch (e) {}
    syncProfileUI();
    showToastNotice("Reset profile to default credentials");
  });
}

// Export Profile JSON
const exportProfileBtn = document.getElementById("exportProfileBtn");
if (exportProfileBtn) {
  exportProfileBtn.addEventListener("click", () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(profileState, null, 2));
    const dlAnchor = document.createElement("a");
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", `fixflow-profile-${Date.now()}.json`);
    dlAnchor.click();
    showToastNotice("Exported profile JSON");
  });
}

// API Key Visibility Toggle
const toggleApiKeyVisibility = document.getElementById("toggleApiKeyVisibility");
if (toggleApiKeyVisibility) {
  toggleApiKeyVisibility.addEventListener("click", () => {
    const input = document.getElementById("profileApiKeyInput");
    if (input) {
      input.type = input.type === "password" ? "text" : "password";
      toggleApiKeyVisibility.textContent = input.type === "password" ? "👁️" : "🔒";
    }
  });
}

// Sound & Autosave Toggles
const profileSoundToggle = document.getElementById("profileSoundToggle");
if (profileSoundToggle) {
  profileSoundToggle.addEventListener("click", () => {
    profileState.soundEnabled = !profileState.soundEnabled;
    syncProfileUI();
    try {
      localStorage.setItem("fixflow_user_profile", JSON.stringify(profileState));
    } catch (e) {}
  });
}

const profileAutoSaveToggle = document.getElementById("profileAutoSaveToggle");
if (profileAutoSaveToggle) {
  profileAutoSaveToggle.addEventListener("click", () => {
    profileState.autoSaveHistory = !profileState.autoSaveHistory;
    syncProfileUI();
    try {
      localStorage.setItem("fixflow_user_profile", JSON.stringify(profileState));
    } catch (e) {}
  });
}

// ============================================================================
// 16. Audit History & Activity Logs System
// ============================================================================

let auditHistory = [];
try {
  const h = localStorage.getItem("fixflow_audit_history");
  if (h) auditHistory = JSON.parse(h);
} catch (e) {
  console.warn("Could not load audit history:", e);
}

function updateHistoryBadge() {
  const badge = document.getElementById("historyCountBadge");
  if (badge) badge.textContent = auditHistory.length;
}

function recordAuditHistory(entry) {
  auditHistory.unshift({
    id: Date.now(),
    channel: entry.channel || "direct",
    channelLabel: entry.channelLabel || "Text Studio",
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    date: new Date().toLocaleDateString(),
    original: entry.original,
    corrected: entry.corrected,
    changesCount: entry.changesCount || 0,
    distance: entry.distance || 0,
    latency: entry.latency || 0
  });

  if (auditHistory.length > 50) auditHistory = auditHistory.slice(0, 50);

  try {
    localStorage.setItem("fixflow_audit_history", JSON.stringify(auditHistory));
  } catch (e) {
    console.warn("Could not save audit history:", e);
  }

  updateHistoryBadge();
  const statRuns = document.getElementById("profileStatRuns");
  if (statRuns) statRuns.textContent = auditHistory.length;
}

function renderHistoryList() {
  const container = document.getElementById("historyListContainer");
  if (!container) return;

  if (auditHistory.length === 0) {
    container.innerHTML = `
      <div class="history-empty-card">
        <div class="history-empty-icon">⏱️</div>
        <h3 style="color: var(--text-main); font-weight: 700; margin-bottom: 6px;">No Correction History Yet</h3>
        <p style="font-size: 0.9rem;">Runs from Text Studio, Presentations, Email, and AI Prompts will be automatically recorded here.</p>
        <button class="btn-primary" style="width: auto; margin-top: 18px; padding: 10px 22px;" onclick="switchPage('direct')">
          Launch Text Studio
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = auditHistory.map(item => `
    <div class="history-card">
      <div class="history-card-header">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span class="history-channel-badge">${escapeHtml(item.channelLabel)}</span>
          <span class="history-timestamp">${escapeHtml(item.date)} at ${escapeHtml(item.timestamp)}</span>
        </div>
        <button class="btn-ghost restore-history-btn" data-history-id="${item.id}" style="padding: 4px 10px; font-size: 0.78rem;">
          <span>↩</span> Restore into Studio
        </button>
      </div>

      <div class="history-snippets-grid">
        <div class="history-snippet-box">
          <div style="font-size: 0.72rem; text-transform: uppercase; color: var(--text-dim); margin-bottom: 4px; font-weight: 700;">Input Snippet</div>
          <div>${escapeHtml(item.original.slice(0, 140))}${item.original.length > 140 ? "..." : ""}</div>
        </div>
        <div class="history-snippet-box" style="border-color: var(--border-focus);">
          <div style="font-size: 0.72rem; text-transform: uppercase; color: var(--accent-primary); margin-bottom: 4px; font-weight: 700;">Polished Output</div>
          <div>${escapeHtml(item.corrected.slice(0, 140))}${item.corrected.length > 140 ? "..." : ""}</div>
        </div>
      </div>

      <div class="history-card-footer">
        <div class="history-metric-chips">
          <span class="history-metric-chip">⚡ Latency: ${escapeHtml(String(item.latency))}ms</span>
          <span class="history-metric-chip">✏️ Edits: ${escapeHtml(String(item.changesCount))}</span>
          <span class="history-metric-chip">📏 Edit Dist: ${escapeHtml(String(item.distance))}</span>
        </div>
      </div>
    </div>
  `).join("");

  // Attach restore listeners
  container.querySelectorAll(".restore-history-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = parseInt(btn.dataset.historyId, 10);
      const item = auditHistory.find(x => x.id === id);
      if (item) {
        restoreHistoryItem(item);
      }
    });
  });
}

function restoreHistoryItem(item) {
  if (item.channel === "direct") {
    switchPage("direct");
    if (directInputText) {
      directInputText.value = item.original;
      updateCharCount(directInputText, directCharCount);
    }
  } else if (item.channel === "files") {
    switchPage("files");
    if (extractedDocText) {
      extractedDocText.value = item.original;
      updateCharCount(extractedDocText, docCharCount);
    }
  } else if (item.channel === "email") {
    switchPage("email");
    if (emailBody) emailBody.value = item.original;
  } else if (item.channel === "prompt") {
    switchPage("prompt");
    if (rawPromptInput) rawPromptInput.value = item.original;
  } else {
    switchPage("direct");
    if (directInputText) {
      directInputText.value = item.original;
      updateCharCount(directInputText, directCharCount);
    }
  }
  showToastNotice(`Restored snippet into ${item.channelLabel}`);
}

// Clear History Button
const clearHistoryBtn = document.getElementById("clearHistoryBtn");
if (clearHistoryBtn) {
  clearHistoryBtn.addEventListener("click", () => {
    if (confirm("Clear all recorded correction logs?")) {
      auditHistory = [];
      try {
        localStorage.removeItem("fixflow_audit_history");
      } catch (e) {}
      updateHistoryBadge();
      renderHistoryList();
      const statRuns = document.getElementById("profileStatRuns");
      if (statRuns) statRuns.textContent = "0";
      showToast("Audit history cleared");
    }
  });
}

// Toast Notice Helper
function showToastNotice(msg) {
  showToast(msg);
}

// ============================================================================
// 17. New Conversation / New Session System
// ============================================================================
const newConversationBtn = document.getElementById("newConversationBtn");
const topbarNewConvBtn = document.getElementById("topbarNewConvBtn");

function startNewConversation() {
  // Archive existing text if it was meaningful so work is never lost
  const activeDraft = (directInputText ? directInputText.value.trim() : "");
  if (activeDraft && activeDraft.length > 5 && typeof recordAuditHistory === "function") {
    recordAuditHistory({
      channel: currentPageId,
      channelLabel: PAGE_TITLES[currentPageId] || "Session Draft",
      original: activeDraft,
      corrected: activeDraft,
      changesCount: 0,
      distance: 0,
      latency: 0
    });
  }

  // Clear Text Studio input
  if (directInputText) {
    directInputText.value = "";
    updateCharCount(directInputText, directCharCount);
  }

  // Clear Email Polisher inputs
  const emSubject = document.getElementById("emailSubject");
  const emBody = document.getElementById("emailBody");
  if (emSubject) emSubject.value = "";
  if (emBody) emBody.value = "";

  // Clear Prompt Optimizer input
  const rawPrompt = document.getElementById("rawPromptInput");
  if (rawPrompt) rawPrompt.value = "";

  // Clear File Upload if any
  if (typeof removeFileBtn !== "undefined" && removeFileBtn) {
    try { removeFileBtn.click(); } catch (e) {}
  }

  // Reset Results View
  if (resultsSection) {
    resultsSection.style.display = "none";
  }
  lastCorrectedOutput = "";

  // If currently on a utility/diagnostic page, navigate to Text Studio
  if (["matrix", "history", "theme", "profile"].includes(currentPageId)) {
    switchPage("direct");
  }

  // Focus active textarea for immediate productivity
  setTimeout(() => {
    if (currentPageId === "direct" && directInputText) {
      directInputText.focus();
    } else if (currentPageId === "email") {
      const b = document.getElementById("emailBody");
      if (b) b.focus();
    } else if (currentPageId === "prompt") {
      const p = document.getElementById("rawPromptInput");
      if (p) p.focus();
    }
  }, 60);

  showToast("✨ Started new conversation session!");
}

if (newConversationBtn) {
  newConversationBtn.addEventListener("click", () => {
    startNewConversation();
  });
}

if (topbarNewConvBtn) {
  topbarNewConvBtn.addEventListener("click", () => {
    startNewConversation();
  });
}

// Global Keyboard Shortcut: Ctrl+N or Cmd+N
window.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && (e.key === "n" || e.key === "N")) {
    e.preventDefault();
    startNewConversation();
  }
});

// Initial sync on boot
applyTheme(themeConfig, false);
syncProfileUI();
updateHistoryBadge();

