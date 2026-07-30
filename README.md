# TodoList MCP Server

A comprehensive Python MCP server for managing ToDoList (.tdl) XML files. This server provides full CRUD operations for tasks in the ToDoList application format, allowing you to manage your tasks programmatically while maintaining compatibility with the ToDoList desktop application.

## Features

- **Full CRUD Operations**: Create, read, update, and delete tasks
- **Hierarchical Task Support**: Handle nested tasks and subtasks
- **Rich Metadata**: Support for priorities, due dates, categories, assignments, and progress tracking
- **Search and Filtering**: Advanced task filtering by various criteria
- **ToDoList Compatibility**: Full compatibility with ToDoList application XML format
- **Real-time Sync**: Works with live ToDoList files

## Prerequisites

- Python 3.10 or higher
- ToDoList application (for .tdl file creation)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/todolist-mcp.git
cd todolist-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Set the `TODOLIST_FILE` environment variable to point to your `.tdl` file. Falls back to the user's default ToDoList path if not set.

## Usage

### Starting the Server

```bash
python tdl_mcp_server.py
```

### Available Tools

#### Task Management
- `get_my_tasks`: Get all tasks from your main ToDoList file
- `get_today_tasks`: Get tasks due today (or specific date)
- `add_task`: Create new tasks with full metadata
- `update_task`: Update existing tasks
- `move_task`: Move tasks to different positions in the hierarchy
- `get_task`: Get detailed information about a specific task

#### Search and Filtering
- `search_tasks`: Search and filter tasks by various criteria

#### File Operations
- `get_file_status`: Check ToDoList file status and statistics
- `read_any_tdl_file`: Read tasks from any .tdl file
- `analyze_structure`: Analyze the XML structure of ToDoList files

### Example MCP Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "todolist": {
      "command": "python",
      "args": ["K:/todolist_mcp/tdl_mcp_server.py"]
    }
  }
}
```

## API Reference

### Task Operations

#### Create a Task
```python
add_task({
    "title": "Complete project documentation",
    "description": "Write comprehensive README files",
    "due_date": "2024-12-31",
    "priority": "High",
    "category": "Documentation"
})
```

#### Update a Task
```python
update_task({
    "task_id": "123",
    "percent_done": 75,
    "allocated_to": "John Doe",
    "priority": "Above Normal"
})
```

#### Search Tasks
```python
search_tasks({
    "search_term": "documentation",
    "category": "Work",
    "completed": false,
    "priority": "High"
})
```

### Task Properties

| Property | Type | Description |
|----------|------|-------------|
| `title` | string | Task title |
| `description` | string | Detailed task description |
| `due_date` | string | Due date (YYYY-MM-DD format) |
| `priority` | enum | Low, Below Normal, Normal, Above Normal, High, Urgent |
| `category` | string | Task category or project |
| `allocated_to` | string | Person(s) assigned to the task |
| `percent_done` | integer | Completion percentage (0-100) |
| `position` | string | Hierarchical position (e.g., "1.2.3") |

## Project Structure

```
todolist-mcp/
├── tdl_mcp_server.py      # Main MCP server
├── requirements.txt       # Python dependencies
├── test_server.py         # Server tests
├── test_update_functionality.py  # Update functionality tests
├── config.json                # Example MCP configuration
├── Introduction.tdl       # Sample ToDoList file
└── README.md             # This file
```

## ToDoList File Format

The server works with ToDoList's native XML format (.tdl files). Key features:

- **Hierarchical Structure**: Tasks can have unlimited nested subtasks
- **Rich Metadata**: Supports all ToDoList fields and properties
- **Position Tracking**: Maintains task order and hierarchy
- **Compatibility**: Files remain fully compatible with ToDoList application

### Example Task Structure
```xml
<TASK ID="1" TITLE="Project Alpha" PRIORITY="1" DUEDATE="44927">
    <CATEGORY>Work</CATEGORY>
    <ALLOCATEDTO>John Doe</ALLOCATEDTO>
    <TASK ID="2" TITLE="Research Phase" PERCENTDONE="100">
        <TASK ID="3" TITLE="Market Analysis" PERCENTDONE="100"/>
        <TASK ID="4" TITLE="Competitor Review" PERCENTDONE="75"/>
    </TASK>
</TASK>
```

## Testing

Run the test suite:

```bash
python test_server.py
python test_update_functionality.py
```

## Integration with ToDoList Application

This MCP server is designed to work alongside the ToDoList desktop application:

1. **Live Editing**: Modify files that ToDoList has open
2. **Real-time Updates**: Changes appear immediately in ToDoList
3. **Backup Safety**: ToDoList maintains automatic backups
4. **Format Preservation**: All ToDoList-specific formatting is preserved

## Advanced Features

### Hierarchical Task Management
- Create nested task structures
- Move tasks between hierarchy levels
- Maintain parent-child relationships

### Position Management
```python
# Add task at specific position
add_task({"title": "New Task", "position": "1.2.3"})

# Move task to new location
move_task({"task_id": "123", "new_position": "2.1"})
```

### Flexible Searching
```python
# Complex search example
search_tasks({
    "search_term": "urgent",
    "category": "Work",
    "priority": "High", 
    "completed": false,
    "assigned_to": "John"
})
```

## Error Handling

The server provides comprehensive error handling:
- File validation and format checking
- Task ID validation
- Date format verification
- Hierarchy consistency checks

## Performance Considerations

- **File Size**: Optimized for large ToDoList files (1000+ tasks)
- **Memory Usage**: Efficient XML parsing and manipulation
- **Concurrent Access**: Safe for use with ToDoList application running

## Troubleshooting

### Common Issues

1. **File Access**: Ensure the .tdl file exists and is accessible
2. **XML Format**: Verify the file is a valid ToDoList XML format
3. **Permissions**: Check file write permissions
4. **ToDoList Lock**: Close ToDoList if experiencing file lock issues

### Debug Mode

Enable detailed logging:
```bash
python -u tdl_mcp_server.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure ToDoList compatibility
5. Submit a pull request

## License

Licensed under the Apache License 2.0. See LICENSE file for details.

## Support

For issues and questions, please open an issue on GitHub.

## Changelog

### v0.4.0
- Added comprehensive task management
- Improved hierarchical support
- Enhanced search capabilities
- Better error handling

### v0.3.0
- Added update functionality
- Position management
- File status checking

### v0.2.0
- Initial CRUD operations
- Basic search functionality

### v0.1.0
- Initial release
- Read-only operations