import Foundation

extension String {
    var isEmail: Bool {
        let emailRegEx = "[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,64}"
        let emailTest = NSPredicate(format:"SELF MATCHES %@", emailRegEx)
        return emailTest.evaluate(with: self)
    }
    
    var isNumeric: Bool {
        return !self.isEmpty && self.rangeOfCharacter(from: CharacterSet.decimalDigits.inverted) == nil
    }
    
    var trimmed: String {
        return self.trimmingCharacters(in: .whitespacesAndNewlines)
    }
    
    func isValidURL() -> Bool {
        if let url = URL(string: self) {
            return UIApplication.shared.canOpenURL(url)
        }
        return false
    }
}