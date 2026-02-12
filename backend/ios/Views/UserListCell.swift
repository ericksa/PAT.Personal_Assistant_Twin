import SwiftUI

struct UserListCell: View {
    let user: User
    
    var body: some View {
        HStack {
            Image("UserIcon")
                .resizable()
                .frame(width: 40, height: 40)
                .clipShape(Circle())
            
            VStack(alignment: .leading) {
                Text(user.name)
                    .font(.headline)
                Text(user.email)
                    .font(.subheadline)
                    .foregroundColor(.gray)
            }
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .foregroundColor(.gray)
        }
        .padding()
        .background(Color(.systemGroupedBackground))
        .cornerRadius(10)
        .padding(.horizontal)
    }
}