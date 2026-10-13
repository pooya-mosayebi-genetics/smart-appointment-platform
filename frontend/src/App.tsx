import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
// import PublicHome from './routes/public/Home'; // حذف یا غیرفعال کردن
import StaffDashboard from './routes/staff/Dashboard';
import TvDisplay from './routes/tv/Display';
import LoginPage from './features/auth/LoginPage';
import SearchAppointment from './features/public/SearchAppointment'; // <--- ایمپورت جدید

function App() {
  return (
    <Router>
      <Routes>
        {/* مسیر اصلی: جستجوی نوبت */}
        <Route path="/" element={<SearchAppointment />} /> 
        
        {/* مسیر لاگین */}
        <Route path="/login" element={<LoginPage />} /> 
        
        {/* مسیرهای مدیریتی/پذیرش */}
        <Route path="/staff/dashboard" element={<StaffDashboard />} />
        
        {/* مسیر نمایشگر تلویزیون */}
        <Route path="/tv" element={<TvDisplay />} />
      </Routes>
    </Router>
  );
}

export default App;