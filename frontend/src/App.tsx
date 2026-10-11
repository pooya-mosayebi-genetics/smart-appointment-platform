import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import PublicHome from './routes/public/Home';
import StaffDashboard from './routes/staff/Dashboard';
import TvDisplay from './routes/tv/Display';

function App() {
  return (
    <Router>
      <Routes>
        {/* مسیرهای عمومی */}
        <Route path="/" element={<PublicHome />} />
        
        {/* مسیرهای مدیریتی/پذیرش */}
        <Route path="/staff/dashboard" element={<StaffDashboard />} />
        
        {/* مسیر نمایشگر تلویزیون */}
        <Route path="/tv" element={<TvDisplay />} />
      </Routes>
    </Router>
  );
}

export default App;