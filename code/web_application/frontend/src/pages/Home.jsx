import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
    deleteFixture,
    fetchFixtures,
} from "../features/fixtures/fixturesSlice";

export default function Home({ user }) {
    const dispatch = useDispatch();

    const {
        items: fixtures,
        loading,
        error,
    } = useSelector((state) => state.fixtures);

    useEffect(() => {
        if (user) {
            dispatch(fetchFixtures());
        }
    }, [user, dispatch]);

    async function handleDelete(fixture) {
        const shouldDelete = window.confirm(
            `Delete "${fixture.fixture_name}"?`
        );

        if (!shouldDelete) {
            return;
        }

        try {
            await dispatch(deleteFixture(fixture.id)).unwrap();
        } catch (requestError) {
            console.error(requestError);
        }
    }

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

            {loading && <p>Loading fixtures...</p>}

            {error && <p role="alert">{error}</p>}

            {!loading && !error && fixtures.length === 0 && (
                <p>No fixtures have been created yet.</p>
            )}

            {!loading && fixtures.length > 0 && (
                <ul>
                    {fixtures.map((fixture) => (
                        <li key={fixture.id}>
                            <strong>{fixture.fixture_name}</strong>
                            {" — "}
                            {fixture.teams}
                            {" — "}
                            {fixture.fixture_code}
                            {" — "}
                            {fixture.available_slots} slots

                            <button
                                type="button"
                                onClick={() => handleDelete(fixture)}
                            >
                                Delete
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </section>
    );
}