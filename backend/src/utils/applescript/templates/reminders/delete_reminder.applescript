-- Delete a reminder from Apple Reminders
on delete_reminder(reminder_id)
    tell application "Reminders"
        -- Find the reminder by ID and delete it
        delete reminder id reminder_id
        return "Reminder deleted successfully"
    end tell
end delete_reminder
