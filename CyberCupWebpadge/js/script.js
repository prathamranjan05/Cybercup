// --- FETCH WATERLOGGED DATA AND UPDATE MAP ---
let map, waterLayer, pulseLayer, alertChart;

document.addEventListener("DOMContentLoaded", function() {
    // Initialize map if #map exists
    const mapElement = document.getElementById('map');
    if (mapElement) {
        map = L.map('map', { zoomControl: false }).setView([28.6139, 77.2090], 11); // Delhi coordinates
        L.control.zoom({ position: 'bottomright' }).addTo(map);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        waterLayer = L.layerGroup().addTo(map);
        pulseLayer = L.layerGroup().addTo(map);

        initializeChart();
        updateDashboard();
        setInterval(updateDashboard, 10000); // refresh every 10s
    }

    async function updateDashboard() {
        try {
            const response = await fetch('/api/waterlogged');
            if (!response.ok) throw new Error('Failed to fetch waterlogged data');
            const data = await response.json();

            waterLayer.clearLayers();
            pulseLayer.clearLayers();

            const alertContainer = document.getElementById('alert-container');
            if (alertContainer) alertContainer.innerHTML = '';

            let dangerCount = 0, warningCount = 0;
            const dangerPoints = [];

            data.forEach(point => {
                const level = point.status;
                const color = level === 'danger' ? '#e74c3c' : (level === 'warning' ? '#f39c12' : '#2ecc71');

                // Draw main circle
                L.circleMarker([point.lat, point.lon], {
                    radius: 6 + point.water_level * 4,
                    color: '#fff',
                    weight: 1,
                    fillColor: color,
                    fillOpacity: 0.8
                }).addTo(waterLayer)
                  .bindPopup(`<b>Sensor ${point.id}</b><br/>Water Level: <b>${point.water_level.toFixed(2)} m</b>`);

                // Add pulse for danger
                if (level === 'danger') {
                    const pulseIcon = L.divIcon({ className: 'leaflet-marker-pulse', html: '<div class="pulse"></div>' });
                    L.marker([point.lat, point.lon], { icon: pulseIcon }).addTo(pulseLayer);
                    dangerCount++;
                    dangerPoints.push([point.lat, point.lon]);
                } else if (level === 'warning') {
                    warningCount++;
                }

                // Add alerts
                if (level === 'danger' || level === 'warning') {
                    const alertElement = document.createElement('div');
                    alertElement.className = `alert alert-${level}`;
                    alertElement.innerHTML = `
                        <h4>${level.toUpperCase()} ALERT</h4>
                        <p>Sensor ID: ${point.id}</p>
                        <p>Water Level: <strong>${point.water_level.toFixed(2)} m</strong></p>
                    `;
                    alertElement.addEventListener('click', () => map.setView([point.lat, point.lon], 15));
                    if (alertContainer) alertContainer.appendChild(alertElement);
                }
            });

            // Center map to danger/warning points if any
            if (dangerPoints.length > 0) {
                const group = L.featureGroup(dangerPoints.map(p => L.marker(p)));
                map.fitBounds(group.getBounds().pad(0.5));
            }

            // Update chart
            if (alertChart) {
                alertChart.data.datasets[0].data = [dangerCount, warningCount, data.length - (dangerCount + warningCount)];
                alertChart.update();
            }

            // All Clear message
            if (dangerCount === 0 && warningCount === 0 && alertContainer) {
                alertContainer.innerHTML = '<div class="alert alert-info"><h4>All Clear</h4><p>No critical waterlogging detected.</p></div>';
            }

        } catch (err) {
            console.error("Error updating dashboard:", err);
        }
    }

    function initializeChart() {
        const ctx = document.getElementById('alert-chart');
        if (!ctx) return;
        alertChart = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Danger', 'Warning', 'Safe'],
                datasets: [{
                    label: 'Alert Levels',
                    data: [0, 0, 1],
                    backgroundColor: ['#e74c3c', '#f39c12', '#2ecc71'],
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        });
    }// --- Theme Toggle ---
const themeToggle = document.getElementById('theme-toggle');
if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
}

// --- Intersection Animations ---
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible-anim');
        }
    });
}, { threshold: 0.1 });
document.querySelectorAll('.hidden-anim').forEach(el => observer.observe(el));

// --- Map Initialization ---
// let map; // Already declared above
// const mapElement = document.getElementById('map'); // Already declared above
if (mapElement) {
    // Only initialize if not already initialized
    if (!map) {
        map = L.map('map').setView([26.8467, 80.9462], 12); // Default coordinates

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
    }
}

// --- Fetch Waterlogged Data ---
async function fetchWaterData() {
    try {
        const response = await fetch('/api/waterlogged');
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();

        if (map) {
            data.forEach(point => {
                const pulseIcon = L.divIcon({ className: 'leaflet-marker-pulse', html: '<div class="pulse"></div>' });
                L.marker([point.lat, point.lng], { icon: pulseIcon }).addTo(map).bindPopup(`<strong>${point.location}</strong><br>Level: ${point.level}`);
            });
        }
    } catch (err) {
        console.error('Failed to fetch waterlogged data:', err);
    }
}

// Call fetchWaterData if map exists
if (map) fetchWaterData();

});
