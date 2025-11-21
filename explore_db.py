import psycopg2
from psycopg2 import sql

def get_tables():
    try:
        # Try connecting to database 'cdm'
        conn = psycopg2.connect(
            dbname="cdm",
            user="smathias",
            host="localhost"
        )
        cur = conn.cursor()
        
        # List tables in public schema
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print("Tables found:")
        for table in tables:
            print(f"- {table[0]}")
            
            # Get columns for each table
            cur.execute(sql.SQL("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = {}
            """).format(sql.Literal(table[0])))
            columns = cur.fetchall()
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_tables()
