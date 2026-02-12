"""
Test migration 003: Add domain and category support to documents table
"""

import pytest
from unittest.mock import MagicMock, patch
import psycopg2


class TestMigration003DomainSupport:
    """Test database schema migration for domain and category support"""

    def test_migration_adds_domain_column(self, mock_database):
        """Test that migration adds domain column to documents table"""
        mock_conn, mock_cursor = mock_database

        # Act: Execute migration logic (this will fail initially)
        migration_003.execute(mock_conn)

        # Assert: Verify ALTER TABLE statement for domain column
        mock_cursor.execute.assert_any_call(
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS domain VARCHAR(50) DEFAULT 'general'"
        )

    def test_migration_adds_category_column(self, mock_database):
        """Test that migration adds category column to documents table"""
        mock_conn, mock_cursor = mock_database

        # Act: Execute migration logic
        migration_003.execute(mock_conn)

        # Assert: Verify ALTER TABLE statement for category column
        mock_cursor.execute.assert_any_call(
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT 'personal'"
        )

    def test_migration_creates_domain_index(self, mock_database):
        """Test that migration creates index on domain column"""
        mock_conn, mock_cursor = mock_database

        # Act: Execute migration logic
        migration_003.execute(mock_conn)

        # Assert: Verify index creation for domain
        mock_cursor.execute.assert_any_call(
            "CREATE INDEX IF NOT EXISTS idx_documents_domain ON documents(domain)"
        )

    def test_migration_creates_category_index(self, mock_database):
        """Test that migration creates index on category column"""
        mock_conn, mock_cursor = mock_database

        # Act: Execute migration logic
        migration_003.execute(mock_conn)

        # Assert: Verify index creation for category
        mock_cursor.execute.assert_any_call(
            "CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category)"
        )

    def test_migration_preserves_existing_data(self, mock_database):
        """Test that migration preserves existing data with default values"""
        mock_conn, mock_cursor = mock_database

        # Arrange: Mock existing data without domain/category
        existing_data = [
            {"id": "doc1", "filename": "old_doc.pdf", "content": "old content"},
            {"id": "doc2", "filename": "another_doc.pdf", "content": "more content"},
        ]
        mock_cursor.fetchall.return_value = existing_data

        # Act: Execute migration logic
        migration_003.execute(mock_conn)

        # Assert: Verify existing data gets defaults when queried
        mock_cursor.execute.assert_any_call(
            "SELECT id, filename, content, COALESCE(domain, 'general') as domain, COALESCE(category, 'personal') as category FROM documents"
        )

    def test_migration_handles_concurrent_schemes(self, mock_database):
        """Test that migration handles concurrent schema changes safely"""
        mock_conn, mock_cursor = mock_database

        # Act: Execute migration logic
        migration_003.execute(mock_conn)

        # Assert: Verify IF NOT EXISTS clauses are used
        execute_calls = [str(call[0][0]) for call in mock_cursor.execute.call_args_list]

        assert any("ADD COLUMN IF NOT EXISTS" in call for call in execute_calls)
        assert any("CREATE INDEX IF NOT EXISTS" in call for call in execute_calls)

    def test_migration_connection_handling(self, mock_database):
        """Test that migration properly handles database connection"""
        mock_conn, mock_cursor = mock_database

        # Act: Execute migration logic
        migration_003.execute(mock_conn)

        # Assert: Verify connection is committed
        mock_conn.commit.assert_called_once()

    def test_migration_error_handling(self):
        """Test that migration handles database errors gracefully"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Arrange: Mock database error
        mock_cursor.execute.side_effect = psycopg2.Error("Database error")
        mock_conn.rollback.return_value = None

        # Act & Assert: Should handle error without raising
        try:
            migration_003.execute(mock_conn)
            assert False, "Should have raised exception"
        except Exception:
            # Exception should be re-raised
            pass

        # Verify rollback was called
        mock_conn.rollback.assert_called_once()


# Placeholder for migration module (will be implemented to pass tests)
class Migration003:
    """Placeholder for migration 003 implementation"""

    @staticmethod
    def execute(connection):
        """Execute migration 003 - Add domain and category support"""
        raise NotImplementedError("Migration 003 not yet implemented")


# Global variable for the migration to be implemented
migration_003 = Migration003
