import SwiftUI

struct OrderDetailView: View {
    let order: Order
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("Order Details")
                    .font(.largeTitle)
                    .bold()
                    .padding(.bottom, 20)
                
                HStack {
                    Text("Order ID:")
                        .font(.headline)
                    Text("\(order.id)")
                        .font(.body)
                }
                
                HStack {
                    Text("User ID:")
                        .font(.headline)
                    Text("\(order.userId)")
                        .font(.body)
                }
                
                HStack {
                    Text("Total:")
                        .font(.headline)
                    Text("$\(order.total, specifier: "%.2f")")
                        .font(.body)
                }
                
                HStack {
                    Text("Status:")
                        .font(.headline)
                    Text(order.status)
                        .font(.body)
                }
                
                HStack {
                    Text("Created:")
                        .font(.headline)
                    Text(order.createdAt)
                        .font(.body)
                }
                
                Spacer()
            }
            .padding()
        }
        .navigationTitle("Order #\(order.id)")
        .navigationBarTitleDisplayMode(.inline)
    }
}