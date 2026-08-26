// ==========================================================================
// Vitalis Fitness - HD Interactive Canvas Charts (Line & Donut)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    initCharts();

    // Re-render on window resize with debounce
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(initCharts, 150);
    });

    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-6px)';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // Notification Center Dropdown
    const notifToggle = document.getElementById('notifDropdownToggle');
    const notifMenu = document.getElementById('notifDropdownMenu');

    if (notifToggle && notifMenu) {
        notifToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            notifMenu.classList.toggle('show');
        });

        document.addEventListener('click', (e) => {
            if (!notifMenu.contains(e.target) && !notifToggle.contains(e.target)) {
                notifMenu.classList.remove('show');
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                notifMenu.classList.remove('show');
            }
        });
    }
});

function initCharts() {
    const revenueCanvas = document.getElementById('revenueChart');
    if (revenueCanvas) {
        renderRevenueChart(revenueCanvas);
    }

    const plansCanvas = document.getElementById('plansDonutChart');
    if (plansCanvas) {
        renderPlansDonutChart(plansCanvas);
    }
}

/**
 * Gráfico de Tendencia de Ingresos (Curva Suavizada HD con Área y Glow)
 */
function renderRevenueChart(canvas) {
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 2;
    
    // Obtener dimensiones reales del contenedor
    const container = canvas.parentElement;
    const width = container.clientWidth;
    const height = container.clientHeight || 230;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    
    ctx.resetTransform ? ctx.resetTransform() : ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);

    const padding = { top: 25, right: 30, bottom: 35, left: 30 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    // Curva exacta del diseño Figma:
    // Ene suave -> sube -> baja Feb -> sube Mar/Abr -> baja suave Jun -> Pico Jul (con punto blanco) -> Ago baja -> subida continua hacia Dic
    const values = [30, 36, 32, 44, 52, 46, 68, 60, 68, 78, 90, 102];
    const minVal = 10;
    const maxVal = 115;

    // 1. Dibujar líneas de cuadrícula horizontales muy sutiles
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
    ctx.lineWidth = 1;
    const gridLines = 4;
    for (let i = 0; i <= gridLines; i++) {
        const y = padding.top + (chartH / gridLines) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();
    }

    // 2. Calcular coordenadas exactas de cada mes
    const points = values.map((val, i) => {
        const x = padding.left + (chartW / (values.length - 1)) * i;
        const y = padding.top + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;
        return { x, y, val, month: months[i] };
    });

    // 3. Crear y rellenar el Área de Gradiente Dorado
    const gradient = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartH);
    gradient.addColorStop(0, 'rgba(245, 184, 46, 0.22)');
    gradient.addColorStop(0.6, 'rgba(245, 184, 46, 0.06)');
    gradient.addColorStop(1, 'rgba(245, 184, 46, 0.00)');

    ctx.beginPath();
    ctx.moveTo(points[0].x, padding.top + chartH);
    ctx.lineTo(points[0].x, points[0].y);

    // Curva Catmull-Rom / Bézier para suavizado óptico
    for (let i = 0; i < points.length - 1; i++) {
        const p0 = (i > 0) ? points[i - 1] : points[0];
        const p1 = points[i];
        const p2 = points[i + 1];
        const p3 = (i != points.length - 2) ? points[i + 2] : p2;

        const cp1x = p1.x + (p2.x - p0.x) / 6;
        const cp1y = p1.y + (p2.y - p0.y) / 6;
        const cp2x = p2.x - (p3.x - p1.x) / 6;
        const cp2y = p2.y - (p3.y - p1.y) / 6;

        ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
    }

    ctx.lineTo(points[points.length - 1].x, padding.top + chartH);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // 4. Dibujar Trazo de Línea Dorada (Glow)
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);

    for (let i = 0; i < points.length - 1; i++) {
        const p0 = (i > 0) ? points[i - 1] : points[0];
        const p1 = points[i];
        const p2 = points[i + 1];
        const p3 = (i != points.length - 2) ? points[i + 2] : p2;

        const cp1x = p1.x + (p2.x - p0.x) / 6;
        const cp1y = p1.y + (p2.y - p0.y) / 6;
        const cp2x = p2.x - (p3.x - p1.x) / 6;
        const cp2y = p2.y - (p3.y - p1.y) / 6;

        ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
    }

    ctx.strokeStyle = '#f5b82e';
    ctx.lineWidth = 2.5;
    ctx.shadowColor = 'rgba(245, 184, 46, 0.5)';
    ctx.shadowBlur = 12;
    ctx.stroke();
    ctx.shadowBlur = 0; // reset shadow

    // 5. Punto destacado en el mes actual (Jul / index 6)
    const hlIdx = 6;
    const hl = points[hlIdx];

    // Glow exterior
    ctx.beginPath();
    ctx.arc(hl.x, hl.y, 8, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(245, 184, 46, 0.25)';
    ctx.fill();

    // Círculo blanco brillante
    ctx.beginPath();
    ctx.arc(hl.x, hl.y, 5, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.shadowColor = 'rgba(245, 184, 46, 0.8)';
    ctx.shadowBlur = 10;
    ctx.fill();
    ctx.shadowBlur = 0;

    // Núcleo central oro
    ctx.beginPath();
    ctx.arc(hl.x, hl.y, 2.5, 0, Math.PI * 2);
    ctx.fillStyle = '#f5b82e';
    ctx.fill();

    // 6. Etiquetas de Meses (Distribuidas a lo ancho de todo el contenedor)
    ctx.fillStyle = '#64748b';
    ctx.font = '500 11px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    points.forEach((pt, idx) => {
        // Si es el mes activo, destacar en color dorado claro
        if (idx === hlIdx) {
            ctx.fillStyle = '#e2e8f0';
            ctx.font = '600 11px Inter, sans-serif';
        } else {
            ctx.fillStyle = '#64748b';
            ctx.font = '500 11px Inter, sans-serif';
        }
        ctx.fillText(pt.month, pt.x, height - 12);
    });
}

/**
 * Gráfico Donut de Distribución de Planes
 */
function renderPlansDonutChart(canvas) {
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 2;
    
    const container = canvas.parentElement;
    const width = container.clientWidth || 160;
    const height = container.clientHeight || 160;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';

    ctx.resetTransform ? ctx.resetTransform() : ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);

    const centerX = width / 2;
    const centerY = height / 2;
    const outerRadius = Math.min(centerX, centerY) - 6;
    const innerRadius = outerRadius - 13;

    // Datos idénticos a Figma: Black Pass VIP (55%), Membresía Studio (28%), Pase Estándar (17%)
    const segments = [
        { percentage: 55, color: '#f5b82e', glow: true },   // Gold
        { percentage: 28, color: '#e2e8f0', glow: false },  // Platinum White
        { percentage: 17, color: '#334155', glow: false }   // Dark Slate
    ];

    // Comenzamos desde la derecha superior (~ -35deg para que coincida con el arco de Figma)
    let startAngle = -Math.PI * 0.15;
    const gapAngle = 0.045; // Separación estética limpia entre arcos

    segments.forEach(seg => {
        const sliceAngle = (seg.percentage / 100) * (Math.PI * 2);
        const endAngle = startAngle + sliceAngle - gapAngle;

        ctx.beginPath();
        ctx.arc(centerX, centerY, outerRadius, startAngle, endAngle);
        ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true);
        ctx.closePath();

        if (seg.glow) {
            ctx.shadowColor = 'rgba(245, 184, 46, 0.4)';
            ctx.shadowBlur = 10;
        } else {
            ctx.shadowBlur = 0;
        }

        ctx.fillStyle = seg.color;
        ctx.fill();
        ctx.shadowBlur = 0;

        startAngle += sliceAngle;
    });
}
