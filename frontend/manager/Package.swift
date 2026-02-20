// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "PATManager",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(
            name: "PATManager",
            targets: ["PATManager"]
        )
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "PATManager",
            dependencies: [],
            path: "PATManager",
            exclude: ["Info.plist"],
            swiftSettings: [
                .enableExperimentalFeature("StrictConcurrency")
            ]
        )
    ]
)
