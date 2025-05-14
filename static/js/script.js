function uploadFile() {
  const fileInput = document.getElementById("fileInput");
  const file = fileInput.files[0];
  if (file) {
    const formData = new FormData();
    formData.append("file", file);

    fetch("/upload", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("Success:", data);
        // Initialize map with data
        initMap(data);
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  } else {
    alert("Please select a file to upload.");
  }
}

function initMap(data) {
  const map = L.map("map").setView([6.13852, 80.10066], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  // Example: Add a marker for each visit record
  data.visit_records.forEach((record) => {
    L.marker([record.check_in[0], record.check_in[1]])
      .addTo(map)
      .bindPopup(
        `<b>${record.shop}</b><br>Check-in: ${record.check_in}<br>Check-out: ${record.check_out}<br>Duration: ${record.duration_min} min`
      );
  });

  // Example: Draw the path
  const latlngs = data.route_coords.map((coord) => [coord[0], coord[1]]);
  L.polyline(latlngs, { color: "blue" }).addTo(map);
}
