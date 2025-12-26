/**
 * WorkSlot - Embeddable Booking Calendar Widget
 * 
 * Usage:
 * <div id="workslot-calendar"></div>
 * <script src="https://your-domain.com/widget/workslot.js"></script>
 * <script>
 *   WorkSlot.init({
 *     apiKey: 'wsk_your_api_key',
 *     container: '#workslot-calendar',
 *     theme: 'light', // 'light' or 'dark'
 *     primaryColor: '#6366f1',
 *     onBookingSuccess: (booking) => console.log('Booked:', booking),
 *     onBookingError: (error) => console.error('Error:', error)
 *   });
 * </script>
 */

(function(window) {
  'use strict';

  const API_BASE = window.WORKSLOT_API_URL || 'http://localhost:8000';
  
  // Inject styles
  function injectStyles(options) {
    const primaryColor = options.primaryColor || '#6366f1';
    const isDark = options.theme === 'dark';
    
    const styles = `
      .ws-container {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
        max-width: 480px;
        margin: 0 auto;
        background: ${isDark ? '#1f2937' : '#ffffff'};
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(0,0,0,${isDark ? '0.3' : '0.1'});
        overflow: hidden;
        color: ${isDark ? '#f3f4f6' : '#1f2937'};
      }
      
      .ws-header {
        padding: 24px;
        background: linear-gradient(135deg, ${primaryColor} 0%, #a855f7 100%);
        color: white;
        text-align: center;
      }
      
      .ws-header h2 {
        margin: 0 0 4px 0;
        font-size: 20px;
        font-weight: 600;
      }
      
      .ws-header p {
        margin: 0;
        opacity: 0.9;
        font-size: 14px;
      }
      
      .ws-content {
        padding: 24px;
      }
      
      .ws-calendar-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;
      }
      
      .ws-calendar-nav button {
        background: ${isDark ? '#374151' : '#f3f4f6'};
        border: none;
        width: 36px;
        height: 36px;
        border-radius: 8px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        color: ${isDark ? '#f3f4f6' : '#374151'};
        transition: all 0.2s;
      }
      
      .ws-calendar-nav button:hover {
        background: ${primaryColor};
        color: white;
      }
      
      .ws-calendar-nav span {
        font-weight: 600;
        font-size: 16px;
      }
      
      .ws-calendar-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 4px;
        margin-bottom: 20px;
      }
      
      .ws-calendar-day-header {
        text-align: center;
        font-size: 12px;
        font-weight: 500;
        color: ${isDark ? '#9ca3af' : '#6b7280'};
        padding: 8px 0;
      }
      
      .ws-calendar-day {
        aspect-ratio: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        background: transparent;
        border: none;
        color: inherit;
      }
      
      .ws-calendar-day:hover:not(:disabled) {
        background: ${isDark ? '#374151' : '#f3f4f6'};
      }
      
      .ws-calendar-day.other-month {
        color: ${isDark ? '#4b5563' : '#d1d5db'};
      }
      
      .ws-calendar-day.today {
        background: ${primaryColor}20;
        color: ${primaryColor};
        font-weight: 600;
      }
      
      .ws-calendar-day.selected {
        background: ${primaryColor};
        color: white;
        font-weight: 600;
      }
      
      .ws-calendar-day.has-slots::after {
        content: '';
        position: absolute;
        bottom: 4px;
        width: 4px;
        height: 4px;
        background: ${primaryColor};
        border-radius: 50%;
      }
      
      .ws-calendar-day:disabled {
        color: ${isDark ? '#4b5563' : '#d1d5db'};
        cursor: not-allowed;
      }
      
      .ws-slots {
        margin-bottom: 20px;
      }
      
      .ws-slots-title {
        font-weight: 600;
        margin-bottom: 12px;
        font-size: 14px;
      }
      
      .ws-slots-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
      }
      
      .ws-slot {
        padding: 10px 12px;
        border: 2px solid ${isDark ? '#374151' : '#e5e7eb'};
        border-radius: 8px;
        background: transparent;
        cursor: pointer;
        font-size: 13px;
        font-weight: 500;
        transition: all 0.2s;
        color: inherit;
      }
      
      .ws-slot:hover {
        border-color: ${primaryColor};
        color: ${primaryColor};
      }
      
      .ws-slot.selected {
        background: ${primaryColor};
        border-color: ${primaryColor};
        color: white;
      }
      
      .ws-slot:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }
      
      .ws-form {
        display: flex;
        flex-direction: column;
        gap: 16px;
      }
      
      .ws-form-group {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      
      .ws-form-group label {
        font-size: 13px;
        font-weight: 500;
        color: ${isDark ? '#9ca3af' : '#6b7280'};
      }
      
      .ws-form-group input,
      .ws-form-group textarea {
        padding: 12px 14px;
        border: 2px solid ${isDark ? '#374151' : '#e5e7eb'};
        border-radius: 8px;
        font-size: 14px;
        transition: all 0.2s;
        background: ${isDark ? '#374151' : '#ffffff'};
        color: inherit;
      }
      
      .ws-form-group input:focus,
      .ws-form-group textarea:focus {
        outline: none;
        border-color: ${primaryColor};
        box-shadow: 0 0 0 3px ${primaryColor}20;
      }
      
      .ws-form-group textarea {
        resize: vertical;
        min-height: 80px;
      }
      
      .ws-submit {
        padding: 14px 24px;
        background: linear-gradient(135deg, ${primaryColor} 0%, #a855f7 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
      }
      
      .ws-submit:hover {
        opacity: 0.9;
        transform: translateY(-1px);
      }
      
      .ws-submit:disabled {
        opacity: 0.6;
        cursor: not-allowed;
        transform: none;
      }
      
      .ws-back-btn {
        background: ${isDark ? '#374151' : '#f3f4f6'};
        color: ${isDark ? '#f3f4f6' : '#374151'};
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 16px;
        transition: all 0.2s;
      }
      
      .ws-back-btn:hover {
        background: ${isDark ? '#4b5563' : '#e5e7eb'};
      }
      
      .ws-success {
        text-align: center;
        padding: 40px 24px;
      }
      
      .ws-success-icon {
        width: 64px;
        height: 64px;
        background: #10b981;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 20px;
      }
      
      .ws-success-icon svg {
        width: 32px;
        height: 32px;
        color: white;
      }
      
      .ws-success h3 {
        margin: 0 0 8px 0;
        font-size: 20px;
      }
      
      .ws-success p {
        margin: 0;
        color: ${isDark ? '#9ca3af' : '#6b7280'};
        font-size: 14px;
      }
      
      .ws-loading {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 60px;
      }
      
      .ws-spinner {
        width: 40px;
        height: 40px;
        border: 3px solid ${isDark ? '#374151' : '#e5e7eb'};
        border-top-color: ${primaryColor};
        border-radius: 50%;
        animation: ws-spin 0.8s linear infinite;
      }
      
      @keyframes ws-spin {
        to { transform: rotate(360deg); }
      }
      
      .ws-error {
        background: #fef2f2;
        color: #dc2626;
        padding: 12px 16px;
        border-radius: 8px;
        font-size: 14px;
        margin-bottom: 16px;
      }
      
      .ws-no-slots {
        text-align: center;
        padding: 24px;
        color: ${isDark ? '#9ca3af' : '#6b7280'};
        font-size: 14px;
      }
    `;
    
    const styleEl = document.createElement('style');
    styleEl.id = 'workslot-styles';
    styleEl.textContent = styles;
    
    if (!document.getElementById('workslot-styles')) {
      document.head.appendChild(styleEl);
    }
  }

  // Format time
  function formatTime(date) {
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  }

  // Format date for display
  function formatDateDisplay(date) {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric'
    });
  }

  // Main Widget Class
  class WorkSlotWidget {
    constructor(options) {
      this.options = {
        container: '#workslot-calendar',
        theme: 'light',
        primaryColor: '#6366f1',
        ...options
      };
      
      this.apiKey = options.apiKey;
      this.container = document.querySelector(this.options.container);
      this.currentMonth = new Date();
      this.selectedDate = null;
      this.selectedSlot = null;
      this.availability = [];
      this.providerInfo = null;
      this.step = 'calendar'; // calendar, slots, form, success
      
      if (!this.container) {
        console.error('WorkSlot: Container not found');
        return;
      }
      
      if (!this.apiKey) {
        console.error('WorkSlot: API key is required');
        return;
      }
      
      injectStyles(this.options);
      this.init();
    }
    
    async init() {
      this.render();
      await this.loadProviderInfo();
      await this.loadAvailability();
      this.render();
    }
    
    async apiCall(endpoint, options = {}) {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey,
          ...options.headers
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'API request failed');
      }
      
      return response.json();
    }
    
    async loadProviderInfo() {
      try {
        this.providerInfo = await this.apiCall('/api/provider-info');
      } catch (error) {
        console.error('WorkSlot: Failed to load provider info', error);
      }
    }
    
    async loadAvailability() {
      try {
        const startDate = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth(), 1);
        const endDate = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth() + 1, 0);
        
        const data = await this.apiCall(
          `/api/availability?start_date=${startDate.toISOString().split('T')[0]}&end_date=${endDate.toISOString().split('T')[0]}`
        );
        
        this.availability = data.days || [];
      } catch (error) {
        console.error('WorkSlot: Failed to load availability', error);
        this.availability = [];
      }
    }
    
    getSlotsForDate(date) {
      const dateStr = date.toISOString().split('T')[0];
      const dayData = this.availability.find(d => d.date === dateStr);
      return dayData?.slots?.filter(s => s.available) || [];
    }
    
    prevMonth() {
      this.currentMonth = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth() - 1, 1);
      this.loadAvailability().then(() => this.render());
    }
    
    nextMonth() {
      this.currentMonth = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth() + 1, 1);
      this.loadAvailability().then(() => this.render());
    }
    
    selectDate(date) {
      this.selectedDate = date;
      this.selectedSlot = null;
      this.step = 'slots';
      this.render();
    }
    
    selectSlot(slot) {
      this.selectedSlot = slot;
      this.step = 'form';
      this.render();
    }
    
    goBack() {
      if (this.step === 'form') {
        this.step = 'slots';
        this.selectedSlot = null;
      } else if (this.step === 'slots') {
        this.step = 'calendar';
        this.selectedDate = null;
      }
      this.render();
    }
    
    async submitBooking(formData) {
      try {
        const booking = await this.apiCall('/api/bookings', {
          method: 'POST',
          body: JSON.stringify({
            customer_name: formData.name,
            customer_email: formData.email,
            customer_phone: formData.phone || null,
            slot_start: this.selectedSlot.start,
            slot_end: this.selectedSlot.end,
            notes: formData.notes || null
          })
        });
        
        this.step = 'success';
        this.render();
        
        if (this.options.onBookingSuccess) {
          this.options.onBookingSuccess(booking);
        }
      } catch (error) {
        if (this.options.onBookingError) {
          this.options.onBookingError(error);
        }
        throw error;
      }
    }
    
    renderCalendar() {
      const year = this.currentMonth.getFullYear();
      const month = this.currentMonth.getMonth();
      const firstDay = new Date(year, month, 1);
      const lastDay = new Date(year, month + 1, 0);
      const startDay = firstDay.getDay();
      const daysInMonth = lastDay.getDate();
      
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December'];
      
      let calendarHTML = `
        <div class="ws-calendar-nav">
          <button onclick="window._wsWidget.prevMonth()">
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
          </button>
          <span>${monthNames[month]} ${year}</span>
          <button onclick="window._wsWidget.nextMonth()">
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </button>
        </div>
        <div class="ws-calendar-grid">
      `;
      
      // Day headers
      days.forEach(day => {
        calendarHTML += `<div class="ws-calendar-day-header">${day}</div>`;
      });
      
      // Previous month days
      const prevMonthDays = new Date(year, month, 0).getDate();
      for (let i = startDay - 1; i >= 0; i--) {
        calendarHTML += `<button class="ws-calendar-day other-month" disabled>${prevMonthDays - i}</button>`;
      }
      
      // Current month days
      for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);
        const isPast = date < today;
        const isToday = date.getTime() === today.getTime();
        const slots = this.getSlotsForDate(date);
        const hasSlots = slots.length > 0;
        
        let classes = 'ws-calendar-day';
        if (isToday) classes += ' today';
        if (hasSlots && !isPast) classes += ' has-slots';
        
        calendarHTML += `
          <button 
            class="${classes}" 
            ${isPast || !hasSlots ? 'disabled' : ''}
            onclick="window._wsWidget.selectDate(new Date(${year}, ${month}, ${day}))"
          >${day}</button>
        `;
      }
      
      // Next month days
      const remaining = 42 - (startDay + daysInMonth);
      for (let i = 1; i <= remaining; i++) {
        calendarHTML += `<button class="ws-calendar-day other-month" disabled>${i}</button>`;
      }
      
      calendarHTML += '</div>';
      
      return calendarHTML;
    }
    
    renderSlots() {
      const slots = this.getSlotsForDate(this.selectedDate);
      
      let html = `
        <button class="ws-back-btn" onclick="window._wsWidget.goBack()">
          ← Back to calendar
        </button>
        <div class="ws-slots">
          <div class="ws-slots-title">Available times for ${formatDateDisplay(this.selectedDate)}</div>
      `;
      
      if (slots.length === 0) {
        html += '<div class="ws-no-slots">No available slots for this date</div>';
      } else {
        html += '<div class="ws-slots-grid">';
        slots.forEach(slot => {
          const startTime = new Date(slot.start);
          html += `
            <button 
              class="ws-slot" 
              onclick="window._wsWidget.selectSlot(${JSON.stringify(slot).replace(/"/g, '&quot;')})"
            >
              ${formatTime(startTime)}
            </button>
          `;
        });
        html += '</div>';
      }
      
      html += '</div>';
      return html;
    }
    
    renderForm() {
      const startTime = new Date(this.selectedSlot.start);
      const endTime = new Date(this.selectedSlot.end);
      
      return `
        <button class="ws-back-btn" onclick="window._wsWidget.goBack()">
          ← Back to time selection
        </button>
        <div class="ws-slots-title">
          ${formatDateDisplay(this.selectedDate)} at ${formatTime(startTime)} - ${formatTime(endTime)}
        </div>
        <form class="ws-form" onsubmit="window._wsWidget.handleSubmit(event)">
          <div id="ws-form-error"></div>
          <div class="ws-form-group">
            <label for="ws-name">Full Name *</label>
            <input type="text" id="ws-name" name="name" required placeholder="John Smith">
          </div>
          <div class="ws-form-group">
            <label for="ws-email">Email Address *</label>
            <input type="email" id="ws-email" name="email" required placeholder="john@example.com">
          </div>
          <div class="ws-form-group">
            <label for="ws-phone">Phone Number</label>
            <input type="tel" id="ws-phone" name="phone" placeholder="(555) 123-4567">
          </div>
          <div class="ws-form-group">
            <label for="ws-notes">Notes (optional)</label>
            <textarea id="ws-notes" name="notes" placeholder="Any special requests or information..."></textarea>
          </div>
          <button type="submit" class="ws-submit" id="ws-submit-btn">
            Request Booking
          </button>
        </form>
      `;
    }
    
    renderSuccess() {
      return `
        <div class="ws-success">
          <div class="ws-success-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
          </div>
          <h3>Booking Request Sent!</h3>
          <p>Please check your email to verify your booking. Once verified, the provider will review and confirm your appointment.</p>
        </div>
      `;
    }
    
    async handleSubmit(event) {
      event.preventDefault();
      
      const form = event.target;
      const submitBtn = document.getElementById('ws-submit-btn');
      const errorDiv = document.getElementById('ws-form-error');
      
      const formData = {
        name: form.name.value,
        email: form.email.value,
        phone: form.phone.value,
        notes: form.notes.value
      };
      
      submitBtn.disabled = true;
      submitBtn.textContent = 'Submitting...';
      errorDiv.innerHTML = '';
      
      try {
        await this.submitBooking(formData);
      } catch (error) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Request Booking';
        errorDiv.innerHTML = `<div class="ws-error">${error.message}</div>`;
      }
    }
    
    render() {
      let content = '';
      
      // Header
      content += `
        <div class="ws-header">
          <h2>${this.providerInfo?.business_name || 'Book an Appointment'}</h2>
          <p>Select a date and time that works for you</p>
        </div>
        <div class="ws-content">
      `;
      
      // Content based on step
      switch (this.step) {
        case 'calendar':
          if (this.availability.length === 0) {
            content += '<div class="ws-loading"><div class="ws-spinner"></div></div>';
          } else {
            content += this.renderCalendar();
          }
          break;
        case 'slots':
          content += this.renderSlots();
          break;
        case 'form':
          content += this.renderForm();
          break;
        case 'success':
          content += this.renderSuccess();
          break;
      }
      
      content += '</div>';
      
      this.container.innerHTML = `<div class="ws-container">${content}</div>`;
    }
  }

  // Public API
  window.WorkSlot = {
    init: function(options) {
      window._wsWidget = new WorkSlotWidget(options);
      return window._wsWidget;
    }
  };

})(window);

