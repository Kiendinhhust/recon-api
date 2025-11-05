#!/usr/bin/env python3
"""
Clear corrupted task results from Redis

This script clears any corrupted Celery task results that may be causing
the "Exception information must include the exception type" error.
"""

import redis
import sys
from app.deps import settings

def clear_redis_task_results():
    """Clear all Celery task results from Redis"""
    try:
        # Parse Redis URL
        redis_url = settings.redis_url
        print(f"Connecting to Redis: {redis_url}")
        
        # Connect to Redis
        r = redis.from_url(redis_url)
        
        # Test connection
        r.ping()
        print("✅ Connected to Redis successfully")
        
        # Get all keys
        all_keys = r.keys('*')
        print(f"Found {len(all_keys)} total keys in Redis")
        
        # Find Celery task result keys
        celery_result_keys = [k for k in all_keys if b'celery-task-meta-' in k]
        print(f"Found {len(celery_result_keys)} Celery task result keys")
        
        if celery_result_keys:
            print("\nCelery task result keys:")
            for key in celery_result_keys[:10]:  # Show first 10
                print(f"  - {key.decode('utf-8')}")
            if len(celery_result_keys) > 10:
                print(f"  ... and {len(celery_result_keys) - 10} more")
            
            # Ask for confirmation
            response = input(f"\n⚠️  Delete {len(celery_result_keys)} Celery task result keys? (yes/no): ")
            
            if response.lower() in ['yes', 'y']:
                # Delete task result keys
                deleted = 0
                for key in celery_result_keys:
                    r.delete(key)
                    deleted += 1
                
                print(f"✅ Deleted {deleted} Celery task result keys")
            else:
                print("❌ Cancelled - no keys deleted")
        else:
            print("✅ No Celery task result keys found - Redis is clean")
        
        # Show remaining keys
        remaining_keys = r.keys('*')
        print(f"\n📊 Remaining keys in Redis: {len(remaining_keys)}")
        
        if remaining_keys:
            # Group by prefix
            prefixes = {}
            for key in remaining_keys:
                key_str = key.decode('utf-8')
                prefix = key_str.split(':')[0] if ':' in key_str else 'other'
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
            
            print("\nKey distribution by prefix:")
            for prefix, count in sorted(prefixes.items(), key=lambda x: x[1], reverse=True):
                print(f"  {prefix}: {count} keys")
        
        print("\n✅ Redis cleanup complete!")
        
    except redis.ConnectionError as e:
        print(f"❌ Failed to connect to Redis: {e}")
        print("\nMake sure Redis is running:")
        print("  redis-server")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def clear_all_redis_data():
    """Clear ALL data from Redis (use with caution!)"""
    try:
        redis_url = settings.redis_url
        print(f"Connecting to Redis: {redis_url}")
        
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Connected to Redis successfully")
        
        # Get count before
        before_count = len(r.keys('*'))
        print(f"Current keys in Redis: {before_count}")
        
        # Ask for confirmation
        response = input(f"\n⚠️  WARNING: This will delete ALL {before_count} keys from Redis! Continue? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            r.flushdb()
            print("✅ All Redis data cleared (FLUSHDB)")
            
            # Verify
            after_count = len(r.keys('*'))
            print(f"Remaining keys: {after_count}")
        else:
            print("❌ Cancelled - no data deleted")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("Redis Cleanup Tool")
    print("=" * 60)
    print()
    print("Choose an option:")
    print("  1. Clear only Celery task results (recommended)")
    print("  2. Clear ALL Redis data (use with caution!)")
    print("  3. Cancel")
    print()
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == "1":
        print("\n" + "=" * 60)
        print("Clearing Celery task results...")
        print("=" * 60 + "\n")
        clear_redis_task_results()
    elif choice == "2":
        print("\n" + "=" * 60)
        print("Clearing ALL Redis data...")
        print("=" * 60 + "\n")
        clear_all_redis_data()
    else:
        print("❌ Cancelled")
        sys.exit(0)

