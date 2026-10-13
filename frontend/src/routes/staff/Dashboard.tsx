import { useState, useEffect } from 'react';
import { getProviders, getSlots, bookSlot } from '../../lib/api/client';

interface Provider {
  id: string;
  first_name: string;
  last_name: string;
}

interface Slot {
  id: string;
  start_time: string;
  end_time: string;
  status: 'available' | 'booked' | 'cancelled' | 'blocked';
  patient_name?: string;
  patient_mobile?: string;
}

const StaffDashboard = () => {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [loading, setLoading] = useState(false);
  const [bookingModalOpen, setBookingModalOpen] = useState(false);
  const [selectedSlotForBooking, setSelectedSlotForBooking] = useState<Slot | null>(null);
  
  // Form State for Booking
  const [patientName, setPatientName] = useState('');
  const [patientMobile, setPatientMobile] = useState('');
  const [bookingLoading, setBookingLoading] = useState(false);

  // ۱. بارگذاری اولیه پزشکان
  useEffect(() => {
    const fetchProviders = async () => {
      try {
        const data = await getProviders();
        setProviders(data);
        if (data.length > 0) {
          setSelectedProvider(data[0].id); // انتخاب اولین پزشک به صورت پیش‌فرض
        }
      } catch (error) {
        console.error("Failed to load providers:", error);
      }
    };
    fetchProviders();
  }, []);

  // ۲. بارگذاری اسلات‌ها هر زمان که پزشک یا تاریخ عوض شود
  useEffect(() => {
    if (selectedProvider && selectedDate) {
      fetchSlots(selectedProvider, selectedDate);
    }
  }, [selectedProvider, selectedDate]);

  const fetchSlots = async (providerId: string, date: string) => {
    setLoading(true);
    try {
      const data = await getSlots({ provider: providerId, date: date });
      setSlots(data);
    } catch (error) {
      console.error("Failed to load slots:", error);
    } finally {
      setLoading(false);
    }
  };

  // ۳. باز کردن مودال رزرو
  const handleBookClick = (slot: Slot) => {
    if (slot.status !== 'available') return;
    setSelectedSlotForBooking(slot);
    setBookingModalOpen(true);
  };

  // ۴. ارسال درخواست رزرو
  const handleConfirmBooking = async () => {
    if (!selectedSlotForBooking) return;
    
    setBookingLoading(true);
    try {
      await bookSlot(selectedSlotForBooking.id, {
        patient_name: patientName,
        patient_mobile: patientMobile
      });
      
      // بستن مودال و ریفرش لیست
      setBookingModalOpen(false);
      setPatientName('');
      setPatientMobile('');
      fetchSlots(selectedProvider, selectedDate); // ریفرش
      
      alert("نوبت با موفقیت ثبت شد!");
      
    } catch (error: any) {
      alert(error.response?.data?.error || "خطا در ثبت نوبت");
    } finally {
      setBookingLoading(false);
    }
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h1 className="text-2xl font-bold mb-6 text-blue-800">داشبورد پذیرش</h1>

      {/* کنترل‌ها */}
      <div className="flex gap-4 mb-6 bg-white p-4 rounded shadow">
        <div className="flex flex-col">
          <label className="text-sm font-medium mb-1">انتخاب پزشک:</label>
          <select 
            value={selectedProvider} 
            onChange={(e) => setSelectedProvider(e.target.value)}
            className="border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {providers.map(p => (
              <option key={p.id} value={p.id}>
                Dr. {p.first_name} {p.last_name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col">
          <label className="text-sm font-medium mb-1">تاریخ:</label>
          <input 
            type="date" 
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* گرید اسلات‌ها */}
      {loading ? (
        <div className="text-center py-10">در حال بارگذاری...</div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {slots.length === 0 ? (
            <div className="col-span-full text-center text-gray-500 py-10">
              هیچ نوبتی برای این تاریخ یافت نشد. (ممکن است برنامه‌ریزی نشده باشد)
            </div>
          ) : (
            slots.map((slot) => (
              <button
                key={slot.id}
                onClick={() => handleBookClick(slot)}
                disabled={slot.status !== 'available'}
                className={`p-3 rounded border text-center transition-all
                  ${slot.status === 'available' 
                    ? 'bg-green-50 border-green-200 hover:bg-green-100 cursor-pointer text-green-800' 
                    : slot.status === 'booked'
                      ? 'bg-red-50 border-red-200 text-red-800 cursor-not-allowed opacity-75'
                      : 'bg-gray-100 border-gray-200 text-gray-500 cursor-not-allowed'
                  }`}
              >
                <div className="font-bold">{slot.start_time}</div>
                <div className="text-xs mt-1 truncate">
                  {slot.status === 'available' ? 'آزاد' : 
                   slot.status === 'booked' ? `${slot.patient_name}` : 
                   slot.status === 'blocked' ? 'مسدود' : 'لغو'}
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {/* مودال رزرو (Modal) */}
      {bookingModalOpen && selectedSlotForBooking && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded shadow-lg w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">ثبت نوبت جدید</h2>
            <p className="mb-4 text-sm text-gray-600">
              ساعت: <strong>{selectedSlotForBooking.start_time}</strong> - {selectedSlotForBooking.end_time}
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">نام بیمار:</label>
                <input 
                  type="text" 
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                  placeholder="مثلاً رضا احمدی"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">شماره موبایل:</label>
                <input 
                  type="tel" 
                  value={patientMobile}
                  onChange={(e) => setPatientMobile(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                  placeholder="0912..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button 
                onClick={() => setBookingModalOpen(false)}
                className="px-4 py-2 border rounded hover:bg-gray-50"
              >
                انصراف
              </button>
              <button 
                onClick={handleConfirmBooking}
                disabled={bookingLoading || !patientName || !patientMobile}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
              >
                {bookingLoading ? 'در حال ثبت...' : 'تأیید و ثبت'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StaffDashboard;