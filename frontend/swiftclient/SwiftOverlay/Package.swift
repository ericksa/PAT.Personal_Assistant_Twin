// swift-tools-version:5.5
import PackageDescription

let package = Package(
    name: "PATOverlay",
    platforms: [
        .macOS(.v12)
    ],
    products: [
        .executable(
            name: "PATOverlay",
            targets: ["PATOverlay"]
        )
    ],
    targets: [
        .executableTarget(
            name: "PATOverlay",
            dependencies: [],
            path: ".",
            exclude: ["README.md", "build.sh", "Info.plist"],
            resources: []
        )
    ]
)