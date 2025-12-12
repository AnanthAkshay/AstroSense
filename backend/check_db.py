#!/usr/bin/env python3
"""
Database connection checker for AstroSense
Run this to verify your database connection and see existing tables
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_database_connection():
    """Check database connection and show table info"""
    
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL not found in environment variables")
        print("Make sure you have a .env file with DATABASE_URL set")
        return False
    
    try:
        print("🔗 Testing database connection...")
        print(f"Database: {database_url.split('@')[-1] if '@' in database_url else 'localhost'}")
        
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("✅ Database connection successful!")
        
        # Check existing tables
        cursor.execute("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name AND table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n📊 Found {len(tables)} tables in database:")
            for table in tables:
                print(f"  • {table['table_name']} ({table['column_count']} columns)")
        else:
            print("\n📊 No tables found in database")
        
        # Check specifically for auth tables
        auth_tables = ['users', 'sessions', 'otps']
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = ANY(%s);
        """, (auth_tables,))
        
        existing_auth_tables = [row['table_name'] for row in cursor.fetchall()]
        
        print(f"\n🔐 Authentication tables status:")
        for table in auth_tables:
            status = "✅ EXISTS" if table in existing_auth_tables else "❌ MISSING"
            print(f"  • {table}: {status}")
        
        if len(existing_auth_tables) == len(auth_tables):
            print("\n🎉 All authentication tables are ready!")
        else:
            print(f"\n⚠️  Missing {len(auth_tables) - len(existing_auth_tables)} auth tables")
            print("Run 'python migrate_auth.py' to create them")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify DATABASE_URL in your .env file")
        print("3. Make sure the database exists")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 AstroSense Database Connection Check")
    print("=" * 40)
    check_database_connection()