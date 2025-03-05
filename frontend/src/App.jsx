import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./components/Home";
import Navbar from "./components/Navbar";
import Features from "./components/Features";
import { BackgroundProvider } from "./context/BackgroundContext";
import Register from "./components/Register/Register";
import Login from "./components/Login";
import Onboarding from "./components/onboarding/Onboarding";
import Signout from "./components/Signout";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BackgroundProvider>
        <BrowserRouter>
          <Navbar />
          <Routes>
            <Route
              path="/"
              element={
                <main className="overflow-hidden relative">
                  {/* Wrapping div to ensure continuous flow */}
                  <div className="relative flex flex-col">
                    <Home />
                    <Features />
                  </div>
                </main>
              }
            />
            <Route path="/features" element={<Features />} />
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signout" element={<Signout />} />
            <Route path="/onboarding" element={<Onboarding />} />
          </Routes>
        </BrowserRouter>
      </BackgroundProvider>
    </QueryClientProvider>
  );
};

export default App;
