import SwiftUI

struct OrderListCell: View {
    let order: Order
    
    var body: some View {
        HStack {
            Image("OrderIcon")
                .resizable()
                .frame(width: 40, height: 40)
                .clipShape(Circle())
            
            VStack(alignment: .leading) {
                Text("Order #\(order.id)")
                    .font(.headline)
                Text("Total: $\(order.total, specifier: "%.2f")")
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