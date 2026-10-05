import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";

import { api } from "../api/axios";
import { createFixture } from "../features/fixtures/fixturesSlice";

export default function CreateRecord({ user }) {
    const dispatch = useDispatch();
    const navigate = useNavigate();

    const [venues, setVenues] = useState([]);
    const [fixtureName, setFixtureName] = useState("");
    const [teamOne, setTeamOne] = useState("");
    const [teamTwo, setTeamTwo] = useState("");
    const [fixtureCode, setFixtureCode] = useState("");
    const [availableSlots, setAvailableSlots] = useState("0");
    const [venueId, setVenueId] = useState("");
    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        async function loadVenues() {
            try {
                const response = await api.get("/venues");
                setVenues(response.data);
            } catch (requestError) {
                setError(
                    requestError.response?.data?.detail ||
                    "Could not load venues"
                );
            }
        }

        if (user) {
            loadVenues();
        }
    }, [user]);

    async function handleSubmit(event) {
        event.preventDefault();

        setError("");
        setIsSubmitting(true);

        try {
            await dispatch(
                createFixture({
                    fixture_name: fixtureName,
                    teams: `${teamOne} vs ${teamTwo}`,
                    fixture_code: fixtureCode,
                    available_slots: Number(availableSlots),
                    venue_id: Number(venueId),
                })
            ).unwrap();

            navigate("/");
        } catch (requestError) {
            setError(requestError);
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

                <label>
                    Fixture code
                    <input
                        type="text"
                        value={fixtureCode}
                        onChange={(event) => setFixtureCode(event.target.value)}
                        required
                    />
                </label>

                <label>
                    Available slots
                    <input
                        type="number"
                        min="0"
                        value={availableSlots}
                        onChange={(event) => setAvailableSlots(event.target.value)}
                        required
                    />
                </label>

                <label>
                    Venue
                    <select
                        value={venueId}
                        onChange={(event) => setVenueId(event.target.value)}
                        required
                    >
                        <option value="">Select a venue</option>

                        {venues.map((venue) => (
                            <option key={venue.id} value={venue.id}>
                                {venue.name} ({venue.code})
                            </option>
                        ))}
                    </select>
                </label>

                {error && <p role="alert">{error}</p>}

                <button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? "Creating..." : "Create fixture"}
                </button>
            </form>
        </section>
    );
}