let ordenes = [
    { id: 1, cliente: "Juan Pérez", equipo: "Smart TV Samsung 55\"", falla: "Sin imagen, tiene sonido", estado: "Ingresado" },
    { id: 2, cliente: "Carlos Gómez", equipo: "PlayStation 5", falla: "Sobrecalentamiento y apague", estado: "En Diagnóstico" }
];

let clientes = [
    { id: 1, nombre: "Juan Pérez", telefono: "11-4433-2211", direccion: "Burzaco", equipos: 1 },
    { id: 2, nombre: "Carlos Gómez", telefono: "11-5566-7788", direccion: "Claypole", equipos: 1 }
];

let repuestos = [
    { id: 1, nombre: "Tira LED Samsung 55 UN55TU7000", cantidad: 4, precio: 18500 },
    { id: 2, nombre: "CI Fuente PWM FAN6754", cantidad: 12, precio: 2200 }
];

let movimientosCaja = [
    { id: 1, tipo: "ingreso", concepto: "Seña Orden #1 - Smart TV Samsung", monto: 15000, fecha: "2026-07-31" },
    { id: 2, tipo: "egreso", concepto: "Compra LEDs Samsung 55", monto: 8500, fecha: "2026-07-31" }
];

document.addEventListener("DOMContentLoaded", () => {
    renderizarOrdenes(ordenes);
    actualizarBalanceCaja();
});

function cambiarVista(vista) {
    const vistas = ['vistaOrdenes', 'vistaClientes', 'vistaStock', 'vistaCaja'];
    vistas.forEach(v => {
        const el = document.getElementById(v);
        if (el) el.classList.add("hidden");
    });

    if (vista === 'ordenes') {
        document.getElementById("vistaOrdenes").classList.remove("hidden");
        renderizarOrdenes(ordenes);
    } else if (vista === 'clientes') {
        document.getElementById("vistaClientes").classList.remove("hidden");
        renderizarClientes();
    } else if (vista === 'stock') {
        document.getElementById("vistaStock").classList.remove("hidden");
        renderizarStock();
    } else if (vista === 'caja') {
        document.getElementById("vistaCaja").classList.remove("hidden");
        renderizarMovimientosCaja();
    }
}

// --- ÓRDENES ---
function renderizarOrdenes(lista) {
    const container = document.getElementById("ordersContainer");
    if (!container) return;
    container.innerHTML = "";

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

function guardarOrden(e) {
    e.preventDefault();
    const cliente = document.getElementById("clienteInput").value;
    const equipo = document.getElementById("equipoInput").value;
    const falla = document.getElementById("fallaInput").value;

    const nueva = {
        id: ordenes.length + 1,
        cliente: cliente,
        equipo: equipo,
        falla: falla,
        estado: "Ingresado"
    };

    ordenes.unshift(nueva);
    renderizarOrdenes(ordenes);
    cerrarModal('modalNuevaOrden');
    document.getElementById("formNuevaOrden").reset();
}

function filtrarOrdenes() {
    const query = document.getElementById("searchInput").value.toLowerCase();
    const filtradas = ordenes.filter(o => 
        o.cliente.toLowerCase().includes(query) ||
        o.equipo.toLowerCase().includes(query) ||
        o.id.toString().includes(query)
    );
    renderizarOrdenes(filtradas);
}

// --- CLIENTES ---
function renderizarClientes() {
    const container = document.getElementById("tablaClientes");
    if (!container) return;
    container.innerHTML = "";

    clientes.forEach(c => {
        const row = document.createElement("tr");
        row.className = "border-b border-bordercolor/50 text-sm";
        row.innerHTML = `
            <td class="py-3 px-4 text-white font-medium">${c.nombre}</td>
            <td class="py-3 px-4 text-slate-400">${c.telefono}</td>
            <td class="py-3 px-4 text-slate-400">${c.direccion}</td>
            <td class="py-3 px-4 text-blue-400 font-bold">${c.equipos} equipo(s)</td>
        `;
        container.appendChild(row);
    });
}

function guardarCliente(e) {
    e.preventDefault();
    const nombre = document.getElementById("clienteNombreInput").value;
    const telefono = document.getElementById("clienteTelInput").value;
    const direccion = document.getElementById("clienteDirInput").value;

    clientes.unshift({
        id: clientes.length + 1,
        nombre: nombre,
        telefono: telefono,
        direccion: direccion,
        equipos: 0
    });

    renderizarClientes();
    cerrarModal('modalNuevoCliente');
    document.getElementById("formNuevoCliente").reset();
}

// --- STOCK / REPUESTOS ---
function renderizarStock() {
    const container = document.getElementById("tablaStock");
    if (!container) return;
    container.innerHTML = "";

    repuestos.forEach(r => {
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

function guardarRepuesto(e) {
    e.preventDefault();
    const nombre = document.getElementById("repuestoNombreInput").value;
    const cantidad = parseInt(document.getElementById("repuestoCantInput").value);
    const precio = parseFloat(document.getElementById("repuestoPrecioInput").value);

    repuestos.unshift({
        id: repuestos.length + 1,
        nombre: nombre,
        cantidad: cantidad,
        precio: precio
    });

    renderizarStock();
    cerrarModal('modalNuevoRepuesto');
    document.getElementById("formNuevoRepuesto").reset();
}

// --- CAJA Y BALANCE ---
function actualizarBalanceCaja() {
    let ingresos = 0;
    let egresos = 0;

    movimientosCaja.forEach(m => {
        if (m.tipo === "ingreso") ingresos += m.monto;
        if (m.tipo === "egreso") egresos += m.monto;
    });

    const totalIngresosEl = document.getElementById("totalIngresos");
    const totalEgresosEl = document.getElementById("totalEgresos");
    const saldoTotalEl = document.getElementById("saldoTotal");

    if (totalIngresosEl) totalIngresosEl.innerText = `$${ingresos.toLocaleString()}`;
    if (totalEgresosEl) totalEgresosEl.innerText = `$${egresos.toLocaleString()}`;
    if (saldoTotalEl) saldoTotalEl.innerText = `$${(ingresos - egresos).toLocaleString()}`;
}

function renderizarMovimientosCaja() {
    const container = document.getElementById("tablaMovimientos");
    if (!container) return;
    container.innerHTML = "";

    movimientosCaja.forEach(m => {
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

    actualizarBalanceCaja();
}

function guardarMovimientoCaja(e) {
    e.preventDefault();
    const concepto = document.getElementById("conceptoInput").value;
    const monto = parseFloat(document.getElementById("montoInput").value);
    const tipo = document.getElementById("tipoInput").value;

    movimientosCaja.unshift({
        id: movimientosCaja.length + 1,
        tipo: tipo,
        concepto: concepto,
        monto: monto,
        fecha: new Date().toISOString().split('T')[0]
    });

    renderizarMovimientosCaja();
    cerrarModal('modalNuevoMovimiento');
    document.getElementById("formNuevoMovimiento").reset();
}

// --- MODALES ---
function abrirModal(id) {
    document.getElementById(id).classList.remove("hidden");
}

function cerrarModal(id) {
    document.getElementById(id).classList.add("hidden");
}

function abrirModalNuevaOrden() { abrirModal('modalNuevaOrden'); }
function cerrarModalNuevaOrden() { cerrarModal('modalNuevaOrden'); }
function abrirModalMovimiento() { abrirModal('modalNuevoMovimiento'); }
function cerrarModalMovimiento() { cerrarModal('modalNuevoMovimiento'); }