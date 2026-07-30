#!/usr/bin/env python3
"""
Test script for the new update and search functionality
"""

import asyncio

import pytest

from src.manager import todo_manager


@pytest.mark.asyncio
async def test_update_and_search():
    """Test the new update and search features"""
    
    print("=== ToDoList MCP Server - Update & Search Test ===\n")
    
    # First, let's read existing tasks to get some IDs
    print("1. Reading existing tasks...")
    try:
        tree = todo_manager.parse_tdl_file()
        tasks = todo_manager.extract_tasks(tree)
        
        if not tasks:
            print("No tasks found. Please add some tasks first using the add_task tool.")
            return
        
        print(f"Found {len(tasks)} tasks:")
        for i, task in enumerate(tasks[:5]):  # Show first 5
            print(f"  ID: {task['id']}, Title: {task['title']}, Priority: {task['priority']}")
        print()
        
    except Exception as e:
        print(f"Error reading tasks: {e}")
        return
    
    # Test search functionality
    print("2. Testing search functionality...")
    
    # Search by title
    print("   Searching for tasks containing 'test':")
    search_results = todo_manager.search_tasks(tasks, search_term='test')
    print(f"   Found {len(search_results)} tasks")
    
    # Search by priority
    print("   Searching for high priority tasks:")
    high_priority = todo_manager.search_tasks(tasks, priority='High')
    print(f"   Found {len(high_priority)} tasks")
    
    # Search by completion
    print("   Searching for incomplete tasks:")
    incomplete = todo_manager.search_tasks(tasks, completed=False)
    print(f"   Found {len(incomplete)} tasks")
    print()
    
    # Test update functionality
    if tasks:
        test_task = tasks[0]
        task_id = test_task['id']
        
        print(f"3. Testing update functionality on task ID {task_id}...")
        print(f"   Original title: '{test_task['title']}'")
        print(f"   Original priority: '{test_task['priority']}'")
        
        # Test updating title and priority
        success, message = todo_manager.update_task(
            task_id, 
            title=f"UPDATED: {test_task['title']}", 
            priority='High',
            percent_done=25
        )
        
        if success:
            print(f"   ✓ Update successful: {message}")
            
            # Read the task again to verify update
            tree = todo_manager.parse_tdl_file()
            updated_tasks = todo_manager.extract_tasks(tree)
            updated_task = next((t for t in updated_tasks if t['id'] == task_id), None)
            
            if updated_task:
                print(f"   Verified - New title: '{updated_task['title']}'")
                print(f"   Verified - New priority: '{updated_task['priority']}'")
                print(f"   Verified - New progress: {updated_task['percent_done']}%")
            
            # Revert the changes for cleanup
            success2, message2 = todo_manager.update_task(
                task_id,
                title=test_task['title'],  # Revert to original
                priority=test_task['priority'],  # Revert to original
                percent_done=0
            )
            if success2:
                print("   ✓ Reverted changes for cleanup")
            
        else:
            print(f"   ✗ Update failed: {message}")
        
        print()
    
    # Test clearing fields
    if tasks:
        task_with_category = next((t for t in tasks if t.get('category')), None)
        if task_with_category:
            task_id = task_with_category['id']
            print(f"4. Testing field clearing on task ID {task_id}...")
            print(f"   Original category: '{task_with_category['category']}'")
            
            # Clear the category
            success, message = todo_manager.update_task(task_id, category='')
            if success:
                print(f"   ✓ Category cleared: {message}")
                
                # Restore the category
                success2, message2 = todo_manager.update_task(
                    task_id, 
                    category=task_with_category['category']
                )
                if success2:
                    print("   ✓ Category restored")
            else:
                print(f"   ✗ Clear failed: {message}")
    
    print("\n=== Test completed! ===")


if __name__ == "__main__":
    asyncio.run(test_update_and_search())
