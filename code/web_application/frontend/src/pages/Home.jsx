import { useEffect, useState } from "react";

export default function Home({ user }) {
    const [fixtures, setFixtures] = useState([]);
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (!user) { // When user is null, Home clears old fixture data and shows a login message
            setFixtures([]);
            setError("");
            setIsLoading(false);
            return;
        }
        // if user changes, the effect runs
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

    if (!user) {
        return (
            <section>
                <h2>Fixtures</h2>
                <p>Please log in to view and manage fixtures.</p>
            </section>
        );
    }

    return (
        <section>
            <h2>Fixtures</h2>
            {/* isLoading and error give the UI clear states while the request is in progress or fails */}
            {isLoading && <p>Loading fixtures...</p>}
            {error && <p role="alert">{error}</p>}

            {/* If there are no fixtures, show a message */}
            {!isLoading && !error && fixtures.length === 0 && (
                <p>No fixtures have been created yet.</p>
            )}

            {/* If there are fixtures, show a list */}
            {!isLoading && fixtures.length > 0 && (
                <ul>
                    {fixtures.map((fixture) => (
                        <li key={fixture.id}>
                            <strong>{fixture.fixture_name}</strong> — {fixture.teams}
                        </li>
                    ))}
                </ul>
            )}
        </section>
    );
}