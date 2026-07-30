let ordenes = [
    { id: 1, cliente: "Juan Pérez", equipo: "Smart TV Samsung 55\"", falla: "Sin imagen, tiene sonido", estado: "Ingresado" },
    { id: 2, cliente: "Carlos Gómez", equipo: "PlayStation 5", falla: "Sobrecalentamiento y apague", estado: "En Diagnóstico" }
];

function renderizarOrdenes(lista = ordenes) {
    const container = document.getElementById('ordersContainer');
    container.innerHTML = '';

    lista.forEach(ord => {
        const card = document.createElement('div');
        card.className = "bg-cardbg border border-bordercolor rounded-xl p-5 hover:border-blue-500/50 transition cursor-pointer shadow-lg";
        card.innerHTML = `
            <div class="flex items-center justify-between mb-3">
                <span class="text-xs font-bold text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-md">#${ord.id}</span>
                <span class="text-xs font-medium text-slate-400 bg-slate-800 px-2.5 py-1 rounded-md">${ord.estado}</span>
            </div>
            <h3 class="font-bold text-white text-base mb-1">${ord.equipo}</h3>
            <p class="text-xs text-slate-400 mb-3">Cliente: <span class="text-slate-200 font-medium">${ord.cliente}</span></p>
            <div class="bg-darkbg/50 rounded-lg p-2.5 border border-bordercolor/50">
                <p class="text-xs text-slate-300"><strong>Falla:</strong> ${ord.falla}</p>
            </div>
        `;
        container.appendChild(card);
    });
}

function filtrarOrdenes() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    const filtradas = ordenes.filter(o => 
        o.cliente.toLowerCase().includes(query) || 
        o.equipo.toLowerCase().includes(query) ||
        o.id.toString().includes(query)
    );
    renderizarOrdenes(filtradas);
}

function abrirModalNuevaOrden() {
    document.getElementById('modalNuevaOrden').classList.remove('hidden');
}

function cerrarModalNuevaOrden() {
    document.getElementById('modalNuevaOrden').classList.add('hidden');
}

function guardarOrden(e) {
    e.preventDefault();
    const cliente = document.getElementById('clienteInput').value;
    const equipo = document.getElementById('equipoInput').value;
    const falla = document.getElementById('fallaInput').value;

    const nueva = {
        id: ordenes.length + 1,
        cliente,
        equipo,
        falla,
        estado: "Ingresado"
    };

    ordenes.unshift(nueva);
    renderizarOrdenes();
    cerrarModalNuevaOrden();
    document.getElementById('formNuevaOrden').reset();
}

document.addEventListener('DOMContentLoaded', () => {
    renderizarOrdenes();
});