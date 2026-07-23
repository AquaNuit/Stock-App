import { useState, useEffect } from 'react';
import { AlertTriangle } from 'lucide-react';

export function MarketStatusBanner() {
  const [timeLeft, setTimeLeft] = useState('');
  const [isClosed, setIsClosed] = useState(false);

  useEffect(() => {
    const updateStatus = () => {
      const now = new Date();
      
      // Convert to IST (UTC +5:30)
      const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
      const istDate = new Date(utc + (3600000 * 5.5));
      
      const day = istDate.getDay(); // 0 is Sunday, 1 is Monday...
      const hours = istDate.getHours();
      const minutes = istDate.getMinutes();
      
      const timeInMinutes = hours * 60 + minutes;
      const openTime = 9 * 60 + 15; // 09:15
      const closeTime = 15 * 60 + 30; // 15:30
      
      let nextOpen = new Date(istDate);
      let marketClosed = false;
      
      if (day === 0) {
        // Sunday -> opens Monday 09:15
        nextOpen.setDate(istDate.getDate() + 1);
        nextOpen.setHours(9, 15, 0, 0);
        marketClosed = true;
      } else if (day === 6) {
        // Saturday -> opens Monday 09:15
        nextOpen.setDate(istDate.getDate() + 2);
        nextOpen.setHours(9, 15, 0, 0);
        marketClosed = true;
      } else if (timeInMinutes < openTime) {
        // Weekday before open -> opens today 09:15
        nextOpen.setHours(9, 15, 0, 0);
        marketClosed = true;
      } else if (timeInMinutes >= closeTime) {
        // Weekday after close -> opens tomorrow 09:15 (or Monday if Friday)
        if (day === 5) {
          nextOpen.setDate(istDate.getDate() + 3);
        } else {
          nextOpen.setDate(istDate.getDate() + 1);
        }
        nextOpen.setHours(9, 15, 0, 0);
        marketClosed = true;
      }
      
      setIsClosed(marketClosed);
      
      if (marketClosed) {
        const diff = nextOpen.getTime() - istDate.getTime();
        const d = Math.floor(diff / (1000 * 60 * 60 * 24));
        const h = Math.floor((diff / (1000 * 60 * 60)) % 24);
        const m = Math.floor((diff / 1000 / 60) % 60);
        const s = Math.floor((diff / 1000) % 60);
        
        setTimeLeft(`${d}d ${h}h ${m}m ${s}s`);
      }
    };

    updateStatus();
    const interval = setInterval(updateStatus, 1000);
    return () => clearInterval(interval);
  }, []);

  if (!isClosed) return null;

  return (
    <div style={{
      background: 'rgba(239, 68, 68, 0.1)',
      borderBottom: '1px solid rgba(239, 68, 68, 0.2)',
      color: '#fca5a5',
      padding: '8px 16px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '8px',
      fontSize: '0.875rem',
      fontWeight: 500,
      width: '100%',
    }}>
      <AlertTriangle size={16} />
      <span>Market is closed. Opens in: {timeLeft}</span>
    </div>
  );
}
