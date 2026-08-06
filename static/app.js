document.addEventListener("DOMContentLoaded", () => {
    verificarSesion();
});

// --- AUTENTICACIÓN Y LOGIN ---
function verificarSesion() {
    const usuarioLogueado = localStorage.getItem("tc_logged_in");
    const loginOverlay = document.getElementById("loginOverlay");

    if (usuarioLogueado === "true") {
        if (loginOverlay) loginOverlay.classList.add("hidden");
        cargarOrdenes();
        cargarClientes();
        cargarStock();
        cargarCaja();
    } else {
        if (loginOverlay) loginOverlay.classList.remove("hidden");
    }
}

async function procesarLogin(e) {
    e.preventDefault();
    const usuarioInput = document.getElementById("loginUsuario").value;
    const passwordInput = document.getElementById("loginPassword").value;
    const errorEl = document.getElementById("loginError");

    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ usuario: usuarioInput, password: passwordInput })
        });

        const data = await res.json();

        if (res.ok && data.status === "ok") {
            localStorage.setItem("tc_logged_in", "true");
            if (errorEl) errorEl.classList.add("hidden");
            document.getElementById("loginOverlay").classList.add("hidden");
            cargarOrdenes();
            cargarClientes();
            cargarStock();
            cargarCaja();
        } else {
            if (errorEl) {
                errorEl.innerText = data.mensaje || "Usuario o contraseña incorrectos";
                errorEl.classList.remove("hidden");
            }
        }
    } catch (err) {
        console.error("Error al autenticar:", err);
        if (errorEl) {
            errorEl.innerText = "Error de conexión con el servidor";
            errorEl.classList.remove("hidden");
        }
    }
}

function cerrarSesion() {
    localStorage.removeItem("tc_logged_in");
    location.reload();
}

function cambiarVista(vista) {
    const vistas = ['vistaOrdenes', 'vistaClientes', 'vistaStock', 'vistaCaja'];
    vistas.forEach(v => {
        const el = document.getElementById(v);
        if (el) el.classList.add("hidden");
    });

    if (vista === 'ordenes') {
        document.getElementById("vistaOrdenes").classList.remove("hidden");
        cargarOrdenes();
    } else if (vista === 'clientes') {
        document.getElementById("vistaClientes").classList.remove("hidden");
        cargarClientes();
    } else if (vista === 'stock') {
        document.getElementById("vistaStock").classList.remove("hidden");
        cargarStock();
    } else if (vista === 'caja') {
        document.getElementById("vistaCaja").classList.remove("hidden");
        cargarCaja();
    }
}

// --- ÓRDENES ---
async function cargarOrdenes() {
    try {
        const res = await fetch('/api/ordenes');
        const data = await res.json();
        renderizarOrdenes(data);
    } catch (err) {
        console.error("Error al cargar órdenes:", err);
    }
}

function renderizarOrdenes(lista) {
    const container = document.getElementById("ordersContainer");
    if (!container) return;
    container.innerHTML = "";

    if (lista.length === 0) {
        container.innerHTML = `<p class="text-slate-500 text-sm col-span-full text-center py-8">No hay órdenes registradas.</p>`;
        return;
    }

    lista.forEach(ord => {
        const card = document.createElement("div");
        card.className = "bg-cardbg border border-bordercolor rounded-2xl p-5 shadow-lg flex flex-col justify-between";
        card.innerHTML = `
            <div>
                <div class="flex items-center justify-between mb-3">
                    <span class="text-xs font-bold text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-lg">#${ord.id}</span>
                    <span class="text-xs font-medium text-slate-300 bg-slate-800 px-2.5 py-1 rounded-lg border border-bordercolor">${ord.estado}</span>
                </div>
                <h3 class="font-bold text-white text-lg mb-1">${ord.equipo}</h3>
                <p class="text-xs text-slate-400 mb-4">Cliente: <span class="text-slate-200 font-medium">${ord.cliente}</span></p>
                <div class="bg-darkbg/50 border border-bordercolor/50 rounded-xl p-3 mb-4">
                    <p class="text-xs text-slate-400"><strong class="text-slate-300">Falla:</strong> ${ord.falla}</p>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

async function guardarOrden(e) {
    e.preventDefault();
    const nueva = {
        cliente: document.getElementById("clienteInput").value,
        equipo: document.getElementById("equipoInput").value,
        falla: document.getElementById("fallaInput").value
    };

    await fetch('/api/ordenes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(nueva)
    });

    cargarOrdenes();
    cerrarModal('modalNuevaOrden');
    document.getElementById("formNuevaOrden").reset();
}

// --- CLIENTES ---
async function cargarClientes() {
    try {
        const res = await fetch('/api/clientes');
        const data = await res.json();
        renderizarClientes(data);
    } catch (err) {
        console.error("Error al cargar clientes:", err);
    }
}

function renderizarClientes(lista) {
    const container = document.getElementById("tablaClientes");
    if (!container) return;
    container.innerHTML = "";

    lista.forEach(c => {
        const row = document.createElement("tr");
        row.className = "border-b border-bordercolor/50 text-sm";
        row.innerHTML = `
            <td class="py-3 px-4 text-white font-medium">${c.nombre}</td>
            <td class="py-3 px-4 text-slate-400">${c.telefono || '-'}</td>
            <td class="py-3 px-4 text-slate-400">${c.direccion || '-'}</td>
        `;
        container.appendChild(row);
    });
}

async function guardarCliente(e) {
    e.preventDefault();
    const nuevo = {
        nombre: document.getElementById("clienteNombreInput").value,
        telefono: document.getElementById("clienteTelInput").value,
        direccion: document.getElementById("clienteDirInput").value
    };

    await fetch('/api/clientes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(nuevo)
    });

    cargarClientes();
    cerrarModal('modalNuevoCliente');
    document.getElementById("formNuevoCliente").reset();
}

// --- STOCK / REPUESTOS ---
async function cargarStock() {
    try {
        const res = await fetch('/api/repuestos');
        const data = await res.json();
        renderizarStock(data);
    } catch (err) {
        console.error("Error al cargar stock:", err);
    }
}

function renderizarStock(lista) {
    const container = document.getElementById("tablaStock");
    if (!container) return;
    container.innerHTML = "";

    lista.forEach(r => {
        const row = document.createElement("tr");
        row.className = "border-b border-bordercolor/50 text-sm";
        row.innerHTML = `
            <td class="py-3 px-4 text-white font-medium">${r.nombre}</td>
            <td class="py-3 px-4 font-bold ${r.cantidad < 5 ? 'text-amber-400' : 'text-emerald-400'}">${r.cantidad} u.</td>
            <td class="py-3 px-4 text-slate-300 font-semibold">$${r.precio.toLocaleString()}</td>
        `;
        container.appendChild(row);
    });
}

async function guardarRepuesto(e) {
    e.preventDefault();
    const nuevo = {
        nombre: document.getElementById("repuestoNombreInput").value,
        cantidad: parseInt(document.getElementById("repuestoCantInput").value),
        precio: parseFloat(document.getElementById("repuestoPrecioInput").value)
    };

    await fetch('/api/repuestos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(nuevo)
    });

    cargarStock();
    cerrarModal('modalNuevoRepuesto');
    document.getElementById("formNuevoRepuesto").reset();
}

// --- CAJA Y BALANCE ---
async function cargarCaja() {
    try {
        const res = await fetch('/api/caja');
        const data = await res.json();
        renderizarMovimientosCaja(data);
    } catch (err) {
        console.error("Error al cargar caja:", err);
    }
}

function renderizarMovimientosCaja(lista) {
    const container = document.getElementById("tablaMovimientos");
    if (!container) return;
    container.innerHTML = "";

    let ingresos = 0;
    let egresos = 0;

    lista.forEach(m => {
        if (m.tipo === "ingreso") ingresos += m.monto;
        if (m.tipo === "egreso") egresos += m.monto;

        const row = document.createElement("tr");
        row.className = "border-b border-bordercolor/50 text-sm";
        const esIngreso = m.tipo === "ingreso";
        row.innerHTML = `
            <td class="py-3 px-4 text-slate-400">${m.fecha}</td>
            <td class="py-3 px-4 text-white font-medium">${m.concepto}</td>
            <td class="py-3 px-4 ${esIngreso ? 'text-emerald-400' : 'text-rose-400'} font-bold">
                ${esIngreso ? '+' : '-'} $${m.monto.toLocaleString()}
            </td>
        `;
        container.appendChild(row);
    });

    const totalIngresosEl = document.getElementById("totalIngresos");
    const totalEgresosEl = document.getElementById("totalEgresos");
    const saldoTotalEl = document.getElementById("saldoTotal");

    if (totalIngresosEl) totalIngresosEl.innerText = `$${ingresos.toLocaleString()}`;
    if (totalEgresosEl) totalEgresosEl.innerText = `$${egresos.toLocaleString()}`;
    if (saldoTotalEl) saldoTotalEl.innerText = `$${(ingresos - egresos).toLocaleString()}`;
}

async function guardarMovimientoCaja(e) {
    e.preventDefault();
    const nuevo = {
        tipo: document.getElementById("tipoInput").value,
        concepto: document.getElementById("conceptoInput").value,
        monto: parseFloat(document.getElementById("montoInput").value),
        fecha: new Date().toISOString().split('T')[0]
    };

    await fetch('/api/caja', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(nuevo)
    });

    cargarCaja();
    cerrarModal('modalNuevoMovimiento');
    document.getElementById("formNuevoMovimiento").reset();
}

// --- MODALES Y UTILIDADES ---
function abrirModal(id) { document.getElementById(id).classList.remove("hidden"); }
function cerrarModal(id) { document.getElementById(id).classList.add("hidden"); }
function abrirModalNuevaOrden() { abrirModal('modalNuevaOrden'); }
function cerrarModalNuevaOrden() { cerrarModal('modalNuevaOrden'); }
function abrirModalMovimiento() { abrirModal('modalNuevoMovimiento'); }
function cerrarModalMovimiento() { cerrarModal('modalNuevoMovimiento'); }

async function filtrarOrdenes() {
    const query = document.getElementById("searchInput").value.toLowerCase();
    const res = await fetch('/api/ordenes');
    const ordenes = await res.json();
    const filtradas = ordenes.filter(o => 
        o.cliente.toLowerCase().includes(query) ||
        o.equipo.toLowerCase().includes(query) ||
        o.id.toString().includes(query)
    );
    renderizarOrdenes(filtradas);
}