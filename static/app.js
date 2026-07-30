let allOrders = [];

document.addEventListener("DOMContentLoaded", () => {
    fetchOrders();
});

async function fetchOrders() {
    try {
        const response = await fetch('/api/v1/ordenes');
        if (!response.ok) throw new Error("Error al consultar API");
        allOrders = await response.json();
        renderOrders(allOrders);
    } catch (error) {
        document.getElementById("ordersContainer").innerHTML = `
            <div class="bg-white p-6 rounded-xl border border-slate-200 text-center text-slate-500 text-sm">
                Conectado al servidor. Listo para sincronizar órdenes.
            </div>`;
    }
}

function renderOrders(orders) {
    const container = document.getElementById("ordersContainer");
    if (!orders || orders.length === 0) {
        container.innerHTML = `
            <div class="bg-white p-8 rounded-xl border border-slate-200 text-center text-slate-500 text-sm">
                No hay órdenes ingresadas aún en la base de datos.
            </div>`;
        return;
    }

    container.innerHTML = orders.map(order => `
        <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex justify-between items-center">
            <div>
                <span class="font-bold text-slate-900">#${order.id || 'N/A'}</span> - 
                <span class="font-semibold text-slate-800">${order.equipo || 'Sin equipo'}</span>
                <p class="text-sm text-slate-500">${order.cliente || 'Cliente no asignado'}</p>
            </div>
            <span class="px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                ${order.estado || 'INGRESADO'}
            </span>
        </div>
    `).join('');
}