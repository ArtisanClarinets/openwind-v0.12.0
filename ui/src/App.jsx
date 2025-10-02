import { NavLink, Route, Routes } from 'react-router-dom';
import { Home } from './pages/Home.jsx';
import { GeometryPage } from './pages/Geometry.jsx';
import { SimulationPage } from './pages/Simulation.jsx';
import { OptimizationPage } from './pages/Optimization.jsx';
import { ResultsPage } from './pages/Results.jsx';
import { SettingsPage } from './pages/Settings.jsx';
import { ToastProvider } from './components/Toast.jsx';

const navItems = [
  { to: '/', label: 'Home' },
  { to: '/geometry', label: 'Geometry Builder' },
  { to: '/simulation', label: 'Simulation' },
  { to: '/optimization', label: 'Optimization' },
  { to: '/results', label: 'Results' },
  { to: '/settings', label: 'Settings' }
];

export default function App() {
  return (
    <ToastProvider>
      <div className="layout">
        <header className="topbar" role="banner">
          <div className="brand">OpenWInD Bb Clarinet Studio</div>
          <nav aria-label="Primary navigation">
            <ul className="nav">
              {navItems.map((item) => (
                <li key={item.to}>
                  <NavLink to={item.to} end={item.to === '/'}>
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        </header>
        <main id="main-content" tabIndex={-1}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/geometry" element={<GeometryPage />} />
            <Route path="/simulation" element={<SimulationPage />} />
            <Route path="/optimization" element={<OptimizationPage />} />
            <Route path="/results" element={<ResultsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </ToastProvider>
  );
}
