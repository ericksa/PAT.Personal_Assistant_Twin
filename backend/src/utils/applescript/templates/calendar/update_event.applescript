-- Update an existing event in Apple Calendar
on update_event(event_id, new_title, new_start_time, new_end_time, new_location, new_notes)
    tell application "Calendar"
        -- Get the event by ID
        set target_event to first event whose id is event_id
        
        -- Update event properties
        tell target_event
            if new_title is not "" then set summary to new_title
            if new_start_time is not "" then set start date to date new_start_time
            if new_end_time is not "" then set end date to date new_end_time
            if new_location is not "" then set location to new_location
            if new_notes is not "" then set description to new_notes
        end tell
        
        return id of target_event
    end tell
end update_event
