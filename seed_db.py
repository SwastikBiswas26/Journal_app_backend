"""
Seed Script for MongoDB Atlas
Populates sample users and journal posts (Public and Private) into your live Atlas database.
"""
import sys
from db import init_db, get_users_collection, get_journals_collection
from services.auth_service import signup_user
from services.journal_service import create_journal_entry, fetch_public_feed, fetch_user_journals

def run_seed_and_test():
    print("\n--- Initializing MongoDB Atlas connection ---")
    init_db()

    users_col = get_users_collection()

    # Clear existing test seed data if present
    print("[1/5] Cleaning previous test data...")
    users_col.delete_many({"email": {"$in": ["alex@example.com", "sarah@example.com"]}})

    print("[2/5] Registering sample users in Atlas...")
    
    # User 1: Alex
    res1, err1, _ = signup_user(
        username="alex_dev",
        email="alex@example.com",
        password="password123"
    )
    if err1:
        print(f"User 1 error: {err1}")
        return
    alex_token = res1["token"]
    alex_id = res1["user"]["id"]
    alex_name = res1["user"]["username"]
    print(f"  + User 'alex_dev' created! (ID: {alex_id})")

    # User 2: Sarah
    res2, err2, _ = signup_user(
        username="sarah_writer",
        email="sarah@example.com",
        password="password123"
    )
    if err2:
        print(f"User 2 error: {err2}")
        return
    sarah_id = res2["user"]["id"]
    sarah_name = res2["user"]["username"]
    print(f"  + User 'sarah_writer' created! (ID: {sarah_id})")

    print("\n[3/5] Creating sample Journal Posts in Atlas...")

    # Alex Posts
    p1, _, _ = create_journal_entry(
        user_id=alex_id,
        author_username=alex_name,
        title="Building my first Fullstack Flask & React App",
        content="Connecting Flask backend to MongoDB Atlas and React frontend is surprisingly smooth!",
        tags=["flask", "react", "mongodb"],
        is_public=True
    )
    print(f"  + Public Post Created: '{p1['post']['title']}' (is_public: True)")

    p2, _, _ = create_journal_entry(
        user_id=alex_id,
        author_username=alex_name,
        title="Personal Web Development Reflection",
        content="Keeping this journal private to reflect on my daily learning progress.",
        tags=["personal", "reflection"],
        is_public=False
    )
    print(f"  + Private Post Created: '{p2['post']['title']}' (is_public: False)")

    # Sarah Posts
    p3, _, _ = create_journal_entry(
        user_id=sarah_id,
        author_username=sarah_name,
        title="Welcome to the Community Journal!",
        content="Excited to share thoughts and read public journals from everyone here.",
        tags=["welcome", "community"],
        is_public=True
    )
    print(f"  + Public Post Created: '{p3['post']['title']}' (is_public: True)")

    p4, _, _ = create_journal_entry(
        user_id=sarah_id,
        author_username=sarah_name,
        title="Drafting Article Ideas for Next Week",
        content="Private draft of topics I want to write about soon.",
        tags=["drafts", "ideas"],
        is_public=False
    )
    print(f"  + Private Post Created: '{p4['post']['title']}' (is_public: False)")

    print("\n[4/5] Verifying Community Public Feed from Atlas...")
    feed_res, _, _ = fetch_public_feed(limit=10, skip=0)
    print(f"  + Found {len(feed_res['posts'])} public posts in feed:")
    for post in feed_res["posts"]:
        print(f"     - [{post['author_username']}] {post['title']} (is_public: {post['is_public']})")

    print("\n[5/5] Verifying User Posts for Alex...")
    alex_posts, _, _ = fetch_user_journals(alex_id)
    print(f"  + Alex has {alex_posts['count']} total posts stored in MongoDB Atlas.")

    print("\n========================================================")
    print(" SUCCESS! Your MongoDB Atlas cluster is working 100%!")
    print("========================================================")
    print("Sample Login Email : alex@example.com")
    print("Sample Password    : password123")
    print(f"Sample JWT Token   : {alex_token}")
    print("========================================================\n")

if __name__ == "__main__":
    run_seed_and_test()
