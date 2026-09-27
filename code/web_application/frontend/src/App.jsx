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
    <>
      <header className="site-header">
        <div className="header-content">
          <div className="header-top">
            <h1>Community Sports League Fixtures</h1>

            {isCheckingSession ? (
              <p className="session-status">Checking session...</p>
            ) : user ? (
              <div className="account-actions">
                <span>
                  Signed in as {user.name} ({user.email})
                </span>
                <button type="button" onClick={handleLogout}>
                  Log out
                </button>
              </div>
            ) : (
              <p className="session-status">Not signed in</p>
            )}
          </div>

          <nav aria-label="Primary navigation">
            <NavLink to="/">Home</NavLink>
            <NavLink to="/create">Create</NavLink>
            <NavLink to="/update">Update</NavLink>
            <NavLink to="/delete">Delete</NavLink>
            {!user && !isCheckingSession && (
              <NavLink to="/login">Login</NavLink>
            )}
          </nav>
        </div>
      </header>

      <main className="page-content">
        <Routes>
          <Route path="/" element={<Home user={user} />} />
          <Route path="/login" element={<Login onLogin={setUser} />} />
          <Route path="/create" element={<CreateRecord user={user} />} />
          <Route path="/update" element={<UpdateRecord user={user} />} />
          <Route path="/delete" element={<DeleteRecord user={user} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}