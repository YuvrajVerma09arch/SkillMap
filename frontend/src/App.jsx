import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import RequireAuth from './components/RequireAuth'

import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import RoleSelect from './pages/RoleSelect'
import Pricing from './pages/Pricing'
import Legal from './pages/Legal'
import SetupProfile from './pages/SetupProfile'
import Profile from './pages/Profile'
import CompanyProfile from './pages/CompanyProfile'
import JobFeed from './pages/JobFeed'
import LiveJobs from './pages/LiveJobs'
import MyApplications from './pages/MyApplications'
import Roadmap from './pages/Roadmap'
import ResumeChecker from './pages/ResumeChecker'
import Prep from './pages/Prep'
import Dashboard from './pages/Dashboard'
import PostJob from './pages/PostJob'
import Applicants from './pages/Applicants'
import TalentFeed from './pages/TalentFeed'

export default function App() {
  return (
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
  )
}
