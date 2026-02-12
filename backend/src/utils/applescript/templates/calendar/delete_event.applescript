-- Delete an event from Apple Calendar
on delete_event(event_id)
    tell application "Calendar"
        -- Get the event by ID
        set target_event to first event whose id is event_id
        
        -- Delete the event
        delete target_event
        
        return "Event deleted successfully"
    end tell
end delete_event
