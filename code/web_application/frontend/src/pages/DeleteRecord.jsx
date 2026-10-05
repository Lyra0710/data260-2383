import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";

import {
    deleteFixture,
    fetchFixtures,
} from "../features/fixtures/fixturesSlice";

export default function DeleteRecord({ user }) {
    const dispatch = useDispatch();
    const navigate = useNavigate();

    const fixtures = useSelector((state) => state.fixtures.items);
    const reduxError = useSelector((state) => state.fixtures.error);

    const [selectedFixtureId, setSelectedFixtureId] = useState("");
    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        if (user) {
            dispatch(fetchFixtures());
        }
    }, [user, dispatch]);

    async function handleSubmit(event) {
        event.preventDefault();

        if (!selectedFixtureId) {
            setError("Select a fixture to delete.");
            return;
        }

        const selectedFixture = fixtures.find(
            (fixture) => fixture.id === Number(selectedFixtureId)
        );

        const shouldDelete = window.confirm(
            `Delete "${selectedFixture.fixture_name}"?`
        );

        if (!shouldDelete) {
            return;
        }

        setError("");
        setIsSubmitting(true);

        try {
            await dispatch(deleteFixture(Number(selectedFixtureId))).unwrap();
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
                <h2>Delete Fixture</h2>
                <p>Please log in before deleting a fixture.</p>
            </section>
        );
    }

    return (
        <section>
            <h2>Delete Fixture</h2>

            <form onSubmit={handleSubmit}>
                <label>
                    Select fixture
                    <select
                        value={selectedFixtureId}
                        onChange={(event) =>
                            setSelectedFixtureId(event.target.value)
                        }
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

                {(error || reduxError) && (
                    <p role="alert">{error || reduxError}</p>
                )}

                <button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? "Deleting..." : "Delete fixture"}
                </button>
            </form>
        </section>
    );
}