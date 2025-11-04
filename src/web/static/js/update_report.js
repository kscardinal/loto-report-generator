// Back Button
const backButton = document.getElementById("backBtn");
backButton.addEventListener("click", async function() {
    console.log("Clicked Back Button!");
});

async function loadData() {
    const response = await fetch(`/get_report_json/${reportName}`);
    if (!response.ok) throw new Error("Report not found");
    const data = await response.json();
    console.log(data);
    return data;
}

async function setName() {
    const reportName = document.getElementById("name");
    
    if (window.reportName) {
        reportName.value = window.reportName;
        reportName.disabled = true;
    } else {
        reportName.disabled = false;
    }

}

async function setData_text(elementID, data) {
    const element = document.getElementById(elementID);
    const element_value = data[elementID];
    if (!element_value) { return };
    element.value = element_value;
}

async function setData_date(elementID, data) {
    const element = document.getElementById(elementID);
    const old_date = data[elementID];
    if (!old_date) { return } 
    const [month, day, year] = old_date.split('/');
    const new_date = `${year}-${month}-${day}`;
    element.value = new_date;
}

async function setData_photo(elementID, data) {
    const input_element = document.getElementById(elementID);
    const element = document.getElementById(elementID + "_preview");
    const image_name = data[elementID];
    if (!image_name) { return }

    const response = await fetch(`/photo_by_name/${image_name}`);
    if (!response.ok) {
        throw new Error('Failed to fetch image');
    }
    const blob = await response.blob();
    const imageUrl = URL.createObjectURL(blob);
    element.src = imageUrl;
    element.style.display = "inline";

    input_element.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const imageUrl = URL.createObjectURL(file);
            element.src = imageUrl;
            element.style.display = "inline";
        } else {
            element.style.display = "none";
        }
    });
}

document.addEventListener('DOMContentLoaded', async function() {
  try {
    setName();
    const data = await loadData();
    const textInputIds = Array.from(document.querySelectorAll('input[type="text"]')).map(input => input.id);
    for (const id of textInputIds) {
      setData_text(id, data);
    }
    const dateInputIds = Array.from(document.querySelectorAll('input[type="date"]')).map(input => input.id);
    for (const id of dateInputIds) {
      setData_date(id, data);
    }
    const photoInputIds = Array.from(document.querySelectorAll('input[type="file"]')).map(input => input.id);
    for (const id of photoInputIds) {
      setData_photo(id, data);
    }
  } catch (error) {
    console.error('Error:', error);
  }
});
