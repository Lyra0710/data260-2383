import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";

import CreateRecord from "./pages/CreateRecord.jsx";
import DeleteRecord from "./pages/DeleteRecord.jsx";
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import UpdateRecord from "./pages/UpdateRecord.jsx";

export default function App() {
  const [user, setUser] = useState(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  useEffect(() => { // runs once when app first loads 
    async function checkSession() {
      try {
        const response = await fetch("/api/me", { // checks whether the browser already has a valid HTTP-only session cookie 
          credentials: "include",
        });

        if (response.ok) { // If valid, it restores the signed-in user into React state after a refresh
          const currentUser = await response.json();
          setUser(currentUser);
        }
      } finally {
        setIsCheckingSession(false);
      }
    }

    checkSession();
  }, []);

  async function handleLogout() { // removes the database session and cookie
    await fetch("/api/logout", {
      method: "POST",
      credentials: "include",
    });

    setUser(null);
  }

  return (
    <main>
      <header>
        <h1>Community Sports League Fixtures</h1>

        <nav>
          <NavLink to="/">Home</NavLink>
          <NavLink to="/create">Create</NavLink>
          <NavLink to="/update">Update</NavLink>
          <NavLink to="/delete">Delete</NavLink>
          <NavLink to="/login">Login</NavLink>
        </nav>

        {isCheckingSession ? (
          <p>Checking session...</p>
        ) : user ? (
          <div>
            <p>
              Signed in as {user.name} ({user.email})
            </p>
            <button type="button" onClick={handleLogout}>
              Log out
            </button>
          </div>
        ) : (
          <p>Not signed in</p>
        )}
      </header>

      <Routes>
        <Route path="/" element={<Home user={user} />} />
        <Route path="/login" element={<Login onLogin={setUser} />} />
        <Route path="/create" element={<CreateRecord user={user} />} />
        <Route path="/update" element={<UpdateRecord />} />
        <Route path="/delete" element={<DeleteRecord />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
  );
}