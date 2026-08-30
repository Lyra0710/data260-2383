const form = document.getElementById('fixtureForm');
const content = document.getElementById('description');
const checkbox = document.getElementById('termsAccepted');

const validateForm = (event) => {
    event.preventDefault(); // to stop the default submission of the form
    if (content.value.trim().length <= 25) {
        alert("Description must be at least 26 characters long.");
    }
    if (!checkbox.checked) {
        alert("You must accept the terms and conditions.");
    }

};

form.addEventListener("submit", validateForm); // attaching the arrow function to the form's submit event