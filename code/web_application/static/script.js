const form = document.getElementById('fixtureForm');
const content = document.getElementById('description');
const checkbox = document.getElementById('termsAccepted');

const updateForm = document.getElementById("updateForm");
const deleteForm = document.getElementById("deleteForm");

const searchForm = document.getElementById("searchForm");
const searchInput = document.getElementById("searchInput");
const clearSearch = document.getElementById("clearSearch");

// states 
const loadingState = document.getElementById("loadingState");
const emptyState = document.getElementById("emptyState");
const errorState = document.getElementById("errorState");
const fixtureList = document.getElementById("fixtureList");
function showState(state) { // false means show the element, true means hide the element
    loadingState.hidden = state !== "loading";
    emptyState.hidden = state !== "empty";
    errorState.hidden = state !== "error";
    fixtureList.hidden = state !== "list";
}

async function loadFixtures(search = "") {
    showState("loading");

    try {
        const url = search
            ? `/api/fixtures?search=${encodeURIComponent(search)}`
            : "/api/fixtures";
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error("Unable to load fixtures.");
        }

        const fixtures = await response.json();

        if (fixtures.length === 0) {
            showState("empty");
            return;
        }

        fixtureList.innerHTML = "";

        fixtures.forEach(function (fixture) {
            const fixtureItem = document.createElement("div");

            fixtureItem.className = "fixture-item";
            fixtureItem.innerHTML = `
                <h3>${fixture.fixtureName}</h3>
                <p>Teams: ${fixture.teams}</p>
            `;

            fixtureList.appendChild(fixtureItem);
        });

        showState("list");
    } catch (error) {
        showState("error");
    }
}


const closureCounterSubmission = function () {
    let count = 0;
    return function () {
        count++;
        return count;
    }
};
const submissionCount = closureCounterSubmission();

// HW1 function
// const validateForm = (event) => {
//     // Question 1
//     event.preventDefault(); // to stop the default submission of the form
//     if (content.value.trim().length <= 25) {
//         alert("Description must be at least 26 characters long.");
//         return;
//     }
//     if (!checkbox.checked) {
//         alert("You must accept the terms and conditions.");
//         return;
//     }

//     // Question 2
//     const formData = new FormData(form); // collect values from the form
//     const formObject = Object.fromEntries(formData.entries());
//     formObject.termsAccepted = checkbox.checked; // because if unchecked, formData does not include the key termsAccepted
//     const jsonData = JSON.stringify(formObject); // convert object to json
//     console.log(jsonData);

//     // Question 3
//     const parseObject = JSON.parse(jsonData); // convert json back to object
//     const { fixtureName, submitterEmail } = parseObject;
//     console.log('Fixture name:', fixtureName);
//     console.log('Email id', submitterEmail);

//     // Question 4
//     const updatedObject = {
//         ...parseObject,
//         submissionDate: new Date().toISOString(), // ISO string represents current date-time
//     }
//     console.log("Submission date updated:", updatedObject)

//     // Question 5

//     console.log("Form submissions count:", submissionCount());
// };

// HW2 function edited from HW1 function above
const validateForm = async (event) => {
    event.preventDefault();

    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    if (content.value.trim().length <= 25) {
        alert("Description must be at least 26 characters long.");
        return;
    }

    if (!checkbox.checked) {
        alert("You must accept the terms and conditions.");
        return;
    }

    const formData = new FormData(form);
    const formObject = Object.fromEntries(formData.entries());

    const fixtureData = {
        fixtureName: formObject.fixtureName,
        teams: `${formObject.team1} vs ${formObject.team2}`
    };

    try {
        const response = await fetch("/api/fixtures", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(fixtureData)
        });

        if (!response.ok) {
            throw new Error("Unable to create fixture.");
        }

        window.location.href = "/";
    } catch (error) {
        showState("error");
    }
};

// Event listener for update form 

form.addEventListener("submit", validateForm); // attaching the arrow function to the form's submit event
updateForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const updateData = {
        fixtureName: document.getElementById("updateFixtureName").value,
        teams: `${document.getElementById("updateTeam1").value} vs ${document.getElementById("updateTeam2").value
            }`
    };

    try {
        const response = await fetch("/api/fixtures/1", {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(updateData)
        });

        if (!response.ok) {
            throw new Error("Unable to update fixture ID 1.");
        }

        window.location.href = "/";
    } catch (error) {
        showState("error");
    }
});

// Event listener for delete form
deleteForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    try {
        const response = await fetch("/api/fixtures/highest", {
            method: "DELETE"
        });

        if (!response.ok) {
            throw new Error("Unable to delete the highest-ID fixture.");
        }

        window.location.href = "/";
    } catch (error) {
        showState("error");
    }
});

// Event listener for search form
searchForm.addEventListener("submit", function (event) {
    event.preventDefault();

    const searchTerm = searchInput.value.trim();

    loadFixtures(searchTerm);
});

clearSearch.addEventListener("click", function () {
    searchInput.value = "";
    loadFixtures();
});

loadFixtures();