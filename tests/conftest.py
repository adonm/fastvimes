"""Pytest configuration with multi-schema fixtures for FastVimes testing."""

import pytest
from pathlib import Path
from fastvimes.database_service import DatabaseService

# Multi-schema test configurations
SCHEMA_CONFIGS = {
    'default_sample': {
        'description': 'Default sample schema with users, products, orders',
        'create_sample_data': True,
        'expected_tables': ['users', 'products', 'orders']
    },
    'nyc_taxi': {
        'description': 'NYC Taxi data with different column names and structure',
        'create_sample_data': False,
        'setup_queries': [
            # Create a table from NYC taxi data with different schema
            """
            CREATE TABLE trips AS 
            SELECT 
                passenger_count,
                trip_distance,
                fare_amount,
                tip_amount,
                total_amount,
                tpep_pickup_datetime as pickup_datetime,
                tpep_dropoff_datetime as dropoff_datetime
            FROM 'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2021-01.parquet'
            LIMIT 1000
            """,
            # Create another table with different structure
            """
            CREATE TABLE trip_summary AS
            SELECT 
                DATE(pickup_datetime) as trip_date,
                COUNT(*) as total_trips,
                AVG(fare_amount) as avg_fare,
                SUM(tip_amount) as total_tips
            FROM trips
            GROUP BY DATE(pickup_datetime)
            """
        ],
        'expected_tables': ['trips', 'trip_summary']
    },
    'financial_data': {
        'description': 'Financial data with different naming conventions',
        'create_sample_data': False,
        'setup_queries': [
            # Create financial tables with different naming patterns
            """
            CREATE TABLE financial_instruments (
                symbol VARCHAR(10),
                name VARCHAR(100),
                sector VARCHAR(50),
                market_cap DECIMAL(15,2),
                price DECIMAL(10,2),
                volume INTEGER,
                last_updated TIMESTAMP
            )
            """,
            """
            INSERT INTO financial_instruments VALUES
            ('AAPL', 'Apple Inc.', 'Technology', 2500000000000.00, 150.25, 50000000, '2024-01-15 16:00:00'),
            ('GOOGL', 'Alphabet Inc.', 'Technology', 1800000000000.00, 2750.80, 25000000, '2024-01-15 16:00:00'),
            ('MSFT', 'Microsoft Corporation', 'Technology', 2200000000000.00, 350.40, 30000000, '2024-01-15 16:00:00'),
            ('TSLA', 'Tesla Inc.', 'Automotive', 800000000000.00, 250.60, 45000000, '2024-01-15 16:00:00')
            """,
            """
            CREATE TABLE trading_sessions (
                session_id UUID DEFAULT gen_random_uuid(),
                symbol VARCHAR(10),
                open_price DECIMAL(10,2),
                close_price DECIMAL(10,2),
                high_price DECIMAL(10,2),
                low_price DECIMAL(10,2),
                session_date DATE,
                session_volume INTEGER
            )
            """,
            """
            INSERT INTO trading_sessions (symbol, open_price, close_price, high_price, low_price, session_date, session_volume) VALUES
            ('AAPL', 149.50, 150.25, 151.00, 148.80, '2024-01-15', 50000000),
            ('GOOGL', 2745.00, 2750.80, 2760.50, 2740.20, '2024-01-15', 25000000),
            ('MSFT', 348.90, 350.40, 352.10, 347.50, '2024-01-15', 30000000),
            ('TSLA', 248.20, 250.60, 255.30, 246.80, '2024-01-15', 45000000)
            """
        ],
        'expected_tables': ['financial_instruments', 'trading_sessions']
    },
    'blog_platform': {
        'description': 'Blog platform schema with different relationships',
        'create_sample_data': False,
        'setup_queries': [
            """
            CREATE TABLE authors (
                author_id INTEGER PRIMARY KEY,
                username VARCHAR(50) UNIQUE,
                email_address VARCHAR(100),
                full_name VARCHAR(100),
                bio TEXT,
                registration_date TIMESTAMP,
                is_verified BOOLEAN DEFAULT FALSE
            )
            """,
            """
            INSERT INTO authors VALUES
            (1, 'techwriter', 'tech@example.com', 'Jane Smith', 'Technology enthusiast', '2023-01-01 10:00:00', TRUE),
            (2, 'foodblogger', 'food@example.com', 'John Doe', 'Culinary expert', '2023-02-15 14:30:00', TRUE),
            (3, 'traveler', 'travel@example.com', 'Alice Johnson', 'World explorer', '2023-03-20 09:15:00', FALSE)
            """,
            """
            CREATE TABLE blog_posts (
                post_id INTEGER PRIMARY KEY,
                title VARCHAR(200),
                slug VARCHAR(200),
                content TEXT,
                author_id INTEGER,
                published_at TIMESTAMP,
                status VARCHAR(20) DEFAULT 'draft',
                view_count INTEGER DEFAULT 0,
                FOREIGN KEY (author_id) REFERENCES authors(author_id)
            )
            """,
            """
            INSERT INTO blog_posts VALUES
            (1, 'Introduction to DuckDB', 'intro-to-duckdb', 'DuckDB is amazing...', 1, '2024-01-10 12:00:00', 'published', 1250),
            (2, 'Best Pasta Recipes', 'best-pasta-recipes', 'Here are my favorite pasta dishes...', 2, '2024-01-12 15:30:00', 'published', 890),
            (3, 'Travel Guide to Japan', 'japan-travel-guide', 'Japan is a wonderful country...', 3, '2024-01-15 08:45:00', 'draft', 0)
            """,
            """
            CREATE TABLE post_comments (
                comment_id INTEGER PRIMARY KEY,
                post_id INTEGER,
                commenter_name VARCHAR(100),
                comment_text TEXT,
                comment_date TIMESTAMP,
                is_approved BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (post_id) REFERENCES blog_posts(post_id)
            )
            """,
            """
            INSERT INTO post_comments VALUES
            (1, 1, 'Developer123', 'Great article! Very informative.', '2024-01-10 14:30:00', TRUE),
            (2, 1, 'DataAnalyst', 'Thanks for sharing this.', '2024-01-11 09:15:00', TRUE),
            (3, 2, 'FoodLover', 'Cannot wait to try these recipes!', '2024-01-12 18:00:00', TRUE),
            (4, 2, 'ChefMike', 'Great tips on pasta cooking.', '2024-01-13 11:45:00', FALSE)
            """
        ],
        'expected_tables': ['authors', 'blog_posts', 'post_comments']
    }
}


@pytest.fixture(params=list(SCHEMA_CONFIGS.keys()))
def multi_schema_db(request):
    """Create test database with different schema patterns to validate autogeneration."""
    schema_name = request.param
    config = SCHEMA_CONFIGS[schema_name]
    
    # Create in-memory database
    service = DatabaseService(Path(":memory:"), create_sample_data=config['create_sample_data'])
    
    # Run setup queries if provided
    if 'setup_queries' in config:
        for query in config['setup_queries']:
            try:
                service.connection.execute(query)
            except Exception as e:
                # Skip if external data source is unavailable (e.g., in CI)
                if 'nyc_taxi' in schema_name and 'HTTP' in str(e):
                    pytest.skip(f"External data source unavailable for {schema_name}: {e}")
                else:
                    raise
    
    # Store expected tables for validation
    service._test_expected_tables = config['expected_tables']
    service._test_schema_name = schema_name
    service._test_description = config['description']
    
    yield service
    service.close()


@pytest.fixture
def default_db_service():
    """Create default test database service for compatibility."""
    service = DatabaseService(Path(":memory:"), create_sample_data=True)
    yield service
    service.close()


# Mark tests that require external data sources
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "external_data: mark test as requiring external data sources"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to mark external data tests."""
    for item in items:
        if "nyc_taxi" in str(item.nodeid):
            item.add_marker(pytest.mark.external_data)
