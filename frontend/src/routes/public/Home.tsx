import { useEffect, useState } from 'react';
import { getHealth } from '../../lib/api/client';

const PublicHome = () => {
  const [status, setStatus] = useState<string>('checking...');

  useEffect(() => {
    checkServer();
  }, []);

  const checkServer = async () => {
    try {
      const data = await getHealth();
      if (data.status === 'ok') {
        setStatus('✅ Connected to Backend');
      } else {
        setStatus('⚠️ Unknown Status');
      }
    } catch (error) {
      setStatus('❌ Cannot connect to Backend after retries');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-blue-600">صفحه نوبت‌دهی عمومی</h1>
        <p className="text-lg text-gray-700">{status}</p>
      </div>
    </div>
  );
};

export default PublicHome;