-- Create a new event in Apple Calendar
on create_event(title, start_time, end_time, location, notes, calendar_name)
    tell application "Calendar"
        -- Get the target calendar
        set target_calendar to first calendar whose name is calendar_name
        
        -- Create the event
        tell target_calendar
            set new_event to make new event with properties {
                summary:title,
                start date:date start_time,
                end date:date end_time,
                location:location,
                description:notes
            }
            return id of new_event
        end tell
    end tell
end create_event
