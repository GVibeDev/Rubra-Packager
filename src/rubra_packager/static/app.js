"use strict";

const token = window.RP_SESSION_TOKEN;
const state = { projects: [], profiles: [], selectedProjectId: null };

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(`/api/${path}`, {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      "X-RP-Token": token,
      ...(options.headers || {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  let payload;
  try { payload = await response.json(); }
  catch { payload = { success: false, error: `Invalid response (${response.status})` }; }
  if (!response.ok || payload.success === false) {
    const error = new Error(payload.error || `Request failed (${response.status})`);
    error.payload = payload;
    throw error;
  }
  return payload;
}

function showToast(message, isError = false) {
  const toast = $("toast");
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.remove("hidden");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.add("hidden"), 4200);
}

function setBusy(active, text = "Working…") {
  $("busyText").textContent = text;
  $("busyLayer").classList.toggle("hidden", !active);
}

function switchView(view) {
  document.querySelectorAll(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
  document.querySelectorAll(".view").forEach((section) => section.classList.toggle("active", section.id === `view-${view}`));
  const labels = {
    projects: "Projects",
    preflight: "Web Preflight",
    windows: "Web → Windows",
    python: "Python → Windows",
    setup: "Setup Builder",
    android: "Android",
    about: "About",
  };
  $("pageTitle").textContent = labels[view] || "Rubra Packager";
}

function projectById(id) { return state.projects.find((item) => item.project_id === id); }
function profileById(id) { return state.profiles.find((item) => item.id === id); }

function fillSelect(select, items, getValue, getLabel, preferred) {
  const current = preferred ?? select.value;
  select.innerHTML = "";
  for (const item of items) {
    const option = document.createElement("option");
    option.value = getValue(item);
    option.textContent = getLabel(item);
    select.append(option);
  }
  if ([...select.options].some((option) => option.value === current)) select.value = current;
}

function fillVariants(profileSelect, variantSelect, preferred) {
  const profile = profileById(profileSelect.value);
  const variants = profile?.variants || [];
  fillSelect(variantSelect, variants, (item) => item.variant_id, (item) => `${item.label} — ${item.description}`, preferred || profile?.defaultVariant);
}

function syncProjectSelection(select, nameInput, profileSelect, variantSelect) {
  const project = projectById(select.value);
  if (!project) return;
  if (nameInput) nameInput.value = project.name;
  if (profileSelect) {
    profileSelect.value = project.profile_id;
    fillVariants(profileSelect, variantSelect, profileById(project.profile_id)?.defaultVariant);
  }
}

function renderProjects() {
  $("projectCount").textContent = String(state.projects.length);
  const grid = $("projectGrid");
  grid.innerHTML = "";
  $("emptyProjects").classList.toggle("hidden", state.projects.length > 0);
  for (const project of state.projects) {
    const card = document.createElement("article");
    card.className = "project-card";
    const availability = project.sourceExists ? '<span class="pill">Source ready</span>' : '<span class="pill offline">Source missing</span>';
    card.innerHTML = `
      <h3>${escapeHtml(project.name)}</h3>
      <p>${escapeHtml(project.description || project.source_path)}</p>
      <div class="project-meta">
        <span class="pill">${escapeHtml(project.profile_id)}</span>
        <span class="pill">v${escapeHtml(project.version)}</span>
        ${availability}
      </div>
      <div class="project-actions">
        <button class="button gold small" data-build="${escapeAttr(project.project_id)}">Build</button>
        <button class="button ghost small" data-preflight="${escapeAttr(project.project_id)}">Inspect</button>
        <button class="button danger small" data-delete="${escapeAttr(project.project_id)}">Remove</button>
      </div>`;
    grid.append(card);
  }
  refreshProjectSelects();
}

function refreshProjectSelects() {
  const selects = [$("preflightProject"), $("windowsProject"), $("androidProject")];
  for (const select of selects) fillSelect(select, state.projects, (item) => item.project_id, (item) => item.name, state.selectedProjectId);
  if (!state.selectedProjectId && state.projects[0]) state.selectedProjectId = state.projects[0].project_id;
  for (const select of selects) if (state.selectedProjectId) select.value = state.selectedProjectId;
  syncProjectSelection($("preflightProject"), null, $("preflightProfile"), $("preflightVariant"));
  syncProjectSelection($("windowsProject"), $("windowsName"), $("windowsProfile"), $("windowsVariant"));
  syncProjectSelection($("androidProject"), $("androidName"), $("androidProfile"), $("androidVariant"));
}

function refreshProfileSelects() {
  const selects = [$("projectProfile"), $("preflightProfile"), $("windowsProfile"), $("androidProfile")];
  for (const select of selects) fillSelect(select, state.profiles, (item) => item.id, (item) => item.label);
  for (const [profileSelect, variantSelect] of [
    [$("preflightProfile"), $("preflightVariant")],
    [$("windowsProfile"), $("windowsVariant")],
    [$("androidProfile"), $("androidVariant")],
  ]) fillVariants(profileSelect, variantSelect);
}

async function loadState() {
  const [health, projects, profiles] = await Promise.all([api("health"), api("projects"), api("profiles")]);
  state.projects = projects.projects;
  state.profiles = profiles.profiles;
  $("connectionDot").classList.add("online");
  $("connectionText").textContent = `Ready · v${health.version}`;
  refreshProfileSelects();
  renderProjects();
}

function renderPreflight(report) {
  const badge = $("preflightBadge");
  badge.className = `badge ${report.errors ? "error" : report.warnings ? "warning" : "success"}`;
  badge.textContent = report.errors ? `${report.errors} errors` : report.warnings ? `${report.warnings} warnings` : "Passed";
  const cards = [
    [report.scanned_files, "scanned"],
    [report.included_files, "included"],
    [report.excluded_files, "excluded"],
    [`${(report.included_bytes / 1048576).toFixed(1)} MB`, "package size"],
  ];
  $("preflightSummary").innerHTML = cards.map(([value, label]) => `<div class="summary-card"><strong>${value}</strong><span>${label}</span></div>`).join("");
  const list = $("findingList");
  if (!report.findings.length) {
    list.innerHTML = '<div class="finding info"><strong>NO FINDINGS</strong><p>The selected package passed all current checks.</p></div>';
    return;
  }
  list.innerHTML = report.findings.map((item) => `
    <div class="finding ${escapeAttr(item.severity)}">
      <strong>${escapeHtml(item.severity.toUpperCase())} · ${escapeHtml(item.code)}</strong>
      <p>${escapeHtml(item.message)}${item.path ? `<br><span>${escapeHtml(item.path)}</span>` : ""}</p>
    </div>`).join("");
}

async function runPreflight() {
  setBusy(true, "Inspecting web package…");
  try {
    const payload = await api("preflight", { method: "POST", body: {
      projectId: $("preflightProject").value,
      profileId: $("preflightProfile").value,
      variantId: $("preflightVariant").value,
    }});
    renderPreflight(payload.report);
    showToast(payload.report.ok ? "Web preflight completed" : "Web preflight found blocking errors", !payload.report.ok);
  } catch (error) { showToast(error.message, true); }
  finally { setBusy(false); }
}

async function fileToDataUri(input) {
  const file = input.files?.[0];
  if (!file) return null;
  return await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error || new Error("Could not read icon"));
    reader.readAsDataURL(file);
  });
}

function resultLog(result) {
  const lines = [...(result.log || [])];
  if (result.success) {
    lines.push("", "=== PUBLISHED ===", `Path: ${result.path}`, `Size: ${(result.bytes / 1048576).toFixed(2)} MB`, `SHA-256: ${result.sha256}`);
    if (result.bundlePath) lines.push(`Bundle: ${result.bundlePath}`);
    if (result.scriptPath) lines.push(`Inno script: ${result.scriptPath}`);
    if (result.signature) lines.push(`Signature: ${result.signature}`);
    if (result.releaseManifestPath) lines.push(`Release manifest: ${result.releaseManifestPath}`);
  } else if (result.error) lines.push("", `ERROR: ${result.error}`);
  return lines.join("\n");
}

async function buildWindows() {
  setBusy(true, "Building Windows executable…");
  $("windowsLog").textContent = "Build started. This may take several minutes.";
  try {
    const result = await api("build/windows", { method: "POST", body: {
      projectId: $("windowsProject").value,
      appName: $("windowsName").value,
      profileId: $("windowsProfile").value,
      variantId: $("windowsVariant").value,
      allowSourceBuild: $("windowsTrust").checked,
      iconData: await fileToDataUri($("windowsIcon")),
    }});
    $("windowsLog").textContent = resultLog(result);
    showToast("Windows executable published");
  } catch (error) {
    $("windowsLog").textContent = error.payload ? resultLog(error.payload) : `${$("windowsLog").textContent}\n\nERROR: ${error.message}`;
    showToast(error.message, true);
  }
  finally { setBusy(false); }
}

function listFromText(value, allowCommas = false) {
  const pattern = allowCommas ? /[\n,]+/ : /\n+/;
  const seen = new Set();
  const result = [];
  for (const raw of String(value || "").split(pattern)) {
    const item = raw.trim();
    if (item && !seen.has(item)) {
      seen.add(item);
      result.push(item);
    }
  }
  return result;
}

function pythonRequestBody() {
  return {
    projectRoot: $("pythonRoot").value.trim(),
    entryPoint: $("pythonEntry").value.trim(),
    appName: $("pythonName").value.trim(),
    version: $("pythonVersion").value.trim(),
    publisher: $("pythonPublisher").value.trim(),
    description: $("pythonDescription").value.trim(),
    bundleMode: $("pythonBundleMode").value,
    windowMode: $("pythonWindowMode").value,
    dependencyMode: $("pythonDependencyMode").value,
    trustDependencyInstall: $("pythonTrust").checked,
    hiddenImports: listFromText($("pythonHiddenImports").value, true),
    dataPaths: listFromText($("pythonDataPaths").value),
    searchPaths: listFromText($("pythonSearchPaths").value),
  };
}

function pythonPreflightLog(report, reportPath = "") {
  const lines = [
    "=== PYTHON PREFLIGHT ===",
    `Project: ${report.project_root}`,
    `Entry point: ${report.entry_point || "(not resolved)"}`,
    `Python: ${report.python_version}`,
    `PyInstaller: ${report.pyinstaller_available ? "available" : "missing"}`,
    `Dependency mode: ${report.dependency_mode}`,
    `Dependency files: ${(report.dependency_files || []).join(", ") || "none"}`,
    `Hidden imports: ${(report.hidden_imports || []).join(", ") || "none"}`,
    `Additional data: ${(report.data_paths || []).join(", ") || "none"}`,
    `Search paths: ${(report.search_paths || []).join(", ") || "none"}`,
    `Errors: ${report.errors}`,
    `Warnings: ${report.warnings}`,
  ];
  if (reportPath) lines.push(`Report: ${reportPath}`);
  if (report.findings?.length) {
    lines.push("", "=== FINDINGS ===");
    for (const item of report.findings) {
      lines.push(`${item.severity.toUpperCase()} · ${item.code} · ${item.message}${item.path ? ` [${item.path}]` : ""}`);
    }
  } else {
    lines.push("", "No findings.");
  }
  return lines.join("\n");
}


function renderPrerequisites(containerId, entries) {
  const container = $(containerId);
  const normalized = entries.map(([label, value]) => [label, value || { ok: false, message: "Not detected" }]);
  const shouldStack = normalized.some(([, value]) => String(value.message || "").trim().length > 64);
  container.classList.toggle("stacked", shouldStack);
  container.innerHTML = normalized.map(([label, value]) =>
    `<div class="prereq ${value.ok ? "ok" : ""}"><strong>${escapeHtml(label)}</strong><span class="prereq-message">${escapeHtml(value.message || "Not detected")}</span></div>`
  ).join("");
}

async function checkPython() {
  try {
    const payload = await api("python/prerequisites");
    const values = payload.prerequisites;
    renderPrerequisites("pythonPrereqs", [
      ["PYTHON", values.python],
      ["PYINSTALLER", values.pyinstaller],
    ]);
  } catch (error) { showToast(error.message, true); }
}

async function browsePythonRoot() {
  try {
    const payload = await api("dialog/folder", { method: "POST", body: {} });
    if (!payload.path) return;
    $("pythonRoot").value = payload.path;
    const name = payload.path.replace(/[\\/]+$/, "").split(/[\\/]/).pop() || "python-app";
    if (!$("pythonName").value.trim()) $("pythonName").value = name;
    try {
      const inspection = await api("python/inspect", { method: "POST", body: { projectRoot: payload.path } });
      const entries = inspection.inspection.suggestedEntryPoints || [];
      if (!$("pythonEntry").value.trim() && entries.length) $("pythonEntry").value = entries[0];
    } catch (error) {
      showToast(error.message, true);
    }
  } catch (error) { showToast(error.message, true); }
}

async function browsePythonEntry() {
  if (!$("pythonRoot").value.trim()) {
    showToast("Choose the Python project folder first", true);
    return;
  }
  try {
    const payload = await api("dialog/python-entry", { method: "POST", body: { projectRoot: $("pythonRoot").value.trim() } });
    if (payload.path) $("pythonEntry").value = payload.path;
  } catch (error) { showToast(error.message, true); }
}

async function runPythonPreflight() {
  setBusy(true, "Inspecting Python project…");
  $("pythonLog").textContent = "Python preflight started.";
  try {
    const result = await api("python/preflight", { method: "POST", body: pythonRequestBody() });
    if (!$("pythonEntry").value.trim() && result.report.entry_point) $("pythonEntry").value = result.report.entry_point;
    $("pythonLog").textContent = pythonPreflightLog(result.report, result.reportPath);
    showToast(result.report.ok ? "Python preflight completed" : "Python preflight found blocking errors", !result.report.ok);
  } catch (error) {
    $("pythonLog").textContent += `\n\nERROR: ${error.message}`;
    showToast(error.message, true);
  }
  finally { setBusy(false); }
}

async function buildPython() {
  setBusy(true, "Building Python executable…");
  $("pythonLog").textContent = "Python build started. Dependency staging and PyInstaller may take several minutes.";
  try {
    const body = pythonRequestBody();
    body.iconData = await fileToDataUri($("pythonIcon"));
    const result = await api("build/python", { method: "POST", body });
    $("pythonLog").textContent = resultLog(result);
    showToast("Python executable published");
  } catch (error) {
    $("pythonLog").textContent = error.payload ? resultLog(error.payload) : `${$("pythonLog").textContent}\n\nERROR: ${error.message}`;
    showToast(error.message, true);
  }
  finally { setBusy(false); }
}

async function checkSetup() {
  try {
    const payload = await api("setup/prerequisites");
    const values = payload.prerequisites;
    renderPrerequisites("setupPrereqs", [
      ["INNO SETUP", values.inno],
      ["WINGET", values.winget],
    ]);
    $("installSetupPrereqButton").disabled = Boolean(values.inno.ok || !values.bootstrapSupported);
    $("installSetupPrereqButton").textContent = values.inno.ok ? "Inno Setup ready" : "Install Inno Setup";
  } catch (error) { showToast(error.message, true); }
}

async function installSetupPrerequisite() {
  if (!confirm("Install Inno Setup using Windows Package Manager (winget)? This runs an external installer on your computer.")) return;
  setBusy(true, "Installing Inno Setup…");
  try {
    const result = await api("setup/bootstrap", { method: "POST", body: { scope: $("setupBootstrapScope").value } });
    $("setupLog").textContent = (result.log || []).join("\n") || `Inno Setup ready: ${result.path || "detected"}`;
    showToast(result.alreadyInstalled ? "Inno Setup already installed" : "Inno Setup installed");
    await checkSetup();
  } catch (error) {
    $("setupLog").textContent = error.payload ? resultLog(error.payload) : `ERROR: ${error.message}`;
    showToast(error.message, true);
  }
  finally { setBusy(false); }
}

function setupSlug(value) {
  return String(value || "application").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "application";
}

function syncSetupDerivedFields(sourcePath) {
  const clean = String(sourcePath || "").replace(/[\\/]+$/, "");
  const leaf = clean.split(/[\\/]/).pop() || "Application";
  const kind = $("setupArtifactKind").value;
  const base = kind === "onefile" ? leaf.replace(/\.exe$/i, "") : leaf;
  if (!$("setupName").value.trim()) $("setupName").value = base;
  if (!$("setupInstallDirName").value.trim()) $("setupInstallDirName").value = base;
  if (!$("setupAppId").value.trim()) $("setupAppId").value = `com.example.${setupSlug(base).replace(/-/g, ".")}`;
  if (kind === "onefile") $("setupPrimaryExe").value = leaf;
}

async function browseSetupSource() {
  try {
    const kind = $("setupArtifactKind").value;
    const payload = kind === "onefile"
      ? await api("dialog/file", { method: "POST", body: { purpose: "setup-exe" } })
      : await api("dialog/folder", { method: "POST", body: {} });
    if (!payload.path) return;
    $("setupSource").value = payload.path;
    syncSetupDerivedFields(payload.path);
  } catch (error) { showToast(error.message, true); }
}

async function browseSetupMetadata(targetId, purpose) {
  try {
    const payload = await api("dialog/file", { method: "POST", body: { purpose } });
    if (payload.path) $(targetId).value = payload.path;
  } catch (error) { showToast(error.message, true); }
}

function setupRequestBody() {
  return {
    sourcePath: $("setupSource").value.trim(),
    artifactKind: $("setupArtifactKind").value,
    primaryExe: $("setupPrimaryExe").value.trim(),
    appName: $("setupName").value.trim(),
    version: $("setupVersion").value.trim(),
    publisher: $("setupPublisher").value.trim(),
    appId: $("setupAppId").value.trim(),
    installMode: $("setupInstallMode").value,
    installDirName: $("setupInstallDirName").value.trim(),
    desktopShortcut: $("setupDesktop").checked,
    startMenuShortcut: $("setupStartMenu").checked,
    launchAfterInstall: $("setupLaunchAfter").checked,
    licenseFile: $("setupLicense").value.trim(),
    releaseNotesFile: $("setupReleaseNotes").value.trim(),
  };
}

async function buildSetup() {
  setBusy(true, "Building Windows setup…");
  $("setupLog").textContent = "Setup build started. Inno Setup will compile the generated .iss file.";
  try {
    const body = setupRequestBody();
    body.iconData = await fileToDataUri($("setupIcon"));
    const result = await api("build/setup", { method: "POST", body });
    $("setupLog").textContent = resultLog(result);
    showToast("Windows setup published");
  } catch (error) {
    $("setupLog").textContent = error.payload ? resultLog(error.payload) : `${$("setupLog").textContent}\n\nERROR: ${error.message}`;
    showToast(error.message, true);
  }
  finally { setBusy(false); }
}

async function checkAndroid() {
  try {
    const payload = await api("android/prerequisites");
    const values = payload.prerequisites;
    renderPrerequisites("androidPrereqs", [
      ["JAVA", values.java],
      ["SDK", values.sdk],
      ["NODE", values.node],
    ]);
  } catch (error) { showToast(error.message, true); }
}

async function buildAndroid() {
  setBusy(true, "Building Android APK…");
  $("androidLog").textContent = "Build started. Gradle may take several minutes.";
  try {
    const result = await api("build/android", { method: "POST", body: {
      projectId: $("androidProject").value,
      appName: $("androidName").value,
      packageName: $("androidPackage").value,
      profileId: $("androidProfile").value,
      variantId: $("androidVariant").value,
      allowSourceBuild: $("androidTrust").checked,
      iconData: await fileToDataUri($("androidIcon")),
      iconBackground: $("androidBackground").value,
    }});
    $("androidLog").textContent = resultLog(result);
    showToast("Android APK published");
  } catch (error) {
    $("androidLog").textContent = error.payload ? resultLog(error.payload) : `${$("androidLog").textContent}\n\nERROR: ${error.message}`;
    showToast(error.message, true);
  }
  finally { setBusy(false); }
}

async function openProjectDialog() {
  $("projectForm").reset();
  $("projectVersion").value = "1.0.0";
  $("projectDialog").showModal();
}

async function browseSource() {
  try {
    const payload = await api("dialog/folder", { method: "POST", body: {} });
    if (!payload.path) return;
    $("projectSource").value = payload.path;
    const name = payload.path.replace(/[\\/]+$/, "").split(/[\\/]/).pop() || "web-project";
    $("projectName").value = name;
    $("projectId").value = name.toLowerCase().replace(/[^a-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "");
    if (name.toLowerCase().includes("arena") && name.toLowerCase().includes("rubra")) $("projectProfile").value = "arena-rubra";
  } catch (error) { showToast(error.message, true); }
}

async function saveProject() {
  setBusy(true, "Registering project…");
  try {
    await api("projects/import", { method: "POST", body: {
      sourcePath: $("projectSource").value,
      projectId: $("projectId").value,
      name: $("projectName").value,
      profileId: $("projectProfile").value,
      author: $("projectAuthor").value,
      version: $("projectVersion").value,
      description: $("projectDescription").value,
    }});
    $("projectDialog").close();
    await loadState();
    showToast("Project registered");
  } catch (error) { showToast(error.message, true); }
  finally { setBusy(false); }
}

async function importLegacy() {
  setBusy(true, "Importing legacy project records…");
  try {
    const payload = await api("projects/import-legacy", { method: "POST", body: {} });
    await loadState();
    showToast(`${payload.imported} legacy projects imported`);
  } catch (error) { showToast(error.message, true); }
  finally { setBusy(false); }
}

async function deleteProject(id) {
  const project = projectById(id);
  if (!project || !confirm(`Remove ${project.name} from Rubra Packager? The source folder will not be deleted.`)) return;
  try {
    await api("projects/delete", { method: "POST", body: { projectId: id } });
    state.selectedProjectId = null;
    await loadState();
    showToast("Project removed");
  } catch (error) { showToast(error.message, true); }
}

function selectProjectAndView(id, view) {
  state.selectedProjectId = id;
  refreshProjectSelects();
  switchView(view);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}
function escapeAttr(value) { return escapeHtml(value); }

function wireEvents() {
  document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.view)));
  $("newProjectButton").addEventListener("click", openProjectDialog);
  $("legacyImportButton").addEventListener("click", importLegacy);
  $("browseSourceButton").addEventListener("click", browseSource);
  $("saveProjectButton").addEventListener("click", saveProject);
  $("runPreflightButton").addEventListener("click", runPreflight);
  $("buildWindowsButton").addEventListener("click", buildWindows);
  $("checkPythonButton").addEventListener("click", checkPython);
  $("browsePythonRootButton").addEventListener("click", browsePythonRoot);
  $("browsePythonEntryButton").addEventListener("click", browsePythonEntry);
  $("runPythonPreflightButton").addEventListener("click", runPythonPreflight);
  $("buildPythonButton").addEventListener("click", buildPython);
  $("checkSetupButton").addEventListener("click", checkSetup);
  $("installSetupPrereqButton").addEventListener("click", installSetupPrerequisite);
  $("browseSetupSourceButton").addEventListener("click", browseSetupSource);
  $("browseSetupLicenseButton").addEventListener("click", () => browseSetupMetadata("setupLicense", "license"));
  $("browseSetupNotesButton").addEventListener("click", () => browseSetupMetadata("setupReleaseNotes", "release-notes"));
  $("buildSetupButton").addEventListener("click", buildSetup);
  $("setupArtifactKind").addEventListener("change", () => { $("setupSource").value = ""; $("setupPrimaryExe").value = ""; });
  $("checkAndroidButton").addEventListener("click", checkAndroid);
  $("buildAndroidButton").addEventListener("click", buildAndroid);

  for (const [projectSelect, nameInput, profileSelect, variantSelect] of [
    [$("preflightProject"), null, $("preflightProfile"), $("preflightVariant")],
    [$("windowsProject"), $("windowsName"), $("windowsProfile"), $("windowsVariant")],
    [$("androidProject"), $("androidName"), $("androidProfile"), $("androidVariant")],
  ]) projectSelect.addEventListener("change", () => {
    state.selectedProjectId = projectSelect.value;
    syncProjectSelection(projectSelect, nameInput, profileSelect, variantSelect);
  });

  for (const [profileSelect, variantSelect] of [
    [$("preflightProfile"), $("preflightVariant")],
    [$("windowsProfile"), $("windowsVariant")],
    [$("androidProfile"), $("androidVariant")],
  ]) profileSelect.addEventListener("change", () => fillVariants(profileSelect, variantSelect));

  document.querySelectorAll("[data-clear]").forEach((button) => button.addEventListener("click", () => $(button.dataset.clear).textContent = ""));
  $("projectGrid").addEventListener("click", (event) => {
    const target = event.target.closest("button");
    if (!target) return;
    if (target.dataset.build) selectProjectAndView(target.dataset.build, "windows");
    if (target.dataset.preflight) selectProjectAndView(target.dataset.preflight, "preflight");
    if (target.dataset.delete) deleteProject(target.dataset.delete);
  });
}

async function boot() {
  wireEvents();
  try {
    await loadState();
    await Promise.all([checkPython(), checkSetup(), checkAndroid()]);
  } catch (error) {
    $("connectionText").textContent = "Connection failed";
    showToast(error.message, true);
  }
}

boot();
