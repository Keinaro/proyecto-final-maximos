/**
 * Clínica Veterinaria Máximos · Frontend (P3)
 *
 * Regla técnica obligatoria (E6 / 03-frontend.md):
 * Todas las peticiones usan exclusivamente rutas relativas (/api/...).
 * Nginx actúa como proxy inverso resolviendo los Services por DNS interno:
 *   /api/pacientes   -> http://pacientes:8080/pacientes
 *   /api/citas       -> http://citas:8080/citas
 *   /api/integrantes -> http://pacientes:8080/integrantes
 */

const API_ROUTES = {
  pacientes: "/api/pacientes",
  citas: "/api/citas",
  integrantes: "/api/integrantes",
  healthPacientes: "/api/health/pacientes",
  healthCitas: "/api/health/citas",
};

const STORAGE_KEYS = {
  forceMock: "vet_maximos_force_mock",
  mockData: "vet_maximos_mock_db_v1",
};

// Datos semilla de respaldo que respetan el Contrato 3.3 y 3.4 mientras P1/P2 levantan sus servicios
const INITIAL_MOCK_DB = {
  integrantes: [
    { id: 1, nombre: "Integrante 1 (P1 · Pacientes)", carne: "1000122" },
    { id: 2, nombre: "Integrante 2 (P2 · Citas)", carne: "1000222" },
    { id: 3, nombre: "Sofía (P3 · Frontend)", carne: "1000322" },
    { id: 4, nombre: "Integrante 4 (P4 · BD y Config)", carne: "1000422" },
    { id: 5, nombre: "Integrante 5 (P5 · Terraform)", carne: "1000522" },
    { id: 6, nombre: "Integrante 6 (P6 · Kubernetes)", carne: "1000622" },
  ],
  pacientes: [
    {
      id: 1,
      nombre: "Max",
      especie: "Perro",
      raza: "Golden Retriever",
      fecha_nacimiento: "2022-04-15",
      propietario_nombre: "Carlos Méndez",
      propietario_telefono: "5512-3489",
    },
    {
      id: 2,
      nombre: "Luna",
      especie: "Gato",
      raza: "Siamés",
      fecha_nacimiento: "2023-08-10",
      propietario_nombre: "María Fernanda Gómez",
      propietario_telefono: "4489-9012",
    },
    {
      id: 3,
      nombre: "Rocky",
      especie: "Perro",
      raza: "Bulldog Francés",
      fecha_nacimiento: "2021-11-02",
      propietario_nombre: "Jorge Castillo",
      propietario_telefono: "3301-7745",
    },
  ],
  citas: [
    {
      id: 1,
      paciente_id: 1,
      fecha_hora: "2026-11-10T09:30:00",
      motivo: "Vacunación anual polivalente y chequeo general",
      veterinario: "Dra. Sofía Morales",
      estado: "programada",
    },
    {
      id: 2,
      paciente_id: 2,
      fecha_hora: "2026-11-10T11:00:00",
      motivo: "Control dermatológico y limpieza dental",
      veterinario: "Dr. Alejandro Reyes",
      estado: "programada",
    },
    {
      id: 3,
      paciente_id: 1,
      fecha_hora: "2026-11-01T15:00:00",
      motivo: "Desparasitación interna trimestral",
      veterinario: "Dra. Sofía Morales",
      estado: "completada",
    },
  ],
  nextPacienteId: 4,
  nextCitaId: 4,
};

const state = {
  pacientes: [],
  citas: [],
  integrantes: [],
  usingMock: false,
  forceMock: localStorage.getItem(STORAGE_KEYS.forceMock) === "true",
  searchPacientes: "",
  filterPacienteId: "",
  filterEstado: "",
};

/* ==========================================================================
   Motor de Simulación Local (Contrato 3.4: 200, 201, 204, 400, 404, 409)
   ========================================================================== */
function loadMockDb() {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.mockData);
    if (raw) return JSON.parse(raw);
  } catch (_) {
    // ignore storage errors
  }
  const clone = JSON.parse(JSON.stringify(INITIAL_MOCK_DB));
  saveMockDb(clone);
  return clone;
}

function saveMockDb(db) {
  try {
    localStorage.setItem(STORAGE_KEYS.mockData, JSON.stringify(db));
  } catch (_) {
    // ignore storage errors
  }
}

function resetMockDb() {
  const clone = JSON.parse(JSON.stringify(INITIAL_MOCK_DB));
  saveMockDb(clone);
  return clone;
}

function createHttpError(status, message) {
  const err = new Error(message);
  err.status = status;
  return err;
}

async function mockApiRequest(method, url, body = null) {
  const db = loadMockDb();
  const parsedUrl = new URL(url, window.location.origin);
  const path = parsedUrl.pathname;

  // Health endpoints
  if (path === API_ROUTES.healthPacientes || path === API_ROUTES.healthCitas) {
    return { status: "ok", version: "1.0.0-sim" };
  }

  // GET /api/integrantes
  if (path === API_ROUTES.integrantes && method === "GET") {
    return db.integrantes;
  }

  // /api/pacientes
  if (path === API_ROUTES.pacientes) {
    if (method === "GET") {
      return db.pacientes;
    }
    if (method === "POST") {
      if (!body || !body.nombre || !body.especie || !body.propietario_nombre) {
        throw createHttpError(400, "Los campos nombre, especie y propietario_nombre son obligatorios");
      }
      const nuevo = {
        id: db.nextPacienteId++,
        nombre: String(body.nombre).trim(),
        especie: String(body.especie).trim(),
        raza: body.raza ? String(body.raza).trim() : null,
        fecha_nacimiento: body.fecha_nacimiento || null,
        propietario_nombre: String(body.propietario_nombre).trim(),
        propietario_telefono: body.propietario_telefono ? String(body.propietario_telefono).trim() : null,
      };
      db.pacientes.push(nuevo);
      saveMockDb(db);
      return nuevo;
    }
  }

  // /api/pacientes/{id}
  const matchPaciente = path.match(/^\/api\/pacientes\/(\d+)$/);
  if (matchPaciente) {
    const id = Number(matchPaciente[1]);
    const idx = db.pacientes.findIndex((p) => Number(p.id) === id);
    if (idx === -1) {
      throw createHttpError(404, `Paciente con id ${id} no encontrado`);
    }

    if (method === "GET") {
      return db.pacientes[idx];
    }
    if (method === "PUT") {
      if (!body || !body.nombre || !body.especie || !body.propietario_nombre) {
        throw createHttpError(400, "Los campos nombre, especie y propietario_nombre son obligatorios");
      }
      db.pacientes[idx] = {
        ...db.pacientes[idx],
        nombre: String(body.nombre).trim(),
        especie: String(body.especie).trim(),
        raza: body.raza ? String(body.raza).trim() : null,
        fecha_nacimiento: body.fecha_nacimiento || null,
        propietario_nombre: String(body.propietario_nombre).trim(),
        propietario_telefono: body.propietario_telefono ? String(body.propietario_telefono).trim() : null,
      };
      saveMockDb(db);
      return db.pacientes[idx];
    }
    if (method === "DELETE") {
      const tieneCitas = db.citas.some((c) => Number(c.paciente_id) === id);
      if (tieneCitas) {
        throw createHttpError(
          409,
          "No se puede eliminar el paciente porque tiene citas registradas (ON DELETE RESTRICT)"
        );
      }
      db.pacientes.splice(idx, 1);
      saveMockDb(db);
      return null;
    }
  }

  // /api/citas
  if (path === API_ROUTES.citas) {
    if (method === "GET") {
      const pacienteIdParam = parsedUrl.searchParams.get("paciente_id");
      if (pacienteIdParam) {
        return db.citas.filter((c) => Number(c.paciente_id) === Number(pacienteIdParam));
      }
      return db.citas;
    }
    if (method === "POST") {
      const pacienteId = Number(body?.paciente_id);
      const existePaciente = db.pacientes.some((p) => Number(p.id) === pacienteId);
      if (!existePaciente) {
        throw createHttpError(400, "paciente no existe");
      }
      const estadosValidos = ["programada", "completada", "cancelada"];
      const estado = body?.estado || "programada";
      if (!estadosValidos.includes(estado)) {
        throw createHttpError(400, "Estado inválido. Valores permitidos: programada, completada, cancelada");
      }
      if (!body?.fecha_hora || !body?.motivo) {
        throw createHttpError(400, "Los campos paciente_id, fecha_hora y motivo son obligatorios");
      }
      const nueva = {
        id: db.nextCitaId++,
        paciente_id: pacienteId,
        fecha_hora: body.fecha_hora,
        motivo: String(body.motivo).trim(),
        veterinario: body.veterinario ? String(body.veterinario).trim() : null,
        estado,
      };
      db.citas.push(nueva);
      saveMockDb(db);
      return nueva;
    }
  }

  // /api/citas/{id}
  const matchCita = path.match(/^\/api\/citas\/(\d+)$/);
  if (matchCita) {
    const id = Number(matchCita[1]);
    const idx = db.citas.findIndex((c) => Number(c.id) === id);
    if (idx === -1) {
      throw createHttpError(404, `Cita con id ${id} no encontrada`);
    }

    if (method === "GET") {
      return db.citas[idx];
    }
    if (method === "PUT") {
      const pacienteId = Number(body?.paciente_id);
      const existePaciente = db.pacientes.some((p) => Number(p.id) === pacienteId);
      if (!existePaciente) {
        throw createHttpError(400, "paciente no existe");
      }
      const estadosValidos = ["programada", "completada", "cancelada"];
      const estado = body?.estado || "programada";
      if (!estadosValidos.includes(estado)) {
        throw createHttpError(400, "Estado inválido. Valores permitidos: programada, completada, cancelada");
      }
      db.citas[idx] = {
        ...db.citas[idx],
        paciente_id: pacienteId,
        fecha_hora: body.fecha_hora,
        motivo: String(body.motivo).trim(),
        veterinario: body.veterinario ? String(body.veterinario).trim() : null,
        estado,
      };
      saveMockDb(db);
      return db.citas[idx];
    }
    if (method === "DELETE") {
      db.citas.splice(idx, 1);
      saveMockDb(db);
      return null;
    }
  }

  throw createHttpError(404, `Ruta no encontrada: ${path}`);
}

/* ==========================================================================
   Cliente HTTP con detección de Backend en Vivo vs Fallback Local
   ========================================================================== */
async function apiFetch(method, url, body = null) {
  if (state.forceMock) {
    state.usingMock = true;
    updateConnectionBadge();
    return mockApiRequest(method, url, body);
  }

  const options = {
    method,
    headers: {
      Accept: "application/json",
    },
  };

  if (body !== null) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(url, options);
  } catch (networkErr) {
    // Si no hay servidor o Nginx aún no está levantado localmente, usar simulación en lectura inicial
    if (method === "GET") {
      state.usingMock = true;
      updateConnectionBadge();
      return mockApiRequest(method, url, body);
    }
    throw createHttpError(503, `No se pudo conectar con ${url} (${networkErr.message})`);
  }

  // Si estamos abriendo el archivo estático sin el proxy de nginx (404 HTML o 502 Bad Gateway)
  const contentType = response.headers.get("content-type") || "";
  if (
    method === "GET" &&
    (response.status === 502 ||
      response.status === 503 ||
      response.status === 504 ||
      (response.status === 404 && !contentType.includes("application/json")))
  ) {
    state.usingMock = true;
    updateConnectionBadge();
    return mockApiRequest(method, url, body);
  }

  // Si ya estábamos en modo mock por falta de backend y hacen POST/PUT/DELETE en pruebas locales
  if (
    state.usingMock &&
    (response.status === 404 || response.status === 405 || response.status === 502) &&
    !contentType.includes("application/json")
  ) {
    return mockApiRequest(method, url, body);
  }

  state.usingMock = false;
  updateConnectionBadge();

  if (response.status === 204) {
    return null;
  }

  let payload = null;
  if (contentType.includes("application/json")) {
    try {
      payload = await response.json();
    } catch (_) {
      payload = null;
    }
  } else {
    const text = await response.text();
    try {
      payload = JSON.parse(text);
    } catch (_) {
      payload = { error: text || response.statusText };
    }
  }

  if (!response.ok) {
    const errMsg =
      payload?.error ||
      payload?.message ||
      payload?.detail ||
      `Error HTTP ${response.status} (${response.statusText})`;
    throw createHttpError(response.status, errMsg);
  }

  return payload;
}

/* ==========================================================================
   Carga de Datos y Salud de Microservicios
   ========================================================================== */
async function loadAllData(showSuccessToast = false) {
  try {
    const citasUrl = state.filterPacienteId
      ? `${API_ROUTES.citas}?paciente_id=${encodeURIComponent(state.filterPacienteId)}`
      : API_ROUTES.citas;

    const [pacientes, citas, integrantes] = await Promise.all([
      apiFetch("GET", API_ROUTES.pacientes),
      apiFetch("GET", citasUrl),
      apiFetch("GET", API_ROUTES.integrantes).catch(() => []),
    ]);

    state.pacientes = Array.isArray(pacientes) ? pacientes : [];
    state.citas = Array.isArray(citas) ? citas : [];
    state.integrantes = Array.isArray(integrantes) ? integrantes : [];

    renderIntegrantes();
    populatePacienteSelects();
    renderPacientes();
    renderCitas();
    updateKpis();
    checkServicesHealth();

    if (showSuccessToast) {
      showAlert("info", "Datos actualizados", "Se consultaron correctamente /api/pacientes, /api/citas y /api/integrantes.");
    }
  } catch (err) {
    showAlert("error", `Error al cargar datos (${err.status || "Red"})`, err.message);
  }
}

async function checkServicesHealth() {
  const elPacientes = document.getElementById("ver-pacientes");
  const elCitas = document.getElementById("ver-citas");
  if (!elPacientes || !elCitas) return;
}

function updateConnectionBadge() {
  const badge = document.getElementById("api-mode-badge");
  const text = document.getElementById("api-mode-text");
  if (!badge || !text) return;

  badge.classList.remove("badge-checking", "badge-live", "badge-mock");
  if (state.usingMock) {
    badge.classList.add("badge-mock");
    text.textContent = "Modo Simulación (Contrato 3.4)";
  } else {
    badge.classList.add("badge-live");
    text.textContent = "API en vivo (/api/*)";
  }
}

/* ==========================================================================
   Renderizado de UI (Pacientes, Citas, Integrantes)
   ========================================================================== */
function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatDate(isoDate) {
  if (!isoDate) return "—";
  const clean = String(isoDate).slice(0, 10);
  const parts = clean.split("-");
  if (parts.length !== 3) return escapeHtml(isoDate);
  return `${parts[2]}/${parts[1]}/${parts[0]}`;
}

function formatDateTime(isoDateTime) {
  if (!isoDateTime) return "—";
  const d = new Date(isoDateTime);
  if (Number.isNaN(d.getTime())) return escapeHtml(isoDateTime);
  return d.toLocaleString("es-GT", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function toDatetimeLocalValue(isoDateTime) {
  if (!isoDateTime) return "";
  const d = new Date(isoDateTime);
  if (Number.isNaN(d.getTime())) {
    return String(isoDateTime).slice(0, 16);
  }
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function renderIntegrantes() {
  const footerCarnes = document.getElementById("footer-integrantes");

  if (!state.integrantes.length) {
    footerCarnes.textContent = "Equipo: pendiente de carga en BD";
    return;
  }

  footerCarnes.innerHTML = state.integrantes
    .map(
      (i) =>
        `<span class="footer-member">${escapeHtml(i.nombre)} <strong>${escapeHtml(i.carne)}</strong></span>`
    )
    .join("");
}

function populatePacienteSelects() {
  const filterSelect = document.getElementById("filter-paciente");
  const modalSelect = document.getElementById("cita-paciente-id");

  const currentFilter = state.filterPacienteId;
  const currentModalVal = modalSelect.value;

  const optionsHtml = state.pacientes
    .map(
      (p) =>
        `<option value="${escapeHtml(p.id)}">#${escapeHtml(p.id)} · ${escapeHtml(p.nombre)} (${escapeHtml(
          p.especie
        )} - ${escapeHtml(p.propietario_nombre)})</option>`
    )
    .join("");

  filterSelect.innerHTML = `<option value="">Todos los pacientes</option>${optionsHtml}`;
  filterSelect.value = currentFilter;

  modalSelect.innerHTML = `<option value="">Seleccione un paciente...</option>${optionsHtml}`;
  if (currentModalVal) {
    modalSelect.value = currentModalVal;
  }
}

function renderPacientes() {
  const tbody = document.getElementById("tbody-pacientes");
  const q = state.searchPacientes.trim().toLowerCase();

  // Contar citas por paciente para mostrar en la tabla
  const citasCountMap = new Map();
  state.citas.forEach((c) => {
    const pid = Number(c.paciente_id);
    citasCountMap.set(pid, (citasCountMap.get(pid) || 0) + 1);
  });

  const filtered = state.pacientes.filter((p) => {
    if (!q) return true;
    return [p.id, p.nombre, p.especie, p.raza, p.propietario_nombre, p.propietario_telefono]
      .filter(Boolean)
      .some((val) => String(val).toLowerCase().includes(q));
  });

  if (!filtered.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-cell">
          No hay pacientes que coincidan con la búsqueda.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtered
    .map((p) => {
      const numCitas = citasCountMap.get(Number(p.id)) || 0;
      const nacimiento = p.fecha_nacimiento ? formatDate(p.fecha_nacimiento) : "—";
      const initial = p.nombre ? String(p.nombre).trim().charAt(0).toUpperCase() : "P";
      return `
        <tr>
          <td><span class="id-badge">#${escapeHtml(p.id)}</span></td>
          <td>
            <div class="pet-cell">
              <span class="pet-avatar" aria-hidden="true">${escapeHtml(initial)}</span>
              <span class="entity-primary">${escapeHtml(p.nombre)}</span>
            </div>
          </td>
          <td>
            <span class="species-tag">${escapeHtml(p.especie)}</span>
            <span class="entity-sub">${escapeHtml(p.raza || "Sin raza especificada")}</span>
          </td>
          <td><span class="date-cell">${nacimiento}</span></td>
          <td>
            <span class="entity-primary">${escapeHtml(p.propietario_nombre)}</span>
            <span class="entity-sub">${escapeHtml(p.propietario_telefono || "Sin teléfono")}</span>
          </td>
          <td>
            <button
              type="button"
              class="btn btn-ghost btn-xs"
              data-action="filter-citas-paciente"
              data-id="${escapeHtml(p.id)}"
              title="Filtrar citas de ${escapeHtml(p.nombre)}"
            >
              Ver (${numCitas})
            </button>
          </td>
          <td class="text-right">
            <div class="actions-group">
              <button
                type="button"
                class="btn btn-ghost btn-xs"
                data-action="edit-paciente"
                data-id="${escapeHtml(p.id)}"
              >
                Editar
              </button>
              <button
                type="button"
                class="btn btn-danger-ghost btn-xs"
                data-action="delete-paciente"
                data-id="${escapeHtml(p.id)}"
              >
                Eliminar
              </button>
            </div>
          </td>
        </tr>
      `;
    })
    .join("");
}

function renderCitas() {
  const tbody = document.getElementById("tbody-citas");
  const clearBtn = document.getElementById("btn-clear-filters");

  if (state.filterPacienteId || state.filterEstado) {
    clearBtn.classList.remove("hidden");
  } else {
    clearBtn.classList.add("hidden");
  }

  // Mapa de pacientes para cruzar paciente_id -> nombre de la mascota (Requisito B4 / 03-frontend.md)
  const pacientesMap = new Map();
  state.pacientes.forEach((p) => {
    pacientesMap.set(Number(p.id), p);
  });

  const filtered = state.citas.filter((c) => {
    if (state.filterPacienteId && Number(c.paciente_id) !== Number(state.filterPacienteId)) {
      return false;
    }
    if (state.filterEstado && String(c.estado).toLowerCase() !== state.filterEstado.toLowerCase()) {
      return false;
    }
    return true;
  });

  if (!filtered.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-cell">
          No hay citas médicas registradas para los filtros seleccionados.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtered
    .map((c) => {
      const pac = pacientesMap.get(Number(c.paciente_id));
      const pacienteNombre = pac ? pac.nombre : `Paciente #${c.paciente_id}`;
      const pacienteDetalle = pac
        ? `${pac.especie} · Prop: ${pac.propietario_nombre}`
        : `ID: ${c.paciente_id}`;
      const estadoNorm = ["programada", "completada", "cancelada"].includes(String(c.estado).toLowerCase())
        ? String(c.estado).toLowerCase()
        : "programada";

      return `
        <tr>
          <td><span class="id-badge">#${escapeHtml(c.id)}</span></td>
          <td>
            <span class="entity-primary">${escapeHtml(pacienteNombre)} <span class="id-badge">#${escapeHtml(
        c.paciente_id
      )}</span></span>
            <span class="entity-sub">${escapeHtml(pacienteDetalle)}</span>
          </td>
          <td><span class="date-cell">${formatDateTime(c.fecha_hora)}</span></td>
          <td>${escapeHtml(c.motivo)}</td>
          <td><span class="entity-primary">${escapeHtml(c.veterinario || "Por asignar")}</span></td>
          <td>
            <span class="status-pill status-${estadoNorm}">${escapeHtml(estadoNorm)}</span>
          </td>
          <td class="text-right">
            <div class="actions-group">
              <button
                type="button"
                class="btn btn-ghost btn-xs"
                data-action="edit-cita"
                data-id="${escapeHtml(c.id)}"
              >
                Editar
              </button>
              <button
                type="button"
                class="btn btn-danger-ghost btn-xs"
                data-action="delete-cita"
                data-id="${escapeHtml(c.id)}"
              >
                Eliminar
              </button>
            </div>
          </td>
        </tr>
      `;
    })
    .join("");
}

function updateKpis() {
  const totalPacientes = state.pacientes.length;
  const totalCitas = state.citas.length;
  const programadas = state.citas.filter((c) => String(c.estado).toLowerCase() === "programada").length;

  document.getElementById("kpi-pacientes").textContent = totalPacientes;
  document.getElementById("kpi-citas").textContent = totalCitas;
  document.getElementById("kpi-programadas").textContent = programadas;
  document.getElementById("tab-count-pacientes").textContent = totalPacientes;
  document.getElementById("tab-count-citas").textContent = totalCitas;
}

/* ==========================================================================
   Alertas y Modales
   ========================================================================== */
function showAlert(type, title, message) {
  const box = document.getElementById("alert-box");
  const titleEl = document.getElementById("alert-title");
  const msgEl = document.getElementById("alert-message");

  box.classList.remove("hidden", "alert-error", "alert-success", "alert-info");
  if (type === "error") box.classList.add("alert-error");
  else if (type === "success") box.classList.add("alert-success");
  else box.classList.add("alert-info");

  titleEl.textContent = `${title}:`;
  msgEl.textContent = message;
}

function hideAlert() {
  document.getElementById("alert-box").classList.add("hidden");
}

function openModal(modalId) {
  document.getElementById(modalId).classList.remove("hidden");
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.add("hidden");
}

/* ==========================================================================
   Operaciones CRUD de Pacientes (/api/pacientes)
   ========================================================================== */
function openNewPacienteModal() {
  document.getElementById("modal-paciente-title").textContent = "Registrar Nuevo Paciente";
  document.getElementById("form-paciente").reset();
  document.getElementById("paciente-id").value = "";
  openModal("modal-paciente");
}

function openEditPacienteModal(id) {
  const paciente = state.pacientes.find((p) => Number(p.id) === Number(id));
  if (!paciente) {
    showAlert("error", "No encontrado", `No se encontró el paciente #${id}.`);
    return;
  }

  document.getElementById("modal-paciente-title").textContent = `Editar Paciente #${paciente.id}`;
  document.getElementById("paciente-id").value = paciente.id;
  document.getElementById("paciente-nombre").value = paciente.nombre || "";
  document.getElementById("paciente-especie").value = paciente.especie || "";
  document.getElementById("paciente-raza").value = paciente.raza || "";
  document.getElementById("paciente-nacimiento").value = paciente.fecha_nacimiento
    ? String(paciente.fecha_nacimiento).slice(0, 10)
    : "";
  document.getElementById("paciente-propietario").value = paciente.propietario_nombre || "";
  document.getElementById("paciente-telefono").value = paciente.propietario_telefono || "";

  openModal("modal-paciente");
}

async function handlePacienteSubmit(event) {
  event.preventDefault();
  const id = document.getElementById("paciente-id").value;

  const payload = {
    nombre: document.getElementById("paciente-nombre").value.trim(),
    especie: document.getElementById("paciente-especie").value.trim(),
    raza: document.getElementById("paciente-raza").value.trim() || null,
    fecha_nacimiento: document.getElementById("paciente-nacimiento").value || null,
    propietario_nombre: document.getElementById("paciente-propietario").value.trim(),
    propietario_telefono: document.getElementById("paciente-telefono").value.trim() || null,
  };

  try {
    if (id) {
      await apiFetch("PUT", `${API_ROUTES.pacientes}/${id}`, payload);
      showAlert("success", "Paciente actualizado (200 OK)", `Se actualizó a "${payload.nombre}" correctamente.`);
    } else {
      await apiFetch("POST", API_ROUTES.pacientes, payload);
      showAlert("success", "Paciente creado (201 Created)", `Se registró a "${payload.nombre}" correctamente.`);
    }
    closeModal("modal-paciente");
    await loadAllData(false);
  } catch (err) {
    showAlert("error", `Error HTTP ${err.status || 400} al guardar paciente`, err.message);
  }
}

async function handleDeletePaciente(id) {
  const paciente = state.pacientes.find((p) => Number(p.id) === Number(id));
  const nombre = paciente ? paciente.nombre : `#${id}`;

  if (!window.confirm(`¿Deseas eliminar al paciente "${nombre}" (ID #${id})?`)) {
    return;
  }

  try {
    await apiFetch("DELETE", `${API_ROUTES.pacientes}/${id}`);
    showAlert("success", "Paciente eliminado (204 No Content)", `El paciente "${nombre}" fue eliminado.`);
    if (String(state.filterPacienteId) === String(id)) {
      state.filterPacienteId = "";
    }
    await loadAllData(false);
  } catch (err) {
    if (err.status === 409) {
      showAlert(
        "error",
        "Error 409 Conflict (Paciente con citas asociadas)",
        `${err.message}. Elimina primero sus citas antes de borrar el paciente.`
      );
    } else {
      showAlert("error", `Error HTTP ${err.status || 500} al eliminar paciente`, err.message);
    }
  }
}

/* ==========================================================================
   Operaciones CRUD de Citas (/api/citas)
   ========================================================================== */
function openNewCitaModal() {
  populatePacienteSelects();
  document.getElementById("modal-cita-title").textContent = "Programar Nueva Cita";
  document.getElementById("form-cita").reset();
  document.getElementById("cita-id").value = "";
  document.getElementById("cita-estado").value = "programada";

  if (state.filterPacienteId) {
    document.getElementById("cita-paciente-id").value = state.filterPacienteId;
  }

  // Fecha sugerida por defecto: mañana a las 10:00
  const tomorrow = new Date(Date.now() + 24 * 60 * 60 * 1000);
  tomorrow.setHours(10, 0, 0, 0);
  document.getElementById("cita-fecha-hora").value = toDatetimeLocalValue(tomorrow.toISOString());

  openModal("modal-cita");
}

function openEditCitaModal(id) {
  populatePacienteSelects();
  const cita = state.citas.find((c) => Number(c.id) === Number(id));
  if (!cita) {
    showAlert("error", "No encontrada", `No se encontró la cita #${id}.`);
    return;
  }

  document.getElementById("modal-cita-title").textContent = `Editar Cita #${cita.id}`;
  document.getElementById("cita-id").value = cita.id;
  document.getElementById("cita-paciente-id").value = cita.paciente_id;
  document.getElementById("cita-fecha-hora").value = toDatetimeLocalValue(cita.fecha_hora);
  document.getElementById("cita-motivo").value = cita.motivo || "";
  document.getElementById("cita-veterinario").value = cita.veterinario || "";
  document.getElementById("cita-estado").value = cita.estado || "programada";

  openModal("modal-cita");
}

async function handleCitaSubmit(event) {
  event.preventDefault();
  const id = document.getElementById("cita-id").value;
  const rawFecha = document.getElementById("cita-fecha-hora").value;
  const isoFecha = rawFecha.length === 16 ? `${rawFecha}:00` : rawFecha;

  const payload = {
    paciente_id: Number(document.getElementById("cita-paciente-id").value),
    fecha_hora: isoFecha,
    motivo: document.getElementById("cita-motivo").value.trim(),
    veterinario: document.getElementById("cita-veterinario").value.trim() || null,
    estado: document.getElementById("cita-estado").value,
  };

  try {
    if (id) {
      await apiFetch("PUT", `${API_ROUTES.citas}/${id}`, payload);
      showAlert("success", "Cita actualizada (200 OK)", `La cita #${id} fue actualizada correctamente.`);
    } else {
      await apiFetch("POST", API_ROUTES.citas, payload);
      showAlert("success", "Cita creada (201 Created)", "La cita médica fue registrada correctamente.");
    }
    closeModal("modal-cita");
    await loadAllData(false);
  } catch (err) {
    showAlert("error", `Error HTTP ${err.status || 400} al guardar cita`, err.message);
  }
}

async function handleDeleteCita(id) {
  if (!window.confirm(`¿Deseas eliminar la cita #${id}?`)) {
    return;
  }

  try {
    await apiFetch("DELETE", `${API_ROUTES.citas}/${id}`);
    showAlert("success", "Cita eliminada (204 No Content)", `La cita #${id} fue eliminada.`);
    await loadAllData(false);
  } catch (err) {
    showAlert("error", `Error HTTP ${err.status || 500} al eliminar cita`, err.message);
  }
}

/* ==========================================================================
   Eventos e Inicialización
   ========================================================================== */
function setViewMode(mode) {
  const grid = document.getElementById("workspace-grid");
  const panelPacientes = document.getElementById("panel-pacientes");
  const panelCitas = document.getElementById("panel-citas");

  document.querySelectorAll(".tab-btn").forEach((btn) => {
    const isActive = btn.dataset.view === mode;
    btn.classList.toggle("active", isActive);
    btn.setAttribute("aria-selected", String(isActive));
  });

  if (mode === "split") {
    grid.classList.remove("hidden", "view-single");
    grid.classList.add("view-split");
    panelPacientes.classList.remove("hidden");
    panelCitas.classList.remove("hidden");
  } else if (mode === "pacientes") {
    grid.classList.remove("hidden", "view-split");
    grid.classList.add("view-single");
    panelPacientes.classList.remove("hidden");
    panelCitas.classList.add("hidden");
  } else if (mode === "citas") {
    grid.classList.remove("hidden", "view-split");
    grid.classList.add("view-single");
    panelPacientes.classList.add("hidden");
    panelCitas.classList.remove("hidden");
  }
}

function bindEvents() {
  document.getElementById("btn-refresh").addEventListener("click", () => loadAllData(true));
  document.getElementById("alert-close").addEventListener("click", hideAlert);

  // Pestañas de vista
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => setViewMode(btn.dataset.view));
  });

  // Botones abrir modales
  document.getElementById("btn-new-paciente").addEventListener("click", openNewPacienteModal);
  document.getElementById("btn-new-cita").addEventListener("click", openNewCitaModal);

  // Cerrar modales
  document.querySelectorAll("[data-close]").forEach((btn) => {
    btn.addEventListener("click", () => closeModal(btn.dataset.close));
  });

  // Enviar formularios
  document.getElementById("form-paciente").addEventListener("submit", handlePacienteSubmit);
  document.getElementById("form-cita").addEventListener("submit", handleCitaSubmit);

  // Búsqueda y filtros
  document.getElementById("search-pacientes").addEventListener("input", (e) => {
    state.searchPacientes = e.target.value;
    renderPacientes();
  });

  document.getElementById("filter-paciente").addEventListener("change", async (e) => {
    state.filterPacienteId = e.target.value;
    await loadAllData(false);
  });

  document.getElementById("filter-estado").addEventListener("change", (e) => {
    state.filterEstado = e.target.value;
    renderCitas();
  });

  document.getElementById("btn-clear-filters").addEventListener("click", async () => {
    state.filterPacienteId = "";
    state.filterEstado = "";
    document.getElementById("filter-paciente").value = "";
    document.getElementById("filter-estado").value = "";
    await loadAllData(false);
  });

  // Delegación de eventos en tabla de pacientes
  document.getElementById("tbody-pacientes").addEventListener("click", async (e) => {
    const btn = e.target.closest("button[data-action]");
    if (!btn) return;
    const action = btn.dataset.action;
    const id = btn.dataset.id;

    if (action === "edit-paciente") {
      openEditPacienteModal(id);
    } else if (action === "delete-paciente") {
      await handleDeletePaciente(id);
    } else if (action === "filter-citas-paciente") {
      state.filterPacienteId = String(id);
      document.getElementById("filter-paciente").value = String(id);
      await loadAllData(false);
    }
  });

  // Delegación de eventos en tabla de citas
  document.getElementById("tbody-citas").addEventListener("click", async (e) => {
    const btn = e.target.closest("button[data-action]");
    if (!btn) return;
    const action = btn.dataset.action;
    const id = btn.dataset.id;

    if (action === "edit-cita") {
      openEditCitaModal(id);
    } else if (action === "delete-cita") {
      await handleDeleteCita(id);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  bindEvents();
  loadAllData(false);
});

