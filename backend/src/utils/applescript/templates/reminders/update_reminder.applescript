-- Update an existing reminder in Apple Reminders
on update_reminder(reminder_id, new_title, new_due_date, new_notes, new_priority, new_completed)
    tell application "Reminders"
        -- Find the reminder by ID
        set theReminder to reminder id reminder_id
        
        -- Update title if provided
        if new_title is not "" then
            set name of theReminder to new_title
        end if
        
        -- Update due date if provided
        if new_due_date is not "" then
            set due date of theReminder to date new_due_date
        end if
        
        -- Update notes if provided
        if new_notes is not "" then
            set body of theReminder to new_notes
        end if
        
        -- Update priority if provided (1=high, 2=medium, 3=low, 9=none)
        if new_priority is not "" then
            set priority of theReminder to new_priority
        end if
        
        -- Update completion status if provided
        if new_completed is not "" then
            set completed of theReminder to new_completed
        end if
        
        -- Return the ID of the updated reminder
        return id of theReminder
    end tell
end update_reminder
