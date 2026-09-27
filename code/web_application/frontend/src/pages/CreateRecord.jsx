import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function CreateRecord({ user }) { //user is passed from App as a prop 
    const navigate = useNavigate();

    const [fixtureName, setFixtureName] = useState("");
    const [teamOne, setTeamOne] = useState("");
    const [teamTwo, setTeamTwo] = useState("");
    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    async function handleSubmit(event) {
        event.preventDefault();

        setError("");
        setIsSubmitting(true);

        try {
            const response = await fetch("/api/fixtures", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: "include",
                body: JSON.stringify({
                    fixture_name: fixtureName,
                    teams: `${teamOne} vs ${teamTwo}`,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Could not create fixture");
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
                <h2>Create Fixture</h2>
                <p>Please log in before creating a fixture.</p>
            </section>
        );
    }

    return (
        <section>
            <h2>Create Fixture</h2>

            <form onSubmit={handleSubmit}>
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
                    {isSubmitting ? "Creating..." : "Create fixture"}
                </button>
            </form>
        </section>
    );
}