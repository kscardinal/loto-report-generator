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
        fetch('/static/dependencies/countries.geojson')
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
                            const center = data.countries_centers[name];  // <-- Use center from locations_summary
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
            });

        // Draw US states
        fetch('/static/dependencies/states.json')
            .then(r => r.json())
            .then(usStatesGeojson => {
                L.geoJSON(usStatesGeojson, {
                    style: f => {
                        const name = f.properties.NAME;  // make sure backend sets this to match
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
            });
    })
    .catch(err => console.error("Error loading map data:", err));