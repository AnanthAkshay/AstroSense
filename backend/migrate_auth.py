#!/usr/bin/env python3
"""
Database migration script for AstroSense authentication tables
Run this to add the auth tables to your existing database
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment"""
    return os.getenv('DATABASE_URL')

def create_auth_tables():
    """Create authentication tables"""
    
    # SQL to create auth tables
    auth_tables_sql = """
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    );

    -- Sessions table
    CREATE TABLE IF NOT EXISTS sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        token VARCHAR(255) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    );

    -- OTP temporary storage
    CREATE TABLE IF NOT EXISTS otps (
        email VARCHAR(255) PRIMARY KEY,
        otp_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        attempts INTEGER DEFAULT 0
    );

    -- Indexes for authentication tables
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
    CREATE INDEX IF NOT EXISTS idx_otps_expires_at ON otps(expires_at);
    """
    
    database_url = get_database_url()
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL not found in environment variables")
        print("Make sure you have a .env file with DATABASE_URL set")
        return False
    
    try:
        print("🔗 Connecting to database...")
        print(f"Database: {database_url.split('@')[-1] if '@' in database_url else 'localhost'}")
        
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("📋 Creating authentication tables...")
        
        # Execute the SQL
        cursor.execute(auth_tables_sql)
        conn.commit()
        
        print("✅ Authentication tables created successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'sessions', 'otps')
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"📊 Created tables: {', '.join([t['table_name'] for t in tables])}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Database migration completed successfully!")
        print("You can now start the backend server and use authentication.")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_existing_tables():
    """Check if auth tables already exist"""
    database_url = get_database_url()
    
    if not database_url:
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'sessions', 'otps');
        """)
        
        existing_tables = [row['table_name'] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        if existing_tables:
            print(f"ℹ️  Found existing auth tables: {', '.join(existing_tables)}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 AstroSense Authentication Database Migration")
    print("=" * 50)
    
    # Check if tables already exist
    if check_existing_tables():
        response = input("\n⚠️  Some auth tables already exist. Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return
    
    # Create the tables
    success = create_auth_tables()
    
    if success:
        print("\n📝 Next steps:")
        print("1. Install Python dependencies: pip install bcrypt email-validator")
        print("2. Start the backend: python main.py")
        print("3. Go to dashboard and try logging in!")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()