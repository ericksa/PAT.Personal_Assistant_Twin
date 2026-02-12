-- Create a new reminder in Apple Reminders
on create_reminder(title, due_date, notes, priority, list_name)
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
        
        -- Create the reminder
        set newReminder to make new reminder at end of reminders of theList
        set name of newReminder to title
        
        -- Set due date if provided
        if due_date is not "" then
            set due date of newReminder to date due_date
        end if
        
        -- Set notes if provided
        if notes is not "" then
            set body of newReminder to notes
        end if
        
        -- Set priority if provided (1=high, 2=medium, 3=low, 9=none)
        if priority is not "" then
            set priority of newReminder to priority
        end if
        
        -- Return the ID of the new reminder
        return id of newReminder
    end tell
end create_reminder
