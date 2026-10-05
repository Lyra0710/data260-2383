import { useEffect, useState } from "react";
import { api } from "../api/axios";

export default function Venues({ user }) {
    const [venues, setVenues] = useState([]);
    const [editingId, setEditingId] = useState(null);
    const [name, setName] = useState("");
    const [address, setAddress] = useState("");
    const [code, setCode] = useState("");
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

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

    useEffect(() => {
        if (user) {
            loadVenues();
        }
    }, [user]);

    function clearForm() {
        setEditingId(null);
        setName("");
        setAddress("");
        setCode("");
    }

    function startEdit(venue) {
        setEditingId(venue.id);
        setName(venue.name);
        setAddress(venue.address);
        setCode(venue.code);
        setError("");
        setMessage("");
    }

    async function handleSubmit(event) {
        event.preventDefault();

        setError("");
        setMessage("");
        setIsSubmitting(true);

        const venueData = {
            name,
            address,
            code,
        };

        try {
            if (editingId) {
                await api.put(`/venues/${editingId}`, venueData);
                setMessage("Venue updated.");
            } else {
                await api.post("/venues", venueData);
                setMessage("Venue created.");
            }

            clearForm();
            await loadVenues();
        } catch (requestError) {
            setError(
                requestError.response?.data?.detail ||
                "Venue request failed"
            );
        } finally {
            setIsSubmitting(false);
        }
    }

    async function handleDelete(venue) {
        const shouldDelete = window.confirm(
            `Delete "${venue.name}"?`
        );

        if (!shouldDelete) {
            return;
        }

        setError("");
        setMessage("");

        try {
            await api.delete(`/venues/${venue.id}`);
            setMessage("Venue deleted.");
            await loadVenues();
        } catch (requestError) {
            setError(
                requestError.response?.data?.detail ||
                "Could not delete venue"
            );
        }
    }

    if (!user) {
        return (
            <section>
                <h2>Venues</h2>
                <p>Please log in to manage venues.</p>
            </section>
        );
    }

    return (
        <section>
            <h2>{editingId ? "Update Venue" : "Create Venue"}</h2>

            <form onSubmit={handleSubmit}>
                <label>
                    Venue name
                    <input
                        type="text"
                        value={name}
                        onChange={(event) => setName(event.target.value)}
                        required
                    />
                </label>

                <label>
                    Address
                    <input
                        type="text"
                        value={address}
                        onChange={(event) => setAddress(event.target.value)}
                        required
                    />
                </label>

                <label>
                    Venue code
                    <input
                        type="text"
                        value={code}
                        onChange={(event) => setCode(event.target.value)}
                        required
                    />
                </label>

                {error && <p role="alert">{error}</p>}
                {message && <p>{message}</p>}

                <button type="submit" disabled={isSubmitting}>
                    {isSubmitting
                        ? "Saving..."
                        : editingId
                            ? "Update venue"
                            : "Create venue"}
                </button>

                {editingId && (
                    <button type="button" onClick={clearForm}>
                        Cancel
                    </button>
                )}
            </form>

            <h3>Available Venues</h3>

            <ul>
                {venues.map((venue) => (
                    <li key={venue.id}>
                        {venue.name} — {venue.address} — {venue.code}
                        {" "}
                        <button
                            type="button"
                            onClick={() => startEdit(venue)}
                        >
                            Edit
                        </button>
                        {" "}
                        <button
                            type="button"
                            onClick={() => handleDelete(venue)}
                        >
                            Delete
                        </button>
                    </li>
                ))}
            </ul>
        </section>
    );
}