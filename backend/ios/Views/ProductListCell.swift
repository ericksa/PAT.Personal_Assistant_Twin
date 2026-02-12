import SwiftUI

struct ProductListCell: View {
    let product: Product
    
    var body: some View {
        HStack {
            Image("ProductIcon")
                .resizable()
                .frame(width: 40, height: 40)
                .clipShape(Circle())
            
            VStack(alignment: .leading) {
                Text(product.name)
                    .font(.headline)
                Text("$\(product.price, specifier: "%.2f")")
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