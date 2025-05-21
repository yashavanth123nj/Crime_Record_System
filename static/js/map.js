// Leaflet.js integration for crime mapping

// Initialize the crime map
function initCrimeMap() {
    // Check if the map container exists
    const mapContainer = document.getElementById('crimeMap');
    if (!mapContainer) return;
    
    // Create map centered at a default location (can be adjusted based on data)
    const map = L.map('crimeMap').setView([40.7128, -74.0060], 12);
    
    // Add the OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
    }).addTo(map);
    
    // Create layer groups for crimes and stations
    const crimeLayer = L.layerGroup().addTo(map);
    const stationLayer = L.layerGroup().addTo(map);
    
    // Define marker icons
    const crimeIcon = L.divIcon({
        html: '<i class="fas fa-exclamation-triangle text-danger" style="font-size: 24px;"></i>',
        className: 'crime-marker-icon',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });
    
    const stationIcon = L.divIcon({
        html: '<i class="fas fa-building text-primary" style="font-size: 24px;"></i>',
        className: 'station-marker-icon',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });
    
    // Function to load crime data
    function loadCrimeData() {
        fetch('/api/crime_data')
            .then(response => response.json())
            .then(crimes => {
                // Clear existing markers
                crimeLayer.clearLayers();
                
                // Array to store all crime coordinates for auto-zoom
                const crimeCoords = [];
                
                // Add crime markers
                crimes.forEach(crime => {
                    const marker = L.marker([crime.lat, crime.lng], {
                        icon: crimeIcon
                    }).addTo(crimeLayer);
                    
                    // Create popup content
                    const popupContent = `
                        <div class="crime-popup">
                            <h6>${crime.type}</h6>
                            <p><strong>Date:</strong> ${crime.date}</p>
                            <p><strong>Time:</strong> ${crime.time || 'Not specified'}</p>
                            <p><strong>Location:</strong> ${crime.location}</p>
                            <p><strong>Status:</strong> <span class="badge bg-${getStatusColor(crime.status)}">${crime.status}</span></p>
                            <a href="/crimes/${crime.id}" class="btn btn-sm btn-primary">View Details</a>
                        </div>
                    `;
                    
                    marker.bindPopup(popupContent);
                    crimeCoords.push([crime.lat, crime.lng]);
                });
                
                // Load police station data after crimes are loaded
                loadStationData(crimeCoords);
            })
            .catch(error => console.error('Error loading crime data:', error));
    }
    
    // Function to load police station data
    function loadStationData(crimeCoords) {
        fetch('/api/station_data')
            .then(response => response.json())
            .then(stations => {
                // Clear existing markers
                stationLayer.clearLayers();
                
                // Add station markers
                stations.forEach(station => {
                    const marker = L.marker([station.lat, station.lng], {
                        icon: stationIcon
                    }).addTo(stationLayer);
                    
                    // Create popup content
                    const popupContent = `
                        <div class="station-popup">
                            <h6>${station.name}</h6>
                            <p><strong>Address:</strong> ${station.address}</p>
                            <p><strong>Contact:</strong> ${station.contact || 'Not available'}</p>
                        </div>
                    `;
                    
                    marker.bindPopup(popupContent);
                    crimeCoords.push([station.lat, station.lng]);
                });
                
                // Auto-zoom if we have coordinates
                if (crimeCoords.length > 0) {
                    const bounds = L.latLngBounds(crimeCoords);
                    map.fitBounds(bounds, { padding: [50, 50] });
                }
            })
            .catch(error => console.error('Error loading station data:', error));
    }
    
    // Helper function to get status color for badge
    function getStatusColor(status) {
        switch (status) {
            case 'reported': return 'secondary';
            case 'investigating': return 'primary';
            case 'solved': return 'success';
            case 'closed': return 'danger';
            default: return 'info';
        }
    }
    
    // Add layer controls
    const overlays = {
        "Crimes": crimeLayer,
        "Police Stations": stationLayer
    };
    
    L.control.layers(null, overlays).addTo(map);
    
    // Load the data
    loadCrimeData();
    
    // Add a legend
    const legend = L.control({ position: 'bottomright' });
    
    legend.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'info legend');
        div.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h6 class="card-title">Legend</h6>
                    <div class="d-flex align-items-center mb-2">
                        <i class="fas fa-exclamation-triangle text-danger me-2"></i>
                        <span>Crime Location</span>
                    </div>
                    <div class="d-flex align-items-center">
                        <i class="fas fa-building text-primary me-2"></i>
                        <span>Police Station</span>
                    </div>
                </div>
            </div>
        `;
        return div;
    };
    
    legend.addTo(map);
}

// Initialize the map when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initCrimeMap();
});
