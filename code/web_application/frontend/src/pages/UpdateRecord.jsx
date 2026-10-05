import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";

import { api } from "../api/axios";
import {
    fetchFixtures,
    updateFixture,
} from "../features/fixtures/fixturesSlice";

function splitTeams(teams) {
    const [teamOne = "", teamTwo = ""] = teams.split(" vs ");

    return {
        teamOne,
        teamTwo,
    };
}

export default function UpdateRecord({ user }) {
    const dispatch = useDispatch();
    const navigate = useNavigate();

    const fixtures = useSelector((state) => state.fixtures.items);
    const reduxError = useSelector((state) => state.fixtures.error);

    const [venues, setVenues] = useState([]);
    const [selectedFixtureId, setSelectedFixtureId] = useState("");
    const [fixtureName, setFixtureName] = useState("");
    const [teamOne, setTeamOne] = useState("");
    const [teamTwo, setTeamTwo] = useState("");
    const [fixtureCode, setFixtureCode] = useState("");
    const [availableSlots, setAvailableSlots] = useState("0");
    const [venueId, setVenueId] = useState("");
    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        if (!user) {
            return;
        }

        dispatch(fetchFixtures());

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

        loadVenues();
    }, [user, dispatch]);

    function handleFixtureChange(event) {
        const fixtureId = Number(event.target.value);
        setSelectedFixtureId(fixtureId);

        const selectedFixture = fixtures.find(
            (fixture) => fixture.id === fixtureId
        );

        if (!selectedFixture) {
            setFixtureName("");
            setTeamOne("");
            setTeamTwo("");
            setFixtureCode("");
            setAvailableSlots("0");
            setVenueId("");
            return;
        }

        const teams = splitTeams(selectedFixture.teams);

        setFixtureName(selectedFixture.fixture_name);
        setTeamOne(teams.teamOne);
        setTeamTwo(teams.teamTwo);
        setFixtureCode(selectedFixture.fixture_code);
        setAvailableSlots(String(selectedFixture.available_slots));
        setVenueId(String(selectedFixture.venue_id));
    }

    async function handleSubmit(event) {
        event.preventDefault();

        setError("");
        setIsSubmitting(true);

        try {
            await dispatch(
                updateFixture({
                    id: selectedFixtureId,
                    data: {
                        fixture_name: fixtureName,
                        teams: `${teamOne} vs ${teamTwo}`,
                        fixture_code: fixtureCode,
                        available_slots: Number(availableSlots),
                        venue_id: Number(venueId),
                    },
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
                <h2>Update Fixture</h2>
                <p>Please log in before updating a fixture.</p>
            </section>
        );
    }

    return (
        <section>
            <h2>Update Fixture</h2>

            <form onSubmit={handleSubmit}>
                <label>
                    Select fixture
                    <select
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
                        onChange={(event) =>
                            setAvailableSlots(event.target.value)
                        }
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

                {(error || reduxError) && (
                    <p role="alert">{error || reduxError}</p>
                )}

                <button
                    type="submit"
                    disabled={isSubmitting || !selectedFixtureId}
                >
                    {isSubmitting ? "Updating..." : "Update fixture"}
                </button>
            </form>
        </section>
    );
}