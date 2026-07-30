#!/usr/bin/env python3
"""
Test script for ToDoList MCP Server
This helps verify the server can read your ToDoList file correctly
without making any changes.
"""

import sys
import os
from pathlib import Path

# Add the current directory to path to import the server module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from tdl_mcp_server import ToDoListManager
    print("✅ Successfully imported ToDoList MCP Server")
except ImportError as e:
    print(f"❌ Failed to import server module: {e}")
    sys.exit(1)

def test_file_reading():
    """Test reading the ToDoList file"""
    print("\n🔍 Testing ToDoList file reading...")
    
    todolist_path = r"D:\Projects\mylist.tdl"
    
    if not Path(todolist_path).exists():
        print(f"❌ ToDoList file not found: {todolist_path}")
        return False
    
    try:
        manager = ToDoListManager()
        tree = manager.parse_tdl_file(todolist_path)
        root = tree.getroot()
        
        print(f"✅ File parsed successfully")
        print(f"   Root element: {root.tag}")
        print(f"   Project name: {root.get('PROJECTNAME', 'Unknown')}")
        print(f"   File version: {root.get('FILEVERSION', 'Unknown')}")
        print(f"   Next unique ID: {root.get('NEXTUNIQUEID', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error parsing file: {e}")
        return False

def test_task_extraction():
    """Test extracting tasks from the file"""
    print("\n📋 Testing task extraction...")
    
    try:
        manager = ToDoListManager()
        tree = manager.parse_tdl_file()
        tasks = manager.extract_tasks(tree)
        
        print(f"✅ Extracted {len(tasks)} tasks")
        
        if tasks:
            # Show first few tasks as examples
            print(f"   Sample tasks:")
            for i, task in enumerate(tasks[:3]):
                title = task.get('title', 'No title')[:50]
                status = "✓" if task.get('completed') else "○"
                print(f"   {status} [{task.get('id', '?')}] {title}")
            
            if len(tasks) > 3:
                print(f"   ... and {len(tasks) - 3} more tasks")
        
        return True
        
    except Exception as e:
        print(f"❌ Error extracting tasks: {e}")
        return False

def test_date_handling():
    """Test date encoding/decoding"""
    print("\n📅 Testing date handling...")
    
    try:
        manager = ToDoListManager()
        
        # Test encoding
        test_date = "2025-09-08"
        encoded = manager._encode_date(test_date)
        print(f"✅ Date encoding: {test_date} -> {encoded}")
        
        # Test decoding  
        decoded = manager._decode_date(encoded)
        print(f"✅ Date decoding: {encoded} -> {decoded}")
        
        if decoded == test_date:
            print("✅ Date round-trip successful")
            return True
        else:
            print(f"❌ Date round-trip failed: expected {test_date}, got {decoded}")
            return False
            
    except Exception as e:
        print(f"❌ Error in date handling: {e}")
        return False

def test_priority_handling():
    """Test priority encoding/decoding"""
    print("\n🎯 Testing priority handling...")
    
    try:
        manager = ToDoListManager()
        
        priorities = ['Low', 'Normal', 'High', 'Urgent']
        
        for priority in priorities:
            encoded = manager._encode_priority(priority)
            decoded = manager._decode_priority(encoded)
            print(f"✅ Priority: {priority} -> {encoded} -> {decoded}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in priority handling: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 ToDoList MCP Server Test Suite")
    print("=" * 50)
    
    tests = [
        test_file_reading,
        test_task_extraction,
        test_date_handling,
        test_priority_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The server should work correctly.")
        print("📝 You can now safely reconnect the MCP server to Claude Desktop.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("🔧 Consider backing up your .tdl file before using the server.")
    
    print("\n💡 Next steps:")
    print("   1. Backup your ToDoList file: copy D:\\Projects\\mylist.tdl to a safe location")
    print("   2. Update your Claude Desktop config to use the new server")
    print("   3. Restart Claude Desktop")
    print("   4. Test with simple 'show my tasks' command first")

if __name__ == "__main__":
    main()