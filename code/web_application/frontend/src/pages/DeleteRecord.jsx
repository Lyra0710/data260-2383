import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function DeleteRecord({ user }) {
    const navigate = useNavigate();

    const [fixtures, setFixtures] = useState([]);
    const [selectedFixtureId, setSelectedFixtureId] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        if (!user) {
            return;
        }

        async function loadFixtures() {
            setIsLoading(true);
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
            } finally {
                setIsLoading(false);
            }
        }

        loadFixtures();
    }, [user]);

    async function handleSubmit(event) {
        event.preventDefault();

        if (!selectedFixtureId) {
            setError("Select a fixture to delete.");
            return;
        }
        // loads the authenticated user’s available fixtures
        const selectedFixture = fixtures.find(
            (fixture) => fixture.id === Number(selectedFixtureId),
        );
        // asks for explicit confirmation 
        const shouldDelete = window.confirm(
            `Delete "${selectedFixture.fixture_name}"?`,
        );

        if (!shouldDelete) {
            return;
        }

        setError("");
        setIsSubmitting(true);

        // Sends a DELETE request to the backend
        try {
            const response = await fetch(
                `/api/fixtures/${selectedFixtureId}`,
                {
                    method: "DELETE",
                    credentials: "include",
                },
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Could not delete fixture");
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
                <h2>Delete Fixture</h2>
                <p>Please log in before deleting a fixture.</p>
            </section>
        );
    }

    return (
        <section>
            <h2>Delete Fixture</h2>

            {isLoading && <p>Loading fixtures...</p>}

            {!isLoading && (
                <form onSubmit={handleSubmit}>
                    <label>
                        Select fixture
                        <select
                            value={selectedFixtureId}
                            onChange={(event) => setSelectedFixtureId(event.target.value)}
                            required
                        >
                            <option value="">Choose a fixture</option>

                            {fixtures.map((fixture) => (
                                <option key={fixture.id} value={fixture.id}>
                                    {fixture.fixture_name} — {fixture.teams}
                                </option>
                            ))}
                        </select>
                    </label>

                    {error && <p role="alert">{error}</p>}

                    <button type="submit" disabled={isSubmitting}>
                        {isSubmitting ? "Deleting..." : "Delete fixture"}
                    </button>
                </form>
            )}
        </section>
    );
}