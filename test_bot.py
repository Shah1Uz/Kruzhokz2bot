#!/usr/bin/env python3
"""
Bot test script to check functionality
"""

import os
import sys
sys.path.append('.')

def test_bot_functions():
    """Test basic bot functionality"""
    
    print("🔍 Testing bot imports...")
    try:
        from main import (
            bot, ADMIN_ID, PAYMENT_CARD, 
            get_user_messages, create_language_keyboard, 
            create_effect_keyboard, is_admin
        )
        print("✅ All imports successful")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False
    
    print("\n🔍 Testing database functions...")
    try:
        from models import (
            get_user_language, can_create_kruzhok, 
            get_user_limits, get_referral_stats
        )
        print("✅ Database functions imported")
        
        # Test basic database connection
        lang = get_user_language(123456)
        print(f"✅ Database connection works, default language: {lang}")
        
        # Test user limits
        limits = get_user_limits(123456)
        print(f"✅ User limits function works: {limits}")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    print("\n🔍 Testing message system...")
    try:
        messages = get_user_messages(123456)
        print(f"✅ Messages loaded, welcome message exists: {'welcome' in messages}")
    except Exception as e:
        print(f"❌ Message system error: {e}")
        return False
    
    print("\n🔍 Testing keyboard creation...")
    try:
        lang_keyboard = create_language_keyboard()
        effect_keyboard = create_effect_keyboard()
        print(f"✅ Keyboards created successfully")
    except Exception as e:
        print(f"❌ Keyboard creation error: {e}")
        return False
    
    print("\n🔍 Testing admin functions...")
    try:
        admin_check = is_admin(ADMIN_ID)
        print(f"✅ Admin check works: {admin_check}")
    except Exception as e:
        print(f"❌ Admin function error: {e}")
        return False
    
    print("\n✅ All tests passed! Bot should work correctly.")
    return True

if __name__ == "__main__":
    test_bot_functions()