/* ─────────────────────────────────────────────
   Paramahamsa Vidyaniketana  ·  app.js
───────────────────────────────────────────── */
"use strict";

const SUBJECTS = ["Maths", "English", "Science", "Kannada", "Hindi"];
const EMOJIS   = { Maths:"📐", English:"📖", Science:"🔬", Kannada:"✍️", Hindi:"📜" };

const CAT_CLASS = { Good:"good", Average:"average", Bad:"bad", Fail:"fail" };
const CAT_ICON  = { Good:"★ Good", Average:"◆ Average", Bad:"▲ Bad", Fail:"✖ Fail" };
const GRADE_CLASS = { "A+":"grade-aplus","A":"grade-a","B":"grade-b","C":"grade-c","D":"grade-d","F":"grade-f" };

let allNames = [];

// ── Boot ────────────────────────────────────────
(async () => {
  // Load student names for autocomplete
  const r = await fetch("/students");
  allNames = await r.json();

  // Load stats for header + dist pills
  const s = await fetch("/stats");
  const stats = await s.json();

  document.getElementById("stat-students").innerHTML =
    `<span class="dot"></span>${stats.total} Students`;
  document.getElementById("stat-accuracy").textContent =
    `Model Accuracy: ${stats.accuracy}%`;

  const dist = stats.distribution;
  const distRow = document.getElementById("dist-row");
  [["Good","good"],["Average","average"],["Bad","bad"],["Fail","fail"]].forEach(([cat, cls]) => {
    const pill = document.createElement("div");
    pill.className = `dist-pill ${cls}`;
    pill.innerHTML = `<span class="dist-count">${dist[cat]}</span> ${cat}`;
    pill.title = `Click to search first ${cat} student`;
    pill.addEventListener("click", () => {
      const match = allNames.find(n => {
        // We can't filter by category client-side easily, so just show pill count
      });
    });
    distRow.appendChild(pill);
  });
})();


// ── Autocomplete ────────────────────────────────
const searchInput = document.getElementById("search-input");
const acBox       = document.getElementById("autocomplete");
let acIndex       = -1;

searchInput.addEventListener("input", () => {
  const q = searchInput.value.trim().toLowerCase();
  acBox.innerHTML = "";
  acIndex = -1;
  if (!q) { acBox.classList.add("hidden"); return; }

  const matches = allNames.filter(n => n.toLowerCase().includes(q)).slice(0, 8);
  if (!matches.length) { acBox.classList.add("hidden"); return; }

  matches.forEach((name, i) => {
    const item = document.createElement("div");
    item.className = "ac-item";
    // Highlight matching part
    const idx = name.toLowerCase().indexOf(q);
    item.innerHTML =
      name.slice(0, idx) +
      `<mark>${name.slice(idx, idx + q.length)}</mark>` +
      name.slice(idx + q.length);
    item.addEventListener("mousedown", e => {
      e.preventDefault();
      searchInput.value = name;
      acBox.classList.add("hidden");
      doSearch(name);
    });
    acBox.appendChild(item);
  });
  acBox.classList.remove("hidden");
});

searchInput.addEventListener("keydown", e => {
  const items = acBox.querySelectorAll(".ac-item");
  if (e.key === "ArrowDown") {
    acIndex = Math.min(acIndex + 1, items.length - 1);
    items.forEach((el, i) => el.classList.toggle("active", i === acIndex));
    e.preventDefault();
  } else if (e.key === "ArrowUp") {
    acIndex = Math.max(acIndex - 1, -1);
    items.forEach((el, i) => el.classList.toggle("active", i === acIndex));
    e.preventDefault();
  } else if (e.key === "Enter") {
    if (acIndex >= 0 && items[acIndex]) {
      searchInput.value = items[acIndex].textContent;
      acBox.classList.add("hidden");
      doSearch(searchInput.value);
    } else {
      doSearch(searchInput.value.trim());
    }
  } else if (e.key === "Escape") {
    acBox.classList.add("hidden");
  }
});

document.addEventListener("click", e => {
  if (!e.target.closest(".search-box")) acBox.classList.add("hidden");
});


// ── Search trigger ───────────────────────────────
document.getElementById("search-btn").addEventListener("click", () => {
  doSearch(searchInput.value.trim());
});


// ── Core search function ─────────────────────────
async function doSearch(name) {
  if (!name) return;
  acBox.classList.add("hidden");
  clearError();

  const btn = document.getElementById("search-btn");
  btn.classList.add("loading");
  btn.disabled = true;

  try {
    const res  = await fetch("/predict", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ name }),
    });
    const data = await res.json();

    if (data.status === "ok") {
      renderResult(data);
    } else if (data.status === "not_found") {
      showError(`${data.message}  ${data.hint || ""}`);
    } else {
      showError(data.message || "An error occurred.");
    }
  } catch (err) {
    showError("Network error — is the server running?");
  } finally {
    btn.classList.remove("loading");
    btn.disabled = false;
  }
}


// ── Render result ────────────────────────────────
function renderResult(d) {
  const cls = CAT_CLASS[d.category] || "average";

  // Category chip
  const chip = document.getElementById("category-chip");
  chip.textContent  = CAT_ICON[d.category];
  chip.className    = `category-chip chip-${cls}`;

  // Avatar + name
  document.getElementById("res-avatar").textContent = d.name.charAt(0).toUpperCase();
  document.getElementById("res-name").textContent   = d.name;
  document.getElementById("res-confidence").textContent = `Model confidence: ${d.confidence}%`;

  // Attendance badge
  const attBadge = document.getElementById("res-attendance-badge");
  const att      = d.attendance;
  let attCls, attLabel;
  if      (att >= 85) { attCls = "att-good"; attLabel = `${att}% — Excellent Attendance`; }
  else if (att >= 75) { attCls = "att-ok";   attLabel = `${att}% — Satisfactory`; }
  else if (att >= 60) { attCls = "att-poor"; attLabel = `${att}% — Poor Attendance`; }
  else                { attCls = "att-crit"; attLabel = `${att}% — Critical Attendance`; }
  attBadge.textContent = attLabel;
  attBadge.className   = `att-badge ${attCls}`;

  // Score ring (out of 100)
  document.getElementById("res-overall").textContent = d.overall_avg;
  const circumference = 201;
  const offset = circumference - (d.overall_pct / 100) * circumference;
  setTimeout(() => {
    document.getElementById("ring-fill").style.strokeDashoffset = offset;
  }, 100);

  // Subject grid
  const grid = document.getElementById("subject-grid");
  grid.innerHTML = "";
  SUBJECTS.forEach((subj, idx) => {
    const sc   = d.subject_scores[subj];
    const weak = d.weak_subjects.includes(subj);
    const barColor = sc.percent >= 75 ? "#16a34a"
                   : sc.percent >= 55 ? "#ca8a04"
                   : sc.percent >= 35 ? "#ea580c" : "#dc2626";
    const gradeCls = GRADE_CLASS[sc.grade] || "grade-f";
    const card = document.createElement("div");
    card.className = `subj-card${weak ? " weak" : ""}`;
    card.style.animationDelay = (idx * 0.06) + "s";
    card.innerHTML = `
      <span class="subj-emoji">${EMOJIS[subj]}</span>
      <div class="subj-name">${subj}</div>
      <div><span class="subj-total">${sc.total}</span><span class="subj-max"> / 100</span></div>
      <div class="subj-grade ${gradeCls}">${sc.grade}</div>
      <div class="subj-bar-track"><div class="subj-bar-fill" style="width:0%;background:${barColor}"></div></div>
      <div class="subj-breakdown">
        <span class="breakdown-item">Assign <span>${sc.assignment}</span></span>
        <span class="breakdown-item">Internal <span>${sc.internal}</span></span>
        <span class="breakdown-item">Exam <span>${sc.exam}</span></span>
      </div>
      ${weak ? '<div class="weak-tag">⚠ Needs Attention</div>' : ""}
    `;
    grid.appendChild(card);
    // Animate bar after a tick
    setTimeout(() => {
      card.querySelector(".subj-bar-fill").style.width = sc.percent + "%";
    }, 150 + idx * 60);
  });

  // Assessment
  document.getElementById("assessment-headline").textContent = d.headline;
  document.getElementById("assessment-overview").textContent = d.overview;

  // Action plan
  const actionList = document.getElementById("action-list");
  actionList.innerHTML = "";
  d.action_plan.forEach((step, i) => {
    const li = document.createElement("li");
    li.textContent = step;
    li.style.animationDelay = (i * 0.07) + "s";
    actionList.appendChild(li);
  });

  // Subject tips
  const tipsGrid    = document.getElementById("tips-grid");
  const weakSection = document.getElementById("weak-section");
  tipsGrid.innerHTML = "";
  const tipEntries = Object.entries(d.subject_tips || {});
  if (tipEntries.length) {
    weakSection.classList.remove("hidden");
    tipEntries.forEach(([subj, tips]) => {
      const card = document.createElement("div");
      card.className = "tip-card";
      card.innerHTML = `
        <div class="tip-card-title">${EMOJIS[subj]} ${subj}</div>
        <ul>${tips.map(t => `<li>${t}</li>`).join("")}</ul>
      `;
      tipsGrid.appendChild(card);
    });
  } else {
    weakSection.classList.add("hidden");
  }

  // Parent note
  document.getElementById("parent-card").textContent = d.parent_note;

  // Show result, hide search
  document.querySelector(".search-panel").classList.add("hidden");
  document.getElementById("result-panel").classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}


// ── Back button ──────────────────────────────────
document.getElementById("back-btn").addEventListener("click", () => {
  document.getElementById("result-panel").classList.add("hidden");
  document.querySelector(".search-panel").classList.remove("hidden");
  // Reset ring
  document.getElementById("ring-fill").style.strokeDashoffset = 201;
  searchInput.value = "";
  clearError();
});


// ── Helpers ──────────────────────────────────────
function showError(msg) {
  const el = document.getElementById("search-error");
  el.textContent = msg;
  el.classList.remove("hidden");
}
function clearError() {
  document.getElementById("search-error").classList.add("hidden");
}

// ═══════════════════════════════════════════════
//  ADD STUDENT FEATURE
// ═══════════════════════════════════════════════

const SUBJECTS_FORM = ["Maths", "English", "Science", "Kannada", "Hindi"];
let currentStep = 1;

// ── Open / close modal ───────────────────────────
document.getElementById("btn-add-student").addEventListener("click", openModal);
document.getElementById("modal-close").addEventListener("click", closeModal);
document.getElementById("add-modal").addEventListener("click", e => {
  if (e.target === document.getElementById("add-modal")) closeModal();
});

function openModal() {
  resetModal();
  document.getElementById("add-modal").classList.remove("hidden");
  document.body.style.overflow = "hidden";
}
function closeModal() {
  document.getElementById("add-modal").classList.add("hidden");
  document.body.style.overflow = "";
}
function resetModal() {
  // Clear all inputs
  ["f-name","f-roll","f-attendance"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
  SUBJECTS_FORM.forEach(s => {
    ["a","i","e"].forEach(p => {
      const el = document.getElementById(`${p}-${s}`);
      if (el) el.value = "";
    });
  });
  hideModalMsg();
  goToStep(1);
}

// ── Step navigation ──────────────────────────────
function goToStep(step) {
  currentStep = step;
  document.getElementById("form-step-1").classList.toggle("active", step === 1);
  document.getElementById("form-step-2").classList.toggle("active", step === 2);

  // Step dots
  const dot1 = document.getElementById("sdot-1");
  const dot2 = document.getElementById("sdot-2");
  dot1.className = "step-dot " + (step === 1 ? "active" : "done");
  dot2.className = "step-dot " + (step === 2 ? "active" : "");

  // Buttons
  const backBtn = document.getElementById("modal-back-btn");
  const nextBtn = document.getElementById("modal-next-btn");
  backBtn.style.visibility = step === 1 ? "hidden" : "visible";
  nextBtn.textContent = step === 1 ? "Next →" : "Submit";
}

document.getElementById("modal-back-btn").addEventListener("click", () => {
  hideModalMsg();
  goToStep(1);
});

document.getElementById("modal-next-btn").addEventListener("click", () => {
  hideModalMsg();
  if (currentStep === 1) {
    if (validateStep1()) goToStep(2);
  } else {
    if (validateStep2()) submitStudent();
  }
});

// ── Validation Step 1 ────────────────────────────
function validateStep1() {
  const name = document.getElementById("f-name").value.trim();
  const att  = parseFloat(document.getElementById("f-attendance").value);
  if (!name) { showModalError("Please enter the student name."); return false; }
  if (isNaN(att) || att < 0 || att > 100) {
    showModalError("Attendance must be a number between 0 and 100.");
    return false;
  }
  return true;
}

// ── Validation Step 2 ────────────────────────────
function validateStep2() {
  for (const s of SUBJECTS_FORM) {
    const a = parseFloat(document.getElementById(`a-${s}`).value);
    const i = parseFloat(document.getElementById(`i-${s}`).value);
    const e = parseFloat(document.getElementById(`e-${s}`).value);
    if (isNaN(a) || a < 0 || a > 25)  { showModalError(`${s}: Assignment must be 0–25.`);  return false; }
    if (isNaN(i) || i < 0 || i > 50)  { showModalError(`${s}: Internal must be 0–50.`);    return false; }
    if (isNaN(e) || e < 0 || e > 100) { showModalError(`${s}: Exam must be 0–100.`);        return false; }
  }
  return true;
}

// ── Submit ───────────────────────────────────────
async function submitStudent() {
  const nextBtn = document.getElementById("modal-next-btn");
  nextBtn.disabled = true;
  nextBtn.textContent = "Saving…";

  const payload = {
    name:       document.getElementById("f-name").value.trim(),
    roll:       document.getElementById("f-roll").value.trim(),
    attendance: parseFloat(document.getElementById("f-attendance").value),
  };
  SUBJECTS_FORM.forEach(s => {
    payload[`assign_${s}`]   = parseFloat(document.getElementById(`a-${s}`).value);
    payload[`internal_${s}`] = parseFloat(document.getElementById(`i-${s}`).value);
    payload[`exam_${s}`]     = parseFloat(document.getElementById(`e-${s}`).value);
  });

  try {
    const res  = await fetch("/add_student", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.status === "ok") {
      showModalSuccess(`✔ ${data.message}  Performance: ${data.performance}  |  Overall: ${data.overall}/100`);
      // Refresh student list & stats
      allNames = await (await fetch("/students")).json();
      const stats = await (await fetch("/stats")).json();
      document.getElementById("stat-students").innerHTML =
        `<span class="dot"></span>${stats.total} Students`;
      // Refresh dist pills
      const distRow = document.getElementById("dist-row");
      distRow.innerHTML = "";
      const dist = stats.distribution;
      [["Good","good"],["Average","average"],["Bad","bad"],["Fail","fail"]].forEach(([cat, cls]) => {
        const pill = document.createElement("div");
        pill.className = `dist-pill ${cls}`;
        pill.innerHTML = `<span class="dist-count">${dist[cat]}</span> ${cat}`;
        distRow.appendChild(pill);
      });
      // Reset form after 2s and close
      setTimeout(() => { closeModal(); }, 2200);
    } else {
      showModalError(data.message || "Something went wrong.");
    }
  } catch (err) {
    showModalError("Network error — is the server running?");
  } finally {
    nextBtn.disabled = false;
    nextBtn.textContent = "Submit";
  }
}

// ── Message helpers ──────────────────────────────
function showModalError(msg) {
  document.getElementById("modal-error").textContent = msg;
  document.getElementById("modal-error").classList.remove("hidden");
  document.getElementById("modal-success").classList.add("hidden");
}
function showModalSuccess(msg) {
  document.getElementById("modal-success").textContent = msg;
  document.getElementById("modal-success").classList.remove("hidden");
  document.getElementById("modal-error").classList.add("hidden");
}
function hideModalMsg() {
  document.getElementById("modal-error").classList.add("hidden");
  document.getElementById("modal-success").classList.add("hidden");
}

// ═══════════════════════════════════════════════
//  MANAGE STUDENTS FEATURE
// ═══════════════════════════════════════════════

let allStudentRecords = [];
let editOriginalName  = "";
let editOriginalRoll  = "";
let editCurrentStep   = 1;

// ── Open / close manage modal ─────────────────
document.getElementById("btn-manage-students").addEventListener("click", openManageModal);
document.getElementById("manage-modal-close").addEventListener("click", closeManageModal);
document.getElementById("manage-modal").addEventListener("click", e => {
  if (e.target === document.getElementById("manage-modal")) closeManageModal();
});

async function openManageModal() {
  document.getElementById("manage-modal").classList.remove("hidden");
  document.body.style.overflow = "hidden";
  document.getElementById("manage-search").value = "";
  document.getElementById("manage-loading").classList.remove("hidden");
  document.getElementById("manage-list").innerHTML = "";
  document.getElementById("manage-empty").classList.add("hidden");
  await loadAllStudents();
}

function closeManageModal() {
  document.getElementById("manage-modal").classList.add("hidden");
  document.body.style.overflow = "";
}

async function loadAllStudents() {
  try {
    const res = await fetch("/all_students");
    allStudentRecords = await res.json();
    document.getElementById("manage-loading").classList.add("hidden");
    renderStudentList(allStudentRecords);
  } catch (err) {
    document.getElementById("manage-loading").textContent = "Failed to load students.";
  }
}

function renderStudentList(records) {
  const listEl = document.getElementById("manage-list");
  const emptyEl = document.getElementById("manage-empty");
  listEl.innerHTML = "";

  if (!records.length) {
    emptyEl.classList.remove("hidden");
    return;
  }
  emptyEl.classList.add("hidden");

  const perfCls = { Good: "good", Average: "average", Bad: "bad", Fail: "fail" };

  records.forEach(rec => {
    const row = document.createElement("div");
    row.className = "student-row";
    const initial = rec.name ? rec.name.charAt(0).toUpperCase() : "?";
    const cls = perfCls[rec.performance] || "average";
    row.innerHTML = `
      <div class="student-row-avatar">${initial}</div>
      <div class="student-row-info">
        <div class="student-row-name">${rec.name}</div>
        <div class="student-row-meta">Roll: ${rec.roll || "—"} &nbsp;·&nbsp; Attendance: ${rec.attendance}%</div>
      </div>
      <div class="student-row-perf ${cls}">${rec.performance}</div>
      <div class="student-row-actions">
        <button class="btn-edit" title="Edit student">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          Edit
        </button>
        <button class="btn-delete" title="Delete student">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
          Delete
        </button>
      </div>
    `;

    row.querySelector(".btn-edit").addEventListener("click", () => openEditModal(rec));
    row.querySelector(".btn-delete").addEventListener("click", () => confirmDelete(rec));
    listEl.appendChild(row);
  });
}

// ── Search filter ─────────────────────────────
document.getElementById("manage-search").addEventListener("input", () => {
  const q = document.getElementById("manage-search").value.trim().toLowerCase();
  if (!q) {
    renderStudentList(allStudentRecords);
    return;
  }
  const filtered = allStudentRecords.filter(r =>
    r.name.toLowerCase().includes(q) ||
    String(r.roll).toLowerCase().includes(q)
  );
  renderStudentList(filtered);
});

// ── Delete with confirm ───────────────────────
async function confirmDelete(rec) {
  const confirmed = window.confirm(
    `Are you sure you want to delete "${rec.name}" (Roll: ${rec.roll || "—"})?\n\nThis will permanently remove the student from the database.`
  );
  if (!confirmed) return;

  try {
    const res  = await fetch("/delete_student", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ name: rec.name, roll: rec.roll }),
    });
    const data = await res.json();
    if (data.status === "ok") {
      // Refresh list
      await loadAllStudents();
      // Refresh header stats
      allNames = await (await fetch("/students")).json();
      const stats = await (await fetch("/stats")).json();
      document.getElementById("stat-students").innerHTML =
        `<span class="dot"></span>${stats.total} Students`;
      const distRow = document.getElementById("dist-row");
      distRow.innerHTML = "";
      const dist = stats.distribution;
      [["Good","good"],["Average","average"],["Bad","bad"],["Fail","fail"]].forEach(([cat, cls]) => {
        const pill = document.createElement("div");
        pill.className = `dist-pill ${cls}`;
        pill.innerHTML = `<span class="dist-count">${dist[cat]}</span> ${cat}`;
        distRow.appendChild(pill);
      });
    } else {
      alert(data.message || "Delete failed.");
    }
  } catch (err) {
    alert("Network error — is the server running?");
  }
}

// ═══════════════════════════════════════════════
//  EDIT STUDENT MODAL
// ═══════════════════════════════════════════════

const SUBJECTS_EDIT = ["Maths", "English", "Science", "Kannada", "Hindi"];

document.getElementById("edit-modal-close").addEventListener("click", closeEditModal);
document.getElementById("edit-modal").addEventListener("click", e => {
  if (e.target === document.getElementById("edit-modal")) closeEditModal();
});

function openEditModal(rec) {
  editOriginalName = rec.name;
  editOriginalRoll = rec.roll;
  editCurrentStep  = 1;

  // Populate fields
  document.getElementById("ef-name").value       = rec.name;
  document.getElementById("ef-roll").value       = rec.roll || "";
  document.getElementById("ef-attendance").value = rec.attendance;

  SUBJECTS_EDIT.forEach(s => {
    document.getElementById(`ea-${s}`).value = rec[`assign_${s}`] ?? "";
    document.getElementById(`ei-${s}`).value = rec[`internal_${s}`] ?? "";
    document.getElementById(`ee-${s}`).value = rec[`exam_${s}`] ?? "";
  });

  hideEditMsg();
  goToEditStep(1);
  document.getElementById("edit-modal").classList.remove("hidden");
}

function closeEditModal() {
  document.getElementById("edit-modal").classList.add("hidden");
}

function goToEditStep(step) {
  editCurrentStep = step;
  document.getElementById("edit-step-1").classList.toggle("active", step === 1);
  document.getElementById("edit-step-2").classList.toggle("active", step === 2);
  const dot1 = document.getElementById("esdot-1");
  const dot2 = document.getElementById("esdot-2");
  dot1.className = "step-dot " + (step === 1 ? "active" : "done");
  dot2.className = "step-dot " + (step === 2 ? "active" : "");
  const backBtn = document.getElementById("edit-modal-back-btn");
  const nextBtn = document.getElementById("edit-modal-next-btn");
  backBtn.style.visibility = step === 1 ? "hidden" : "visible";
  nextBtn.textContent = step === 1 ? "Next →" : "Save Changes";
}

document.getElementById("edit-modal-back-btn").addEventListener("click", () => {
  hideEditMsg();
  goToEditStep(1);
});

document.getElementById("edit-modal-next-btn").addEventListener("click", () => {
  hideEditMsg();
  if (editCurrentStep === 1) {
    if (validateEditStep1()) goToEditStep(2);
  } else {
    if (validateEditStep2()) submitEdit();
  }
});

function validateEditStep1() {
  const name = document.getElementById("ef-name").value.trim();
  const att  = parseFloat(document.getElementById("ef-attendance").value);
  if (!name) { showEditError("Please enter the student name."); return false; }
  if (isNaN(att) || att < 0 || att > 100) {
    showEditError("Attendance must be a number between 0 and 100."); return false;
  }
  return true;
}

function validateEditStep2() {
  for (const s of SUBJECTS_EDIT) {
    const a = parseFloat(document.getElementById(`ea-${s}`).value);
    const i = parseFloat(document.getElementById(`ei-${s}`).value);
    const e = parseFloat(document.getElementById(`ee-${s}`).value);
    if (isNaN(a) || a < 0 || a > 25)  { showEditError(`${s}: Assignment must be 0–25.`);  return false; }
    if (isNaN(i) || i < 0 || i > 50)  { showEditError(`${s}: Internal must be 0–50.`);    return false; }
    if (isNaN(e) || e < 0 || e > 100) { showEditError(`${s}: Exam must be 0–100.`);        return false; }
  }
  return true;
}

async function submitEdit() {
  const nextBtn = document.getElementById("edit-modal-next-btn");
  nextBtn.disabled    = true;
  nextBtn.textContent = "Saving…";

  const payload = {
    original_name: editOriginalName,
    original_roll: editOriginalRoll,
    name:          document.getElementById("ef-name").value.trim(),
    roll:          document.getElementById("ef-roll").value.trim(),
    attendance:    parseFloat(document.getElementById("ef-attendance").value),
  };
  SUBJECTS_EDIT.forEach(s => {
    payload[`assign_${s}`]   = parseFloat(document.getElementById(`ea-${s}`).value);
    payload[`internal_${s}`] = parseFloat(document.getElementById(`ei-${s}`).value);
    payload[`exam_${s}`]     = parseFloat(document.getElementById(`ee-${s}`).value);
  });

  try {
    const res  = await fetch("/edit_student", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.status === "ok") {
      showEditSuccess(`✔ ${data.message}  Performance: ${data.performance}`);
      // Reload manage list
      await loadAllStudents();
      allNames = await (await fetch("/students")).json();
      const stats = await (await fetch("/stats")).json();
      document.getElementById("stat-students").innerHTML =
        `<span class="dot"></span>${stats.total} Students`;
      setTimeout(() => { closeEditModal(); }, 1800);
    } else {
      showEditError(data.message || "Update failed.");
    }
  } catch (err) {
    showEditError("Network error — is the server running?");
  } finally {
    nextBtn.disabled    = false;
    nextBtn.textContent = "Save Changes";
  }
}

function showEditError(msg) {
  document.getElementById("edit-modal-error").textContent = msg;
  document.getElementById("edit-modal-error").classList.remove("hidden");
  document.getElementById("edit-modal-success").classList.add("hidden");
}
function showEditSuccess(msg) {
  document.getElementById("edit-modal-success").textContent = msg;
  document.getElementById("edit-modal-success").classList.remove("hidden");
  document.getElementById("edit-modal-error").classList.add("hidden");
}
function hideEditMsg() {
  document.getElementById("edit-modal-error").classList.add("hidden");
  document.getElementById("edit-modal-success").classList.add("hidden");
}
