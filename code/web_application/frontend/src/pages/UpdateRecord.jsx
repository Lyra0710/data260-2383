import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

function splitTeams(teams) {
    const [teamOne = "", teamTwo = ""] = teams.split(" vs ");

    return {
        teamOne,
        teamTwo,
    };
}

export default function UpdateRecord({ user }) {
    const navigate = useNavigate();

    const [fixtures, setFixtures] = useState([]);
    const [selectedFixtureId, setSelectedFixtureId] = useState("");
    const [fixtureName, setFixtureName] = useState("");
    const [teamOne, setTeamOne] = useState("");
    const [teamTwo, setTeamTwo] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => { // fetches the protected fixture list once a user is available
        if (!user) {
            return;
        }

        async function loadFixtures() {
            setError("");

            try {
                const response = await fetch("/api/fixtures", {
                    credentials: "include",
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || "Could not load fixtures");
                }

                setFixtures(data);
            } catch (requestError) {
                setError(requestError.message);
            }
        }

        loadFixtures();
    }, [user]);
    // finds that fixture in the downloaded list and fills the form
    function handleFixtureChange(event) {
        const fixtureId = Number(event.target.value);

        setSelectedFixtureId(fixtureId);

        const selectedFixture = fixtures.find(
            (fixture) => fixture.id === fixtureId,
        );

        if (!selectedFixture) {
            setFixtureName("");
            setTeamOne("");
            setTeamTwo("");
            return;
        }

        const teams = splitTeams(selectedFixture.teams); // turns the stored string, such as Falcons vs Tigers, back into the two separate inputs

        setFixtureName(selectedFixture.fixture_name);
        setTeamOne(teams.teamOne);
        setTeamTwo(teams.teamTwo);
    }

    async function handleSubmit(event) {
        event.preventDefault();

        if (!selectedFixtureId) {
            setError("Select a fixture to update.");
            return;
        }

        setError("");
        setIsSubmitting(true);

        try {
            const response = await fetch(
                `/api/fixtures/${selectedFixtureId}`,
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    credentials: "include",
                    body: JSON.stringify({
                        fixture_name: fixtureName,
                        teams: `${teamOne} vs ${teamTwo}`,
                    }),
                },
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Could not update fixture");
            }

            navigate("/");
        } catch (requestError) {
            setError(requestError.message);
        } finally {
            setIsSubmitting(false);
        }
    }

    if (!user) {
        return (
            <section>
                <h2>Update Fixture</h2>
                <p>Please log in before updating a fixture.</p>
            </section>
        );
    }

    return (
        <section>
            <h2>Update Fixture</h2>

            {isLoading && <p>Loading fixtures...</p>}

            {!isLoading && (
                <form onSubmit={handleSubmit}>
                    <label>
                        Select fixture
                        <select /* chooses which fixture to edit */
                            value={selectedFixtureId}
                            onChange={handleFixtureChange}
                            required
                        >
                            <option value="">Choose a fixture</option>

                            {fixtures.map((fixture) => (
                                <option key={fixture.id} value={fixture.id}>
                                    {fixture.fixture_name}
                                </option>
                            ))}
                        </select>
                    </label>

                    <label>
                        Fixture name
                        <input
                            type="text"
                            value={fixtureName}
                            onChange={(event) => setFixtureName(event.target.value)}
                            required
                        />
                    </label>

                    <label>
                        Team one
                        <input
                            type="text"
                            value={teamOne}
                            onChange={(event) => setTeamOne(event.target.value)}
                            required
                        />
                    </label>

                    <label>
                        Team two
                        <input
                            type="text"
                            value={teamTwo}
                            onChange={(event) => setTeamTwo(event.target.value)}
                            required
                        />
                    </label>

                    {error && <p role="alert">{error}</p>}

                    <button type="submit" disabled={isSubmitting}>
                        {isSubmitting ? "Updating..." : "Update fixture"}
                    </button>
                </form>
            )}
        </section>
    );
}