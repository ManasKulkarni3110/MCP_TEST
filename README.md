# Employee & Leave Management System

A comprehensive Model Context Protocol (MCP) server for managing employees and their leave requests. This system provides a complete solution for HR departments to handle employee records, leave applications, approvals, and balance tracking.

## Features

### Employee Management
- ✅ Create, read, update employee records
- ✅ Department-based organization
- ✅ Manager-employee relationships
- ✅ Employee status tracking (active, inactive, terminated)
- ✅ Hierarchical reporting structure

### Leave Management
- ✅ Multiple leave types (Annual, Sick, Maternity, Paternity, Emergency, Unpaid)
- ✅ Automatic leave balance tracking
- ✅ Leave request workflow (Submit → Approve/Reject)
- ✅ Balance validation before approval
- ✅ Historical leave request tracking

### Data Persistence
- ✅ SQLite database for reliable data storage
- ✅ Automatic database initialization
- ✅ Foreign key relationships for data integrity

## Installation

### Prerequisites
- Python 3.12 or higher
- pip package manager

### Setup

1. **Clone or download the project files**
   ```bash
   # Ensure you have main.py, pyproject.toml, and requirements.txt
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or using the project configuration:
   ```bash
   pip install fastmcp pydantic python-dateutil typing-extensions
   ```

3. **Run the server**
   ```bash
   python main.py
   ```

The server will automatically create the SQLite database (`employee_leave.db`) and initialize the required tables on first run.

## Quick Start

### Load Demo Data
To get started quickly with sample data:

```python
# Use the load_demo_data tool to create sample employees and leave requests
load_demo_data()
```

This creates:
- 3 sample employees across Engineering and Marketing departments
- 2 sample leave requests

### Basic Usage Examples

#### 1. Create an Employee
```python
create_employee(
    first_name="Alice",
    last_name="Wilson",
    email="alice.wilson@company.com",
    department="HR",
    position="HR Manager",
    hire_date="2023-01-15",
    manager_id=None  # Optional: ID of their manager
)
```

#### 2. Submit a Leave Request
```python
submit_leave_request(
    employee_id=1,
    leave_type="annual",
    start_date="2025-08-01",
    end_date="2025-08-05",
    reason="Family vacation"
)
```

#### 3. Approve a Leave Request
```python
approve_leave_request(
    leave_request_id=1,
    approver_id=2,  # Manager's employee ID
    comments="Approved. Enjoy your vacation!"
)
```

## API Reference

### Employee Management Tools

#### `create_employee()`
Creates a new employee record.

**Parameters:**
- `first_name` (str): Employee's first name
- `last_name` (str): Employee's last name
- `email` (str): Unique email address
- `department` (str): Department name
- `position` (str): Job position
- `hire_date` (str): Hire date in YYYY-MM-DD format
- `manager_id` (int, optional): ID of the employee's manager

#### `get_employee(employee_id)`
Retrieves employee details by ID.

#### `list_employees(department=None, status=None)`
Lists all employees with optional filtering.

#### `update_employee(employee_id, **fields)`
Updates employee information. All fields except `employee_id` are optional.

### Leave Management Tools

#### `submit_leave_request()`
Submits a new leave request.

**Parameters:**
- `employee_id` (int): ID of the requesting employee
- `leave_type` (str): Type of leave (annual, sick, maternity, paternity, emergency, unpaid)
- `start_date` (str): Start date in YYYY-MM-DD format
- `end_date` (str): End date in YYYY-MM-DD format
- `reason` (str): Reason for the leave

#### `approve_leave_request(leave_request_id, approver_id, comments=None)`
Approves a pending leave request and deducts from employee's balance.

#### `reject_leave_request(leave_request_id, approver_id, comments)`
Rejects a pending leave request with mandatory comments.

#### `get_leave_requests(employee_id=None, status=None, leave_type=None)`
Retrieves leave requests with optional filtering.

#### `get_employee_leave_balance(employee_id)`
Gets current leave balance for an employee.

## Data Models

### Employee Statuses
- `active`: Currently employed
- `inactive`: Temporarily inactive
- `terminated`: No longer employed

### Leave Types
- `annual`: Paid annual leave (default: 25 days/year)
- `sick`: Paid sick leave (default: 10 days/year)
- `maternity`: Maternity leave
- `paternity`: Paternity leave
- `emergency`: Emergency leave
- `unpaid`: Unpaid leave

### Leave Request Statuses
- `pending`: Awaiting approval
- `approved`: Approved by manager
- `rejected`: Rejected by manager
- `cancelled`: Cancelled by employee

## Database Schema

### Employees Table
- `id` (Primary Key)
- `first_name`, `last_name`, `email`
- `department`, `position`
- `hire_date`, `status`
- `manager_id` (Foreign Key)
- `annual_leave_balance`, `sick_leave_balance`

### Leave Requests Table
- `id` (Primary Key)
- `employee_id` (Foreign Key)
- `leave_type`, `start_date`, `end_date`
- `days_requested`, `reason`, `status`
- `requested_date`, `approved_by`, `approved_date`
- `comments`

## Features in Detail

### Automatic Balance Management
- New employees start with default leave balances (25 annual, 10 sick days)
- Balances are automatically deducted when leave is approved
- System prevents over-booking of leave days

### Validation Rules
- Email addresses must be unique
- Start date cannot be after end date
- Only pending requests can be approved/rejected
- Sufficient leave balance required for annual/sick leave
- Manager relationships are validated

### Hierarchical Structure
- Employees can have managers assigned
- Manager information is displayed in employee details
- Approvers are tracked for audit purposes

## Error Handling

The system provides comprehensive error messages for:
- Invalid data formats
- Database constraint violations
- Business rule violations
- Missing records
- Insufficient permissions

## Development

### Project Structure
```
├── main.py              # Main server implementation
├── pyproject.toml       # Project configuration
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── employee_leave.db   # SQLite database (created automatically)
```

### Extending the System

To add new features:

1. **New Leave Types**: Add to the `LeaveType` enum
2. **Additional Fields**: Modify the database schema and models
3. **Custom Validation**: Add business logic to the respective functions
4. **New Tools**: Use the `@mcp.tool()` decorator

## Troubleshooting

### Common Issues

**Database locked error**
- Ensure only one instance of the server is running
- Check file permissions for the database file

**Invalid date format**
- Always use YYYY-MM-DD format for dates
- Ensure dates are valid calendar dates

**Foreign key constraint errors**
- Verify employee IDs exist before referencing them
- Check manager relationships for circular references

## License

This project is provided as-is for educational and internal business use.

## Support

For issues or questions about this Employee & Leave Management System, please refer to the FastMCP documentation or create an issue in your project repository.