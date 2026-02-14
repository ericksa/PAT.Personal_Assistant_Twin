// swift-tools-version:5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "PATApp",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(
            name: "PATApp",
            targets: ["PATApp"]
        ),
    ],
    dependencies: [
        // No external dependencies - using Swift standard library only
    ],
    targets: [
        .executableTarget(
            name: "PATApp",
            dependencies: [],
            path: ".",
            exclude: [
                "Tests",
                "Preview Content"
            ],
            sources: [
                "PATApp",
                "Models",
                "ViewModels",
                "Views",
                "Services",
                "Utilities"
            ]
        ),
        .testTarget(
            name: "PATAppTests",
            dependencies: ["PATApp"],
            path: "Tests"
        ),
    ]
)
