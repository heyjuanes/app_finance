// Configuración - ACTUALIZAR CON TU IP REAL
const API_URL = 'http://192.168.1.13:8000';

// Estado global
let currentTab = 'dashboard';
let isOnline = true;

// Detectar cambios de conexión
window.addEventListener('online', () => {
    isOnline = true;
    removeOfflineBanner();
    if (currentTab === 'dashboard') loadDashboard();
    if (currentTab === 'transacciones') loadTransacciones();
});

window.addEventListener('offline', () => {
    isOnline = false;
    showOfflineBanner();
    showErrorInContent('Sin conexión a internet. Verifica tu red y que la API esté corriendo.');
});

// Mostrar banner de offline
function showOfflineBanner() {
    if (document.getElementById('offline-banner')) return;
    const banner = document.createElement('div');
    banner.id = 'offline-banner';
    banner.className = 'offline-banner';
    banner.innerHTML = '📡 Sin conexión al servidor - Verifica que la API esté corriendo';
    const container = document.querySelector('.app-container');
    container.insertBefore(banner, container.firstChild);
}

function removeOfflineBanner() {
    const banner = document.getElementById('offline-banner');
    if (banner) banner.remove();
}

// Mostrar error en el contenido
function showErrorInContent(message) {
    document.getElementById('dashboard-content').innerHTML = `
        <div class="error">
            <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
            <p>${message}</p>
            <button class="retry-btn" onclick="window.location.reload()">Reintentar</button>
        </div>
    `;
}

// Función para formatear dinero COP
function formatCOP(monto) {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(monto);
}

// Fetch con manejo de errores
async function fetchAPI(endpoint, options = {}) {
    if (!isOnline) {
        throw new Error('Sin conexión a internet');
    }
    
    try {
        const response = await fetch(`${API_URL}${endpoint}`, options);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error en la petición');
        }
        return await response.json();
    } catch (error) {
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            isOnline = false;
            showOfflineBanner();
            throw new Error('No se pudo conectar al servidor. ¿La API está corriendo?');
        }
        throw error;
    }
}

// Cargar Dashboard
async function loadDashboard() {
    try {
        const data = await fetchAPI('/dashboard');
        removeOfflineBanner();
        isOnline = true;
        
        const html = `
            <div class="hero-card">
                <div class="hero-label">fondo migratorio</div>
                <div class="hero-amount">${formatCOP(data.fondo_migratorio)}</div>
                <div class="hero-sub">meta: ${formatCOP(data.meta_total)}</div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: ${data.progreso}%"></div>
                </div>
                <div class="progress-meta">
                    <span>${data.progreso}% alcanzado</span>
                    <span>estimado: ${data.dias_restantes} días</span>
                </div>
            </div>
            
            <div class="semaforo-row">
                <div class="semaforo-pill">
                    <div class="dot ${data.semaforo.estado}"></div>
                    ${data.semaforo.mensaje}
                </div>
                <div class="day-count">${data.dias_restantes} días</div>
            </div>
            
            <div class="section-label">bolsillos</div>
            <div class="pockets-grid">
                ${data.bolsillos.map(b => `
                    <div class="pocket ${b.nombre === 'Migración' ? 'accent' : ''}">
                        <div class="pocket-name">${b.nombre.toLowerCase()}</div>
                        <div class="pocket-amount">${formatCOP(b.monto)}</div>
                        <div class="pocket-pct">${b.porcentaje}% del ingreso</div>
                    </div>
                `).join('')}
            </div>
            
            <div class="section-label">inversión cdt</div>
            <div class="cdt-card">
                <div class="cdt-left">
                    <div class="cdt-tag">CDT digital · bloqueado</div>
                    <div class="cdt-amount">${formatCOP(data.cdt.capital)}</div>
                </div>
                <div class="cdt-right">
                    <div class="cdt-rate">${data.cdt.tasa}% E.A.</div>
                    <div class="cdt-venc">+${formatCOP(data.cdt.interes_proyectado)} interés</div>
                </div>
            </div>
            
            <div class="section-label">proyección</div>
            <div class="scenario-row">
                <div class="sc-card">
                    <div class="sc-label">conservador</div>
                    <div class="sc-val">${data.proyeccion_escenarios.conservador} meses</div>
                </div>
                <div class="sc-card best">
                    <div class="sc-label">actual</div>
                    <div class="sc-val">${data.proyeccion_escenarios.actual} meses</div>
                </div>
                <div class="sc-card">
                    <div class="sc-label">óptimo</div>
                    <div class="sc-val">${data.proyeccion_escenarios.optimo} meses</div>
                </div>
            </div>
            
            <div class="action-row">
                <div class="action-btn" onclick="openModal('ingreso')">
                    <div class="action-btn-icon">↑</div>
                    <div class="action-btn-label">ingreso</div>
                </div>
                <div class="action-btn" onclick="openModal('gasto')">
                    <div class="action-btn-icon">↓</div>
                    <div class="action-btn-label">gasto</div>
                </div>
                <div class="action-btn" onclick="openCDTModal()">
                    <div class="action-btn-icon">⊕</div>
                    <div class="action-btn-label">cdt</div>
                </div>
            </div>
        `;
        
        document.getElementById('dashboard-content').innerHTML = html;
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showErrorInContent(error.message);
    }
}

// Cargar transacciones
async function loadTransacciones() {
    try {
        const data = await fetchAPI('/transacciones?limite=50');
        removeOfflineBanner();
        
        if (data.length === 0) {
            document.getElementById('dashboard-content').innerHTML = `
                <div class="loading">
                    <p>📭 No hay transacciones aún</p>
                    <p style="font-size: 13px; margin-top: 8px;">Registra tu primer ingreso o gasto</p>
                </div>
            `;
            return;
        }
        
        const html = `
            <div class="section-label">últimas transacciones</div>
            ${data.map(t => `
                <div class="transaccion-item transaccion-${t.tipo}">
                    <div>
                        <div class="transaccion-desc">${t.descripcion || (t.tipo === 'ingreso' ? 'Ingreso registrado' : `Gasto de ${t.bolsillo}`)}</div>
                        <div class="transaccion-fecha">${new Date(t.fecha).toLocaleString('es-CO')}</div>
                    </div>
                    <div class="transaccion-monto">
                        ${t.tipo === 'ingreso' ? '+' : '-'} ${formatCOP(t.monto)}
                    </div>
                </div>
            `).join('')}
        `;
        
        document.getElementById('dashboard-content').innerHTML = html;
    } catch (error) {
        console.error('Error loading transacciones:', error);
        showErrorInContent(error.message);
    }
}

// Modal para ingreso/gasto
const modal = document.getElementById('modal');
const closeBtn = document.querySelector('.close');
let transactionType = '';

function openModal(type) {
    transactionType = type;
    const modalTitle = document.getElementById('modal-title');
    const bolsilloSelect = document.getElementById('bolsillo');
    
    if (type === 'ingreso') {
        modalTitle.textContent = 'Registrar Ingreso';
        bolsilloSelect.style.display = 'none';
    } else {
        modalTitle.textContent = 'Registrar Gasto';
        bolsilloSelect.style.display = 'block';
    }
    
    modal.style.display = 'block';
}

closeBtn.onclick = function() {
    modal.style.display = 'none';
}

window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}

// Enviar formulario
document.getElementById('transaction-form').onsubmit = async function(e) {
    e.preventDefault();
    
    const monto = parseInt(document.getElementById('monto').value);
    const descripcion = document.getElementById('descripcion').value;
    const bolsillo = document.getElementById('bolsillo').value;
    
    if (isNaN(monto) || monto <= 0) {
        alert('Por favor ingresa un monto válido');
        return;
    }
    
    try {
        if (transactionType === 'ingreso') {
            await fetchAPI('/ingreso', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ monto, descripcion })
            });
            alert('✅ Ingreso registrado exitosamente');
        } else {
            await fetchAPI('/gasto', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bolsillo, monto, descripcion })
            });
            alert('✅ Gasto registrado exitosamente');
        }
        
        modal.style.display = 'none';
        document.getElementById('transaction-form').reset();
        
        if (currentTab === 'dashboard') {
            loadDashboard();
        } else if (currentTab === 'transacciones') {
            loadTransacciones();
        }
    } catch (error) {
        alert(`❌ Error: ${error.message}`);
    }
}

// Modal para CDT
function openCDTModal() {
    const capital = prompt('Capital a invertir en CDT (COP):');
    if (!capital) return;
    
    const tasa = prompt('Tasa de interés anual (%):', '12.4');
    if (!tasa) return;
    
    const meses = prompt('Plazo en meses:', '12');
    if (!meses) return;
    
    fetchAPI(`/cdt?capital=${parseInt(capital)}&tasa=${parseFloat(tasa)}&meses=${parseInt(meses)}`, {
        method: 'POST'
    })
    .then(() => {
        alert(`✅ CDT creado exitosamente\nCapital: ${formatCOP(parseInt(capital))}\nTasa: ${tasa}% E.A.\nPlazo: ${meses} meses`);
        loadDashboard();
    })
    .catch(error => {
        alert(`❌ Error: ${error.message}`);
    });
}

// Navegación por tabs
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', async () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        const tabName = tab.dataset.tab;
        currentTab = tabName;
        
        if (tabName === 'dashboard') {
            loadDashboard();
        } else if (tabName === 'transacciones') {
            loadTransacciones();
        } else if (tabName === 'cdt') {
            document.getElementById('dashboard-content').innerHTML = `
                <div class="loading">
                    <p>🏦 Sección de CDT</p>
                    <p style="font-size: 13px; margin-top: 8px;">Presiona el botón ⊕ para crear un nuevo CDT</p>
                </div>
                <div class="action-row">
                    <div class="action-btn" onclick="openCDTModal()">
                        <div class="action-btn-icon">⊕</div>
                        <div class="action-btn-label">nuevo cdt</div>
                    </div>
                </div>
            `;
        } else if (tabName === 'config') {
            document.getElementById('dashboard-content').innerHTML = `
                <div class="loading">
                    <p>⚙️ Configuración</p>
                    <p style="font-size: 13px; margin-top: 8px;">Próximamente: editar meta, porcentajes y más</p>
                </div>
            `;
        }
    });
});

// Inicializar
loadDashboard();