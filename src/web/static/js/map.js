// Global Abort Controller for map data fetches
let mapLoadController = new AbortController();

/**
 * Function to cancel the current map data loading operation
 */
function cancelMapLoading() {
    console.log("Attempting to cancel map data loading...");
    
    // Abort any pending network requests
    mapLoadController.abort();
    
    // Create a NEW controller for the next time the page is loaded
    mapLoadController = new AbortController();
}


// Get the loading overlay element
const loadingOverlay = document.getElementById('mapLoadingOverlay');
// Initially, the overlay is visible (as there is no .hidden-overlay class in HTML)

const map = L.map('map' , {
    maxBounds: [[-90, -180], [90, 180]],
    maxBoundsViscosity: 1.0,
    minZoom: 3,
    maxZoom: 8
}).setView([37, -95], 4);

// Minimal tiles
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', {
    subdomains: 'abcd',
    maxZoom: 19,
    continuousWorld: false,
    noWrap: true
}).addTo(map);

// Use a promise counter to track both GeoJSON loads
let layersToLoad = 2; // We expect to load countries and states
const checkLoadStatus = () => {
    layersToLoad--;
    if (layersToLoad <= 0) {
        // All layers are loaded, hide the spinner
        loadingOverlay.classList.add('hidden-overlay');
        // Optional: Remove the element from the DOM after transition for maximum cleanup
        setTimeout(() => {
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
        }, 300); // 300ms matches the CSS transition time
    }
};

// Get the abort signal
const signal = mapLoadController.signal;

fetch('/locations_summary')
    .then(r => r.json())
    .then(data => {
        const visitedCountries = data.countries || [];
        const visitedStates = data.us_states || [];
        const countriesColors = data.countries_colors || {};
        const statesColors = data.states_colors || {};
        const countriesCounts = data.countries_counts || {};
        const statesCounts = data.states_counts || {};

        // Helper to darken color based on number of IPs
        function darkenColor(hex, factor) {
            const rgb = hex.match(/\w\w/g).map(x => parseInt(x,16));
            rgb[0] = Math.max(0, rgb[0] - factor);
            rgb[1] = Math.max(0, rgb[1] - factor);
            rgb[2] = Math.max(0, rgb[2] - factor);
            return "#" + rgb.map(x => x.toString(16).padStart(2,'0')).join('');
        }

        // Draw countries
        // PASS SIGNAL TO FETCH
        fetch('/static/dependencies/countries.geojson', { signal })
            .then(r => r.json())
            .then(worldGeojson => {
                L.geoJSON(worldGeojson, {
                    style: f => {
                        const name = f.properties.name;
                        const baseColor = countriesColors[name] || "#cccccc";
                        const count = countriesCounts[name] || 0;
                        const fill = baseColor;
                        return {
                            fillColor: fill,
                            color: "transparent",
                            weight: 0,
                            fillOpacity: count > 0 ? 0.7 : 0.2
                        };
                    },
                    onEachFeature: (feature, layer) => {
                        const name = feature.properties.name;
                        const count = countriesCounts[name] || 0;
                        if (count > 0) {
                            const center = data.countries_centers[name];
                            if (center) {
                                L.tooltip({
                                    permanent: true,
                                    direction: 'center',
                                    className: 'territory-label'
                                })
                                .setLatLng(center)
                                .setContent(`${count}`)
                                .addTo(map);
                            }
                        }
                    }
                }).addTo(map);
                
                // CALL CHECK STATUS 1: Countries loaded
                checkLoadStatus(); 
            })
            .catch(err => {
                if (err.name !== 'AbortError') {
                    console.error("Error loading countries GeoJSON:", err);
                } else {
                    console.log("Countries GeoJSON load cancelled.");
                }
                // Call check status even on error to prevent infinite spin
                checkLoadStatus(); 
            });

        // Draw US states
        // PASS SIGNAL TO FETCH
        fetch('/static/dependencies/states.json', { signal })
            .then(r => r.json())
            .then(usStatesGeojson => {
                L.geoJSON(usStatesGeojson, {
                    style: f => {
                        const name = f.properties.NAME;
                        const baseColor = statesColors[name] || "#dddddd";
                        const count = statesCounts[name] || 0;
                        const fill = baseColor;
                        return {
                            fillColor: fill,
                            color: "transparent",
                            weight: 0,
                            fillOpacity: count > 0 ? 0.7 : 0.3
                        };
                    },
                    onEachFeature: (feature, layer) => {
                        const name = feature.properties.NAME;
                        const count = statesCounts[name] || 0;
                        if (count > 0) {
                            const center = data.states_centers[name];
                            if (center) {
                                L.tooltip({
                                    permanent: true,
                                    direction: 'center',
                                    className: 'territory-label'
                                })
                                .setLatLng(center)
                                .setContent(`${count}`)
                                .addTo(map);
                            }
                        }
                    }
                }).addTo(map);
                
                // CALL CHECK STATUS 2: States loaded
                checkLoadStatus(); 
            })
            .catch(err => {
                if (err.name !== 'AbortError') {
                    console.error("Error loading states GeoJSON:", err);
                } else {
                    console.log("States GeoJSON load cancelled.");
                }
                // Call check status even on error to prevent infinite spin
                checkLoadStatus();
            });
    })
    .catch(err => {
        if (err.name !== 'AbortError') {
            console.error("Error loading map data summary:", err);
        } else {
            console.log("Map data summary fetch cancelled.");
        }
        
        // If the initial data load fails or is cancelled, hide the spinner
        layersToLoad = 0; // Ensure it hides immediately
        loadingOverlay.classList.add('hidden-overlay');
        setTimeout(() => {
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
        }, 300);
    });

// -----------------------------------------------------------------
// BACK BUTTON LISTENER
// -----------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    const backBtn = document.querySelector('.back-btn');

    if (backBtn) {
        backBtn.addEventListener('click', (event) => {
            // 1. Prevent the default navigation immediately
            event.preventDefault(); 
            
            // 2. Cancel the current map loading process
            cancelMapLoading();
            
            // 3. Immediately redirect the browser to the desired endpoint
            window.location.href = backBtn.href; 
        });
    }
});