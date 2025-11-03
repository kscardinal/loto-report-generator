const img = document.getElementById("machine_image_preview");
const machine_image_button = document.getElementById("machine_image_button");

// Set the image source dynamically
img.src = "/photo/6900e18012ef82a867770cb5";  // Replace with your photo ID
img.style.display = "inline-block"; // Make it visible after setting src
machine_image_button.style.display = "inline-block"


// Optional: handle load/error
img.onload = () => console.log("Image loaded!");
img.onerror = () => {
    console.warn("Image not found.");
    img.style.display = "none";
}