"""Seed the database with demo users."""
from app import seed_database

if __name__ == "__main__":
    seed_database()
    print("Database seeded successfully.")
    print("Demo accounts (password: password123):")
    print("  - alice@ajaia.com (Alice Chen)")
    print("  - bob@ajaia.com (Bob Martinez)")
    print("  - carol@ajaia.com (Carol Williams)")
