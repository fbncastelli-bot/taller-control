let ordenSeleccionadaId = null;
let repuestoSeleccionadoId = null;
let firmwareSeleccionadoUrl = null;

document.addEventListener("DOMContentLoaded", () => {
    verificarSesion();
});

// --- SESIÓN ---
function verificarSesion() {
    const logueado = localStorage.getItem("tc_logged_in");
    const overlay = document.getElementById("loginOverlay");
    if (logueado === "true") {
        if (overlay) overlay.classList.add("hidden");
        cargarOrdenes();
        cargarStock();
        cargarPublicaciones();
        cargarCaja();
        cargarFirmwares();
    } else {
        if (overlay) overlay.classList.remove("hidden");
    }
}

async function procesarLogin(e) {
    e.preventDefault();
    const u = document.getElementById("loginUsuario").value;
    const p = document.getElementById("loginPassword").value;
    const err = document.getElementById("loginError");

    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ usuario: u, password: p })
        });
        const data = await res.json();
        if (res.ok && data.status === "ok") {
            localStorage.setItem("tc_logged_in", "true");
            document.getElementById("loginOverlay").classList.add("hidden");
            cargarOrdenes();
            cargarStock();
            cargarPublicaciones();
            cargarCaja();
            cargarFirmwares();
        } else {
            err.innerText = data.mensaje || "Error al autenticar";
            err.classList.remove("hidden");
        }
    } catch (e) {
        err.innerText = "Error de conexión";
        err.classList.remove("hidden");
    }
}

function cerrarSesion() {
    localStorage.removeItem("tc_logged_in");
    location.reload();
}

// --- VISTAS ---
function cambiarVista(vista) {
    const ids = ['vistaOrdenes', 'vistaPlacas', 'vistaStock', 'vistaVentas', 'vistaCaja', 'vistaFirmwares'];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.add("hidden");
    });

    const btns = ['btnTabOrdenes', 'btnTabPlacas', 'btnTabStock', 'btnTabVentas', 'btnTabCaja', 'btnTabFirmwares'];
    btns.forEach(b => {
        const btn = document.getElementById(b);
        if (btn) {
            btn.className = "px-4 py-2 text-xs font-semibold rounded-t-lg text-slate-400 hover:text-white transition";
        }
    });

    if (vista === 'ordenes') {
        document.getElementById("vistaOrdenes").classList.remove("hidden");
        document.getElementById("btnTabOrdenes").className = "px-4 py-2 text-xs font-semibold rounded-t-lg bg-cyan-600 text-white border-t border-x border-cyan-400 transition";
        cargarOrdenes();
    } else if (vista === 'placas') {
        document.getElementById("vistaPlacas").classList.remove("hidden");
        document.getElementById("btnTabPlacas").className = "px-4 py-2 text-xs font-semibold rounded-t-lg bg-cyan-600 text-white border-t border-x border-cyan-400 transition";
    } else if (vista === 'stock') {
        document.getElementById("vistaStock").classList.remove("hidden");
        document.getElementById("btnTabStock").className = "px-4 py-2 text-xs font-semibold rounded-t-lg bg-cyan-600 text-white border-t border-x border-cyan-400 transition";
        cargarStock();
    } else if (vista === 'ventas') {
        document.getElementById("vistaVentas").classList.remove("hidden");
        document.getElementById("btnTabVentas").className = "px-4 py-2 text-xs font-semibold rounded-t-lg bg-cyan-600 text-white border-t border-x border-cyan-400 transition";
        cargarPublicaciones();
    } else if (vista === 'caja') {
        document.getElementById("vistaCaja").classList.remove("hidden");
        document.getElementById("btnTabCaja").className = "px-4 py-2 text-xs font-semibold rounded-t-lg bg-cyan-600 text-white border-t border-x border-cyan-400 transition";
        cargarCaja();
    } else if (vista === 'firmwares') {
        document.getElementById("vistaFirmwares").classList.remove("hidden");
        document.getElementById("btnTabFirmwares").className = "px-4 py-2 text-xs font-semibold rounded-t-lg bg-cyan-600 text-white border-t border-x border-cyan-400 transition";
        cargarFirmwares();
    }
}

// --- ÓRDENES ---
async function cargarOrdenes() {
    const res = await fetch('/api/ordenes');
    const data = await res.json();
    renderOrdenes(data);
}

function renderOrdenes(lista) {
    const tbody = document.getElementById("tablaOrdenesBody");
    tbody.innerHTML = "";
    lista.forEach(o => {
        const tr = document.createElement("tr");
        tr.className = "border-b border-bordercolor/50 hover:bg-slate-800/50 cursor-pointer";
        tr.onclick = () => {
            document.querySelectorAll("#tablaOrdenesBody tr").forEach(r => r.classList.remove("bg-slate-800"));
            tr.classList.add("bg-slate-800");
            ordenSeleccionadaId = o.id;
        };
        tr.innerHTML = `
            <td class="py-2 px-3 text-cyan-400 font-bold">${o.id}</td>
            <td class="py-2 px-3 text-white font-medium">${o.cliente}</td>
            <td class="py-2 px-3 text-slate-300">${o.equipo}</td>
            <td class="py-2 px-3 text-slate-400">${o.falla}</td>
            <td class="py-2 px-3 text-amber-400 font-bold">$${(o.presupuesto || 0).toLocaleString()}</td>
            <td class="py-2 px-3 text-cyan-300 font-semibold">${o.estado}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function guardarOrdenDirecta(e) {
    e.preventDefault();
    const o = {
        cliente: document.getElementById("ordCliente").value,
        equipo: document.getElementById("ordEquipo").value,
        falla: document.getElementById("ordFalla").value,
        presupuesto: parseFloat(document.getElementById("ordPresupuesto").value || 0),
        estado: document.getElementById("ordEstado").value
    };
    await fetch('/api/ordenes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(o)
    });
    document.getElementById("ordCliente").value = "";
    document.getElementById("ordEquipo").value = "";
    document.getElementById("ordFalla").value = "";
    document.getElementById("ordPresupuesto").value = "";
    cargarOrdenes();
}

async function filtrarOrdenes() {
    const q = document.getElementById("buscarOrdenInput").value.toLowerCase();
    const res = await fetch('/api/ordenes');
    const list = await res.json();
    const filt = list.filter(o =>
        o.cliente.toLowerCase().includes(q) ||
        o.equipo.toLowerCase().includes(q) ||
        o.id.toString().includes(q)
    );
    renderOrdenes(filt);
}

function verFichaInforme() {
    if (!ordenSeleccionadaId) return alert("Seleccioná una orden de la lista.");
    alert(`Generando Ficha/Informe para la Orden N° ${ordenSeleccionadaId}`);
}

function imprimirComprobanteCliente() {
    if (!ordenSeleccionadaId) return alert("Seleccioná una orden de la lista.");
    alert(`Imprimiendo comprobante para el cliente de la Orden N° ${ordenSeleccionadaId}`);
}

function imprimirTicketTapa() {
    if (!ordenSeleccionadaId) return alert("Seleccioná una orden de la lista.");
    alert(`Imprimiendo ticket para tapa TV de la Orden N° ${ordenSeleccionadaId}`);
}

// --- STOCK COMPONENTES ---
async function cargarStock() {
    const res = await fetch('/api/repuestos');
    const data = await res.json();
    renderStock(data);
}

function renderStock(lista) {
    const tbody = document.getElementById("tablaStockBody");
    tbody.innerHTML = "";
    lista.forEach(r => {
        const tr = document.createElement("tr");
        tr.className = "border-b border-bordercolor/50 hover:bg-slate-800/50 cursor-pointer";
        tr.onclick = () => {
            document.querySelectorAll("#tablaStockBody tr").forEach(row => row.classList.remove("bg-slate-800"));
            tr.classList.add("bg-slate-800");
            repuestoSeleccionadoId = r.id;
            tr.dataset.codigo = r.nombre;
        };
        tr.innerHTML = `
            <td class="py-2 px-3 text-cyan-400 font-bold">${r.id}</td>
            <td class="py-2 px-3 text-slate-300">${r.categoria || 'Gral'}</td>
            <td class="py-2 px-3 text-white font-medium">${r.nombre}</td>
            <td class="py-2 px-3 text-slate-400">${r.ubicacion || '-'}</td>
            <td class="py-2 px-3 font-bold ${r.cantidad < 5 ? 'text-amber-400' : 'text-emerald-400'}">${r.cantidad} u.</td>
        `;
        tbody.appendChild(tr);
    });
}

async function guardarComponenteDirecto(e) {
    e.preventDefault();
    const c = {
        categoria: document.getElementById("compCategoria").value,
        nombre: document.getElementById("compCodigo").value,
        ubicacion: document.getElementById("compUbicacion").value,
        cantidad: parseInt(document.getElementById("compCantidad").value || 1),
        precio: 0.0
    };
    await fetch('/api/repuestos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(c)
    });
    document.getElementById("compCodigo").value = "";
    document.getElementById("compUbicacion").value = "";
    document.getElementById("compCantidad").value = "1";
    cargarStock();
}

async function sumarStockSeleccionado() {
    if (!repuestoSeleccionadoId) return alert("Seleccioná un componente de la tabla.");
    await fetch(`/api/repuestos/${repuestoSeleccionadoId}/stock`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cambio: 1 })
    });
    cargarStock();
}

async function restarStockSeleccionado() {
    if (!repuestoSeleccionadoId) return alert("Seleccioná un componente de la tabla.");
    await fetch(`/api/repuestos/${repuestoSeleccionadoId}/stock`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cambio: -1 })
    });
    cargarStock();
}

function buscarDatasheetSeleccionado() {
    const selected = document.querySelector("#tablaStockBody tr.bg-slate-800");
    if (!selected) return alert("Seleccioná un componente de la tabla.");
    const codigo = selected.dataset.codigo;
    window.open(`https://www.google.com/search?q=${encodeURIComponent(codigo + ' datasheet pdf')}`, '_blank');
}

function imprimirEtiquetaComponente() {
    if (!repuestoSeleccionadoId) return alert("Seleccioná un componente de la tabla.");
    alert(`Imprimiendo etiqueta de gaveta para el componente ID ${repuestoSeleccionadoId}`);
}

async function filtrarComponentes() {
    const q = document.getElementById("buscarCompInput").value.toLowerCase();
    const res = await fetch('/api/repuestos');
    const list = await res.json();
    const filt = list.filter(r =>
        r.nombre.toLowerCase().includes(q) ||
        (r.categoria && r.categoria.toLowerCase().includes(q))
    );
    renderStock(filt);
}

// --- VENTAS Y USADOS ---
async function cargarPublicaciones() {
    const res = await fetch('/api/publicaciones');
    const data = await res.json();
    renderPublicaciones(data);
}

function renderPublicaciones(lista) {
    const tbody = document.getElementById("tablaVentasBody");
    tbody.innerHTML = "";
    lista.forEach(p => {
        const tr = document.createElement("tr");
        tr.className = "border-b border-bordercolor/50";
        tr.innerHTML = `
            <td class="py-2 px-3 text-cyan-400 font-bold">${p.id}</td>
            <td class="py-2 px-3 text-white font-medium">${p.producto}</td>
            <td class="py-2 px-3 text-emerald-400 font-bold">$${p.precio.toLocaleString()}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function guardarPublicacion(e) {
    e.preventDefault();
    const p = {
        producto: document.getElementById("ventProducto").value,
        precio: parseFloat(document.getElementById("ventPrecio").value || 0),
        estado: document.getElementById("ventEstado").value
    };
    await fetch('/api/publicaciones', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(p)
    });
    document.getElementById("ventProducto").value = "";
    document.getElementById("ventPrecio").value = "";
    cargarPublicaciones();
}

function consultarMercadoLibre() {
    const prod = document.getElementById("ventProducto").value.trim();
    if (!prod) return alert("Ingresá el nombre o código del producto en el campo 'Producto / Equipo'.");
    window.open(`https://listado.mercadolibre.com.ar/${encodeURIComponent(prod)}`, '_blank');
}

// --- CAJA Y FINANZAS ---
async function cargarCaja() {
    const res = await fetch('/api/caja');
    const data = await res.json();
    renderCaja(data);
}

function renderCaja(lista) {
    const tbody = document.getElementById("tablaCajaBody");
    tbody.innerHTML = "";
    let ingresos = 0;
    let egresos = 0;

    lista.forEach(m => {
        if (m.tipo.toLowerCase() === "ingreso") ingresos += m.monto;
        if (m.tipo.toLowerCase() === "egreso") egresos += m.monto;

        const tr = document.createElement("tr");
        tr.className = "border-b border-bordercolor/50";
        const esIng = m.tipo.toLowerCase() === "ingreso";
        tr.innerHTML = `
            <td class="py-2 px-3 text-cyan-400 font-bold">${m.id}</td>
            <td class="py-2 px-3 text-slate-400">${m.fecha}</td>
            <td class="py-2 px-3 ${esIng ? 'text-emerald-400' : 'text-rose-400'} font-semibold">${m.tipo}</td>
            <td class="py-2 px-3 text-white font-medium">${m.concepto}</td>
            <td class="py-2 px-3 ${esIng ? 'text-emerald-400' : 'text-rose-400'} font-bold">$${m.monto.toLocaleString()}</td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById("lblIngresos").innerText = `$${ingresos.toLocaleString()}`;
    document.getElementById("lblEgresos").innerText = `$${egresos.toLocaleString()}`;
}

async function registrarMovimientoCaja(e) {
    e.preventDefault();
    const m = {
        tipo: document.getElementById("cajaTipo").value,
        concepto: document.getElementById("cajaConcepto").value,
        monto: parseFloat(document.getElementById("cajaMonto").value || 0),
        fecha: new Date().toISOString().replace('T', ' ').substring(0, 16)
    };
    await fetch('/api/caja', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(m)
    });
    document.getElementById("cajaConcepto").value = "";
    document.getElementById("cajaMonto").value = "";
    cargarCaja();
}

// --- FIRMWARES ---
async function cargarFirmwares() {
    const res = await fetch('/api/firmwares');
    const data = await res.json();
    renderFirmwares(data);
}

function renderFirmwares(lista) {
    const tbody = document.getElementById("tablaFirmwaresBody");
    tbody.innerHTML = "";
    lista.forEach(f => {
        const tr = document.createElement("tr");
        tr.className = "border-b border-bordercolor/50 hover:bg-slate-800/50 cursor-pointer";
        tr.onclick = () => {
            document.querySelectorAll("#tablaFirmwaresBody tr").forEach(row => row.classList.remove("bg-slate-800"));
            tr.classList.add("bg-slate-800");
            firmwareSeleccionadoUrl = f.url_archivo;
        };
        tr.innerHTML = `
            <td class="py-2 px-3 text-cyan-400 font-bold">${f.id}</td>
            <td class="py-2 px-3 text-white font-medium">${f.chasis}</td>
            <td class="py-2 px-3 text-slate-300">${f.modelo}</td>
            <td class="py-2 px-3 text-cyan-300">${f.memoria || '-'}</td>
            <td class="py-2 px-3 text-slate-400">${f.tamano || '-'}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function filtrarFirmwares() {
    const q = document.getElementById("buscarFirmwareInput").value.toLowerCase();
    const res = await fetch('/api/firmwares');
    const list = await res.json();
    const filt = list.filter(f =>
        f.chasis.toLowerCase().includes(q) ||
        f.modelo.toLowerCase().includes(q) ||
        (f.memoria && f.memoria.toLowerCase().includes(q))
    );
    renderFirmwares(filt);
}

function descargarFirmwareSeleccionado() {
    if (!firmwareSeleccionadoUrl) return alert("Seleccioná un archivo de la lista de firmwares.");
    window.open(firmwareSeleccionadoUrl, '_blank');
}
