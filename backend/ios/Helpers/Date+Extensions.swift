import Foundation

extension Date {
    func toString(format: String = "yyyy-MM-dd HH:mm:ss") -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = format
        return formatter.string(from: self)
    }
    
    static func fromString(_ dateString: String, format: String = "yyyy-MM-dd HH:mm:ss") -> Date? {
        let formatter = DateFormatter()
        formatter.dateFormat = format
        return formatter.date(from: dateString)
    }
    
    func timeAgoSinceDate() -> String {
        let calendar = Calendar.current
        let unitFlags: Set<Calendar.Component> = [.minute, .hour, .day, .weekOfYear, .month, .year, .second]
        let now = Date()
        let earliest = now < self ? now : self
        let latest = (earliest == now) ? self : now
        let components = calendar.dateComponents(unitFlags, from: earliest, to: latest)
        
        if let year = components.year, year >= 2 {
            return "\(year) years ago"
        }
        
        if let month = components.month, month >= 2 {
            return "\(month) months ago"
        }
        
        if let week = components.weekOfYear, week >= 2 {
            return "\(week) weeks ago"
        }
        
        if let day = components.day, day >= 2 {
            return "\(day) days ago"
        }
        
        if let hour = components.hour, hour >= 2 {
            return "\(hour) hours ago"
        }
        
        if let minute = components.minute, minute >= 2 {
            return "\(minute) minutes ago"
        }
        
        if let second = components.second, second >= 3 {
            return "\(second) seconds ago"
        }
        
        return "Just now"
    }
}