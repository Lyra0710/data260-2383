import { useState } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";

import CreateRecord from "./pages/CreateRecord.jsx";
import DeleteRecord from "./pages/DeleteRecord.jsx";
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import UpdateRecord from "./pages/UpdateRecord.jsx";

export default function App() {
  const [user, setUser] = useState(null);

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

        {user ? (
          <p>
            Signed in as {user.name} ({user.email})
          </p>
        ) : (
          <p>Not signed in</p>
        )}
      </header>

      <Routes>
        <Route path="/" element={<Home user={user} />} />
        <Route path="/login" element={<Login onLogin={setUser} />} />
        <Route path="/create" element={<CreateRecord />} />
        <Route path="/update" element={<UpdateRecord />} />
        <Route path="/delete" element={<DeleteRecord />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
  );
}