import { useState, useEffect } from 'react';
import axios from 'axios'; // <--- حیاتی: ایمپورت مستقیم axios برای دیباگ
import { getPublicProviders, bookSlot } from '../../lib/api/client';

interface Provider {
  id: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  bio?: string;
}

interface Slot {
  id: string;
  start_time: string;
  end_time: string;
  status: string;
  patient_name?: string;
  patient_mobile?: string;
}

const SearchAppointment = () => {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Booking Modal State
  const [bookingModalOpen, setBookingModalOpen] = useState(false);
  const [selectedSlotForBooking, setSelectedSlotForBooking] = useState<Slot | null>(null);
  const [patientName, setPatientName] = useState('');
  const [patientMobile, setPatientMobile] = useState('');
  const [bookingLoading, setBookingLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  // ۱. بارگذاری پزشکان هنگام لود شدن صفحه
  useEffect(() => {
    const fetchProviders = async () => {
      try {
        console.log("--- Fetching Providers ---");
        const response = await axios.get('/api/v1/appointments/providers/?status=active');
        
        let dataToSet: Provider[] = [];
        if (Array.isArray(response.data)) {
          dataToSet = response.data;
        } else if (response.data.results && Array.isArray(response.data.results)) {
          dataToSet = response.data.results;
        }

        setProviders(dataToSet);
        
        if (dataToSet.length > 0) {
          setSelectedProvider(dataToSet[0].id);
        }

      } catch (error: any) {
        console.error("Failed to load providers:", error.response?.data || error.message);
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
    setSlots([]);
    
    try {
      const response = await axios.get('/api/v1/appointments/slots/', {
        params: {
          provider: providerId,
          date: date,
          status: 'available' 
        }
      });
      
      let dataToSet: Slot[] = [];
      if (Array.isArray(response.data)) {
        dataToSet = response.data;
      } else if (response.data.results && Array.isArray(response.data.results)) {
        dataToSet = response.data.results;
      }

      // ⬇️ تغییر مهم: فیلتر امنیتی اضافی در سمت کلاینت
      // حتی اگر سرور اشتباهی بدهد، اینجا مطمئن می‌شویم فقط available هستند
      const filteredSlots = dataToSet.filter(slot => slot.status === 'available');
      
      setSlots(filteredSlots);

    } catch (error: any) {
      console.error("Failed to load slots:", error.response?.data || error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBookClick = (slot: Slot) => {
    setSelectedSlotForBooking(slot);
    setBookingModalOpen(true);
    setSuccessMessage('');
  };

  const handleConfirmBooking = async () => {
    if (!selectedSlotForBooking) return;
    
    setBookingLoading(true);
    try {
      await bookSlot(selectedSlotForBooking.id, {
        patient_name: patientName,
        patient_mobile: patientMobile
      });
      
      // ⬇️ تغییر مهم: Optimistic UI Update
      // به جای ریفرش کل لیست، فقط همین آیتم را از لیست حذف می‌کنیم.
      // این کار سریع‌تر است و از مشکلات کش جلوگیری می‌کند.
      setSlots(prevSlots => prevSlots.filter(s => s.id !== selectedSlotForBooking.id));
      
      setSuccessMessage(`نوبت شما برای ساعت ${selectedSlotForBooking.start_time} با موفقیت ثبت شد.`);
      setBookingModalOpen(false);
      
      // پاک کردن فرم
      setPatientName('');
      setPatientMobile('');
      
    } catch (error: any) {
      alert(error.response?.data?.error || "خطا در ثبت نوبت.");
      // اگر خطا داد (مثلاَ کسی دیگر زودتر رزرو کرد)، لیست را ریفرش می‌کنیم تا وضعیت واقعی دیده شود
      fetchSlots(selectedProvider, selectedDate);
    } finally {
      setBookingLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center text-blue-700 mb-8">جستجو و نوبت‌دهی آنلاین</h1>

        {/* فیلترها */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">انتخاب پزشک:</label>
            <select 
              value={selectedProvider} 
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {providers.length === 0 ? (
                <option disabled>در حال بارگذاری...</option>
              ) : (
                providers.map(p => (
                  <option key={p.id} value={p.id}>
                    Dr. {p.first_name} {p.last_name}
                  </option>
                ))
              )}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">تاریخ مراجعه:</label>
            <input 
              type="date" 
              value={selectedDate}
              min={new Date().toISOString().split('T')[0]}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* پیام موفقیت */}
        {successMessage && (
          <div className="mb-6 p-4 bg-green-100 border border-green-400 text-green-700 rounded-md text-center animate-fade-in">
            {successMessage}
          </div>
        )}

        {/* لیست اسلات‌ها */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">
            ساعات آزاد برای {providers.find(p => p.id === selectedProvider)?.last_name || '...'} در تاریخ {selectedDate}
          </h2>
          
          {loading ? (
            <div className="text-center py-10 text-gray-500">در حال بارگذاری...</div>
          ) : slots.length === 0 ? (
            <div className="text-center py-10 text-gray-500">
              متأسفانه هیچ نوبت آزادی برای این تاریخ یافت نشد.
            </div>
          ) : (
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
              {slots.map((slot) => (
                <button
                  key={slot.id}
                  onClick={() => handleBookClick(slot)}
                  className="py-3 px-2 border border-blue-200 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-md font-medium transition-colors cursor-pointer"
                >
                  {slot.start_time}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* مودال ثبت اطلاعات بیمار */}
      {bookingModalOpen && selectedSlotForBooking && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-md">
            <h3 className="text-xl font-bold mb-4 text-gray-800">تأیید نوبت</h3>
            <p className="mb-4 text-gray-600">
              شما در حال رزرو نوبت ساعت <strong>{selectedSlotForBooking.start_time}</strong> هستید.
            </p>
            
            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">نام و نام خانوادگی:</label>
                <input 
                  type="text" 
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="مثلاً رضا احمدی"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">شماره موبایل:</label>
                <input 
                  type="tel" 
                  value={patientMobile}
                  onChange={(e) => setPatientMobile(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0912..."
                  required
                />
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setBookingModalOpen(false)}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-gray-700"
              >
                انصراف
              </button>
              <button 
                onClick={handleConfirmBooking}
                disabled={bookingLoading || !patientName || !patientMobile}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {bookingLoading ? 'در حال ثبت...' : 'تأیید و نهایی کردن'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchAppointment;