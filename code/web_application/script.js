const form = document.getElementById('fixtureForm');
const content = document.getElementById('description');
const checkbox = document.getElementById('termsAccepted');

const validateForm = (event) => {
    if (content.value.trim().length <= 25) {
        alert("Description must be at least 26 characters long.");
        return false;
    }
    if (!checkbox.checked) {
        alert("You must accept the terms and conditions.");
        return false;
    }
    return true;
};

form.addEventListener("submit", validateForm);