import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Home from "./components/Home";
import Navbar from "./components/Navbar";
import Features from "./components/Features";
import { BackgroundProvider } from "./context/BackgroundContext";
import Register from "./components/Register/Register";
import Login from "./components/Login";
import Onboarding from "./components/onboarding/Onboarding";
import SkillAssesment from "./components/SkillAssessment";
import SkillAssessmentRecommendations from "./components/SkillAssessmentRecommendations";
import YoutubeAssessment from "./components/YoutubeAssessment";
import Dashboard from "./components/Dashboard";
import Signout from "./components/Signout";
import OverallStatistics from "./components/OverallStatistics";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Protected route to ensure the user is logged in
const ProtectedRoute = ({ children }) => {
  const isLoggedIn = localStorage.getItem("isLoggedIn") === "true";
  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// Route that checks for user progress
const UserProgressRoute = ({ children }) => {
  const isLoggedIn = localStorage.getItem("isLoggedIn") === "true";
  const onboardingComplete = localStorage.getItem("onboardingComplete") === "true";
  const assessmentComplete = localStorage.getItem("skillAssessmentComplete") === "true";
  const reassessmentInfo = localStorage.getItem("reassessmentInfo");

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }
  if (!onboardingComplete && !reassessmentInfo) {
    return <Navigate to="/onboarding" replace />;
  }
  if (!assessmentComplete && !reassessmentInfo) {
    return <Navigate to="/assessment" replace />;
  }
  return children;
};

const queryClient = new QueryClient();

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BackgroundProvider>
        <BrowserRouter>
          <Navbar />
          <Routes>
            {/* Public routes */}
            <Route
              path="/"
              element={
                <main className="overflow-hidden relative">
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

            {/* Protected routes */}
            <Route
              path="/onboarding"
              element={
                <ProtectedRoute>
                  <Onboarding />
                </ProtectedRoute>
              }
            />
            <Route
              path="/assessment"
              element={
                <ProtectedRoute>
                  <SkillAssesment />
                </ProtectedRoute>
              }
            />
            <Route
              path="/recommendations"
              element={
                <ProtectedRoute>
                  <SkillAssessmentRecommendations />
                </ProtectedRoute>
              }
            />
            <Route
              path="/youtube-assesment"
              element={
                <ProtectedRoute>
                  <YoutubeAssessment />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <UserProgressRoute>
                  <Dashboard />
                </UserProgressRoute>
              }
            />
            <Route
              path="/overall-statistics"
              element={
                  <OverallStatistics />
              }
            />
          </Routes>
        </BrowserRouter>
      </BackgroundProvider>
    </QueryClientProvider>
  );
};

export default App;
