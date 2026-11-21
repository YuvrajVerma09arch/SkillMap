import { Suspense, lazy } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import RequireAuth from "./components/RequireAuth";

// Home stays eager: it's the landing/LCP page, so it must paint in the
// first bundle. Everything else is route-split so visitors only download
// the pages they actually visit.
import Home from "./pages/Home";
const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const RoleSelect = lazy(() => import("./pages/RoleSelect"));
const Pricing = lazy(() => import("./pages/Pricing"));
const Legal = lazy(() => import("./pages/Legal"));
const SetupProfile = lazy(() => import("./pages/SetupProfile"));
const Profile = lazy(() => import("./pages/Profile"));
const CompanyProfile = lazy(() => import("./pages/CompanyProfile"));
const JobFeed = lazy(() => import("./pages/JobFeed"));
const LiveJobs = lazy(() => import("./pages/LiveJobs"));
const MyApplications = lazy(() => import("./pages/MyApplications"));
const Roadmap = lazy(() => import("./pages/Roadmap"));
const ResumeChecker = lazy(() => import("./pages/ResumeChecker"));
const Prep = lazy(() => import("./pages/Prep"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const PostJob = lazy(() => import("./pages/PostJob"));
const Applicants = lazy(() => import("./pages/Applicants"));
const TalentFeed = lazy(() => import("./pages/TalentFeed"));

export default function App() {
  return (
    <Suspense
      fallback={
        // Reserve viewport height so the swap to the loaded route can't
        // shift surrounding layout (CLS guard).
        <div
          className="min-h-[60vh] flex items-center justify-center"
          role="status"
          aria-live="polite"
        >
          <span className="font-mono text-sm text-slate-400 animate-blink">
            loading…
          </span>
        </div>
      }
    >
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/role-select" element={<RoleSelect />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/legal" element={<Legal />} />

          <Route
            path="/setup-profile"
            element={
              <RequireAuth>
                <SetupProfile />
              </RequireAuth>
            }
          />

          <Route
            path="/profile"
            element={
              <RequireAuth role="seeker">
                <Profile />
              </RequireAuth>
            }
          />
          <Route
            path="/company"
            element={
              <RequireAuth role="recruiter">
                <CompanyProfile />
              </RequireAuth>
            }
          />

          <Route
            path="/jobs"
            element={
              <RequireAuth role="seeker" needsProfile>
                <JobFeed />
              </RequireAuth>
            }
          />
          <Route
            path="/live-jobs"
            element={
              <RequireAuth role="seeker">
                <LiveJobs />
              </RequireAuth>
            }
          />
          <Route
            path="/applications"
            element={
              <RequireAuth role="seeker">
                <MyApplications />
              </RequireAuth>
            }
          />
          <Route
            path="/roadmap"
            element={
              <RequireAuth role="seeker">
                <Roadmap />
              </RequireAuth>
            }
          />
          <Route
            path="/resume-checker"
            element={
              <RequireAuth>
                <ResumeChecker />
              </RequireAuth>
            }
          />
          <Route
            path="/prep"
            element={
              <RequireAuth role="seeker">
                <Prep />
              </RequireAuth>
            }
          />

          <Route
            path="/dashboard"
            element={
              <RequireAuth role="recruiter" needsProfile>
                <Dashboard />
              </RequireAuth>
            }
          />
          <Route
            path="/post-job"
            element={
              <RequireAuth role="recruiter" needsProfile>
                <PostJob />
              </RequireAuth>
            }
          />
          <Route
            path="/applicants/:jobId"
            element={
              <RequireAuth role="recruiter">
                <Applicants />
              </RequireAuth>
            }
          />
          <Route
            path="/talent"
            element={
              <RequireAuth role="recruiter" needsProfile>
                <TalentFeed />
              </RequireAuth>
            }
          />
          <Route
            path="/talent/:userId"
            element={
              <RequireAuth role="recruiter">
                <Profile />
              </RequireAuth>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
