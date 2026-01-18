from datetime import datetime, timedelta, date, time
from typing import List, Dict, Any
from .models import Booking

def generate_slots(
    date_obj: date, 
    availability_config: Dict[str, Any], 
    existing_bookings: List[Booking]
) -> List[Dict[str, Any]]:
    """
    Generate available slots for a given date based on config and existing bookings.
    Supports legacy schema (start_time/end_time) and new flexible schema (day_schedules).
    """
    if not availability_config:
        return []
    
    day_name = date_obj.strftime("%a")
    dur_val = availability_config.get("slot_duration")
    if dur_val is None:
        dur_val = 30
    duration_min = int(dur_val)
    potential_slots = []

    # --- Strategy Selection ---
    # New Schema: "day_schedules": { "Mon": [ {type: 'window', start: '09:00', end: '12:00'} ] }
    if "day_schedules" in availability_config:
        day_config = availability_config["day_schedules"].get(day_name, [])
        if not day_config:
            return [] # Not working today
            
        for block in day_config:
            block_type = block.get("type", "window")
            start_str = block.get("start")
            
            if not start_str: continue

            start_dt = datetime.combine(date_obj, datetime.strptime(start_str, "%H:%M").time())
            
            if block_type == "specific":
                # Single fixed slot
                # If duration is custom (0), default specific slots to 30m? Or maybe 60m? 
                # Let's use 60m as a reasonable default for a "visit", or fallback to 30.
                actual_duration = duration_min if duration_min > 0 else 60
                slot_end = start_dt + timedelta(minutes=actual_duration)
                potential_slots.append({
                    "start": start_dt,
                    "end": slot_end,
                    "label": start_dt.strftime("%H:%M")
                })
            
            elif block_type == "window":
                # Range of slots
                end_str = block.get("end")
                if not end_str: continue
                
                end_dt = datetime.combine(date_obj, datetime.strptime(end_str, "%H:%M").time())
                
                # If Duration is Custom (0), treat the entire window as ONE slot
                if duration_min <= 0:
                     potential_slots.append({
                        "start": start_dt,
                        "end": end_dt,
                        "label": f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
                    })
                     continue

                # Standard Fixed Slicing
                current = start_dt
                while current + timedelta(minutes=duration_min) <= end_dt:
                    slot_end = current + timedelta(minutes=duration_min)
                    potential_slots.append({
                        "start": current,
                        "end": slot_end,
                        "label": current.strftime("%H:%M")
                    })
                    current = slot_end

    # Legacy Schema Fallback: "working_days": ["Mon"], "start_time": "09:00"...
    else:
        working_days = availability_config.get("working_days", [])
        if day_name not in working_days:
            return []

        start_str = availability_config.get("start_time", "09:00")
        end_str = availability_config.get("end_time", "17:00")
        
        start_dt = datetime.combine(date_obj, datetime.strptime(start_str, "%H:%M").time())
        end_dt = datetime.combine(date_obj, datetime.strptime(end_str, "%H:%M").time())
        
        current = start_dt
        while current + timedelta(minutes=duration_min) <= end_dt:
            slot_end = current + timedelta(minutes=duration_min)
            potential_slots.append({
                "start": current,
                "end": slot_end,
                "label": current.strftime("%H:%M")
            })
            current = slot_end
        
    # --- Filter against Bookings ---
    final_slots = []
    
    # Sort potential slots by time to be neat
    potential_slots.sort(key=lambda x: x["start"])

    for slot in potential_slots:
        is_blocked = False
        for booking in existing_bookings:
            if booking.status in ["declined", "expired"]:
                continue
                
            b_start = booking.start_time
            b_end = booking.end_time
            
            # Intersection Check
            if (slot["start"] < b_end) and (slot["end"] > b_start):
                is_blocked = True
                break
        
        if not is_blocked:
            final_slots.append(slot)
            
    return final_slots
