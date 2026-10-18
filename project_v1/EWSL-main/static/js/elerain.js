 // Initialize Leaflet map
 var map = L.map('map').setView([-1.9403, 29.8739], 8);
          
 // Add a tile layer (OpenStreetMap)
 L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
   attribution: '© OpenStreetMap contributors'
 }).addTo(map);

 // Add a marker layer
 var marker = L.marker([-1.9403, 29.8739]).addTo(map);

 // Function to get elevation data from Open-Elevation API
 function getElevation(latitude, longitude) {
   const apiURL = `https://api.open-elevation.com/api/v1/lookup?locations=${latitude},${longitude}`;

   fetch(apiURL)
     .then(response => response.json())
     .then(data => {
       if (data.results.length > 0) {
         const elevation = data.results[0].elevation;

         // Update the elevation input field
         document.getElementById('elevation').value = elevation;

         console.log(`Elevation at (${latitude}, ${longitude}): ${elevation} meters`);

         // Call the function to get updated weather data
         getWeatherData(latitude, longitude);
       } else {
         console.error('Error retrieving elevation data');
       }
     })
     .catch(error => console.error('Error fetching elevation data:', error));
 }

 // Function to get 7 days forecast rainfall data from OpenWeatherMap API
 function getWeatherData(latitude, longitude) {
   const apiKey = 'c4f07e1c02379b1dbf7153b971742581'; // Replace with your valid API key
   const weatherApiURL = `http://api.openweathermap.org/data/2.5/forecast?lat=${latitude}&lon=${longitude}&appid=${apiKey}`;

   fetch(weatherApiURL)
     .then(response => {
       if (!response.ok) {
         throw new Error('Unauthorized');
       }
       return response.json();
     })
     .then(data => {
       if (data.list) {
         // Find the highest rainfall value in 7 days
         let highestRainfall = 0;
         data.list.forEach(entry => {
           const rain = entry.rain && entry.rain['3h'] || 0; // Extract rainfall for 3-hour interval
           highestRainfall = Math.max(highestRainfall, rain);
         });

         // Convert to millimeters (mm)
         const highestRainfallInMM = highestRainfall * 1000;

         // Update the rainfall input field
         document.getElementById('rainfall').value = highestRainfallInMM.toFixed(2);

         console.log('Highest Rainfall in 7 Days (in mm):', highestRainfallInMM.toFixed(2));
       } else {
         console.error('Error retrieving weather data');
       }
     })
     .catch(error => console.error('Error fetching weather data:', error));
 }

 // Update slider values dynamically
 document.querySelectorAll('input[type="range"]').forEach(function (input) {
   input.addEventListener('input', function () {
     document.getElementById(input.name + 'Value').textContent = input.value;

     // Update map position based on slider values
     var latitude = parseFloat(document.querySelector('input[name="latitude"]').value);
     var longitude = parseFloat(document.querySelector('input[name="longitude"]').value);

     // Update the marker position
     marker.setLatLng([latitude, longitude]);

     // Update map view
     map.setView([latitude, longitude]);

     // Call the function to get updated elevation
     getElevation(latitude, longitude);
   });
 });

 // Full-screen control
 map.addControl(new L.Control.Fullscreen());