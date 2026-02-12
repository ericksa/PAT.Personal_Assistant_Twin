import SwiftUI

struct CartListCell: View {
    let cartItem: CartItem
    
    var body: some View {
        HStack {
            Image("CartIcon")
                .resizable()
                .frame(width: 40, height: 40)
                .clipShape(Circle())
            
            VStack(alignment: .leading) {
                Text("Product ID: \(cartItem.productId)")
                    .font(.headline)
                Text("Quantity: \(cartItem.quantity)")
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