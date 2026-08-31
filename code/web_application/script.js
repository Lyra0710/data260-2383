const form = document.getElementById('fixtureForm');
const content = document.getElementById('description');
const checkbox = document.getElementById('termsAccepted');

const closureCounterSubmission = function () {
    let count = 0;
    return function () {
        count++;
        return count;
    }
};
const submissionCount = closureCounterSubmission();

const validateForm = (event) => {
    // Question 1
    event.preventDefault(); // to stop the default submission of the form
    if (content.value.trim().length <= 25) {
        alert("Description must be at least 26 characters long.");
        return;
    }
    if (!checkbox.checked) {
        alert("You must accept the terms and conditions.");
        return;
    }

    // Question 2
    const formData = new FormData(form); // collect values from the form
    const formObject = Object.fromEntries(formData.entries());
    formObject.termsAccepted = checkbox.checked; // because if unchecked, formData does not include the key termsAccepted
    const jsonData = JSON.stringify(formObject); // convert object to json
    console.log(jsonData);

    // Question 3
    const parseObject = JSON.parse(jsonData); // convert json back to object
    const { fixtureName, submitterEmail } = parseObject;
    console.log('Fixture name:', fixtureName);
    console.log('Email id', submitterEmail);

    // Question 4
    const updatedObject = {
        ...parseObject,
        submissionDate: new Date().toISOString(), // ISO string represents current date-time
    }
    console.log("Submission date updated:", updatedObject)

    // Question 5

    console.log("Form submissions count:", submissionCount());
};

form.addEventListener("submit", validateForm); // attaching the arrow function to the form's submit event
