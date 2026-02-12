-- Get reminders from Apple Reminders within a date range
on get_reminders(start_date, end_date, list_name)
    tell application "Reminders"
        -- Use the specified list or default to the first list
        if list_name is not "" then
            set theList to list list_name
            if (count of theList) is 0 then
                set theList to first list
            else
                set theList to item 1 of theList
            end if
        else
            set theList to first list
        end if
        
        -- Set date range
        set startDate to date start_date
        set endDate to date end_date
        
        -- Get reminders within the date range
        set matchingReminders to {}
        repeat with aReminder in reminders of theList
            if due date of aReminder is not missing value then
                if (due date of aReminder) ≥ startDate and (due date of aReminder) ≤ endDate then
                    set end of matchingReminders to {id:id of aReminder, name:name of aReminder, due date:due date of aReminder, body:body of aReminder, priority:priority of aReminder, completed:completed of aReminder}
                end if
            end if
        end repeat
        
        -- Return matching reminders
        return matchingReminders
    end tell
end get_reminders
