import XCTest
import Combine
@testable import PATclient

final class EmailIntegrationTests: XCTestCase {
    var coreService: PATCoreService!
    var cancellables: Set<AnyCancellable>!
    
    override func setUp() {
        super.setUp()
        coreService = PATCoreService.shared
        cancellables = []
    }
    
    func testEmailModels() throws {
        let json = """
        {
            "id": "0f7b1e9c-77c1-4930-b55d-5380b8f7069c",
            "subject": "Test Email",
            "sender_email": "test@example.com",
            "sender_name": "Test User",
            "received_at": "2024-02-12T10:00:00Z",
            "read": false,
            "flagged": true,
            "category": "work",
            "priority": 5,
            "folder": "INBOX"
        }
        """.data(using: .utf8)!
        
        let email = try JSONDecoder().decode(PATEmail.self, from: json)
        XCTAssertEqual(email.subject, "Test Email")
        XCTAssertEqual(email.category, .work)
        XCTAssertTrue(email.flagged)
    }
    
    func testEmailAnalyticsModel() throws {
        let json = """
        {
            "total_emails": 10,
            "unread_count": 5,
            "flagged_count": 2,
            "urgent_count": 1,
            "categories": {"work": 5, "personal": 5}
        }
        """.data(using: .utf8)!
        
        let analytics = try JSONDecoder().decode(EmailAnalytics.self, from: json)
        XCTAssertEqual(analytics.totalEmails, 10)
        XCTAssertEqual(analytics.categories["work"], 5)
    }
    
    // Note: These tests require the PAT Core API to be running on localhost:8010
    func testFetchAnalyticsLive() async throws {
        do {
            let analytics = try await coreService.getEmailAnalytics()
            XCTAssertNotNil(analytics)
            print("Successfully fetched analytics: \(analytics!)")
        } catch {
            XCTFail("Failed to fetch analytics: \(error)")
        }
    }
    
    func testListEmailsLive() async throws {
        do {
            let emails = try await coreService.listEmails()
            XCTAssertNotNil(emails)
            print("Successfully fetched \(emails.count) emails")
        } catch {
            XCTFail("Failed to fetch emails: \(error)")
        }
    }
}
