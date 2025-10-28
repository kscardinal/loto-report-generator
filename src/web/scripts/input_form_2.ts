// Format dates to today on load
window.onload = () => {
  const dateInput = document.getElementById("date") as HTMLInputElement | null;
  const completedDateInput = document.getElementById("completedDate") as HTMLInputElement | null;

  const today: Date = new Date()

  if (dateInput) {
    dateInput.value = formatDate(today, "-");
  }
  if (completedDateInput) {
    completedDateInput.value = formatDate(today, "-");
  }
};

function formatDate(dateInput: Date, separator = "-"): string {
  const date = new Date(dateInput);
  if (isNaN(date.getTime())) {
    throw new Error("Invalid date");
  }
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return `${yyyy}${separator}${mm}${separator}${dd}`;
}
