import SwiftUI

struct UserDetailView: View {
    let user: User
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("User Details")
                    .font(.largeTitle)
                    .bold()
                    .padding(.bottom, 20)
                
                HStack {
                    Text("Name:")
                        .font(.headline)
                    Text(user.name)
                        .font(.body)
                }
                
                HStack {
                    Text("Email:")
                        .font(.headline)
                    Text(user.email)
                        .font(.body)
                }
                
                HStack {
                    Text("Role:")
                        .font(.headline)
                    Text(user.role)
                        .font(.body)
                }
                
                Spacer()
            }
            .padding()
        }
        .navigationTitle(user.name)
        .navigationBarTitleDisplayMode(.inline)
    }
}