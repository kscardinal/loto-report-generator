const map = L.map('map' , {
    maxBounds: [[-90, -180], [90, 180]],
    maxBoundsViscosity: 1.0,
    minZoom: 3,
    maxZoom: 6
}).setView([37, -95], 4);

// Minimal tiles
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', {
    subdomains: 'abcd',
    maxZoom: 19,
    continuousWorld: false,
    noWrap: true
}).addTo(map);

fetch('/locations_summary')
.then(r => r.json())
.then(data => {
    const visitedCountries = data.countries || [];
    const visitedStates = data.us_states || [];
    const countriesColors = data.countries_colors || {};
    const statesColors = data.states_colors || {};

    // WORLD COUNTRIES
    fetch('/static/dependencies/countries.geojson')
    .then(r => r.json())
    .then(worldGeojson => {
        L.geoJSON(worldGeojson, {
        style: f => ({
            fillColor: countriesColors[f.properties.name] || "#cccccc",
            color: "transparent",
            weight: 0,
            fillOpacity: countriesColors[f.properties.name] ? 0.7 : 0.2
        }),
        onEachFeature: () => {}
        }).addTo(map);
    });

    // U.S. STATES
    fetch('/static/dependencies/states.json')
    .then(r => r.json())
    .then(usStatesGeojson => {
        L.geoJSON(usStatesGeojson, {
        style: f => ({
            fillColor: statesColors[f.properties.NAME] || "#dddddd",
            color: "transparent",
            weight: 0,
            fillOpacity: statesColors[f.properties.NAME] ? 0.7 : 0.3
        }),
        onEachFeature: () => {}
        }).addTo(map);
    });
});