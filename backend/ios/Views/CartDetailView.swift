import SwiftUI

struct CartDetailView: View {
    let cartItem: CartItem
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("Cart Item Details")
                    .font(.largeTitle)
                    .bold()
                    .padding(.bottom, 20)
                
                HStack {
                    Text("Product ID:")
                        .font(.headline)
                    Text("\(cartItem.productId)")
                        .font(.body)
                }
                
                HStack {
                    Text("Quantity:")
                        .font(.headline)
                    Text("\(cartItem.quantity)")
                        .font(.body)
                }
                
                Spacer()
            }
            .padding()
        }
        .navigationTitle("Cart Item #\(cartItem.productId)")
        .navigationBarTitleDisplayMode(.inline)
    }
}