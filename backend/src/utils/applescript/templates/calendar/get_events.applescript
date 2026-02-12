-- Get events from Apple Calendar within a date range
on get_events(start_time, end_time, calendar_name)
    tell application "Calendar"
        -- Get the target calendar
        set target_calendar to first calendar whose name is calendar_name
        
        -- Set date range
        set start_date to date start_time
        set end_date to date end_time
        
        -- Fetch events
        set event_list to {}
        tell target_calendar
            set events_in_range to every event whose (start date ≥ start_date and start date ≤ end_date)
            repeat with current_event in events_in_range
                set end of event_list to {
                    id:id of current_event,
                    summary:summary of current_event,
                    start date:start date of current_event,
                    end date:end date of current_event,
                    location:location of current_event,
                    description:description of current_event
                }
            end repeat
        end tell
        
        return event_list
    end tell
end get_events
