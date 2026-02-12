import SwiftUI

struct ProductDetailView: View {
    let product: Product
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("Product Details")
                    .font(.largeTitle)
                    .bold()
                    .padding(.bottom, 20)
                
                HStack {
                    Text("Name:")
                        .font(.headline)
                    Text(product.name)
                        .font(.body)
                }
                
                HStack {
                    Text("Description:")
                        .font(.headline)
                    Text(product.description)
                        .font(.body)
                }
                
                HStack {
                    Text("Price:")
                        .font(.headline)
                    Text("$\(product.price, specifier: "%.2f")")
                        .font(.body)
                }
                
                HStack {
                    Text("Category:")
                        .font(.headline)
                    Text(product.category)
                        .font(.body)
                }
                
                Spacer()
            }
            .padding()
        }
        .navigationTitle(product.name)
        .navigationBarTitleDisplayMode(.inline)
    }
}