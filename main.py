# employee_leave_server.py
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
import json
import sqlite3
import os

# Create MCP server
mcp = FastMCP("Employee & Leave Management System")

# Database configuration
DB_FILE = "employee_leave.db"

# Data Models
class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"

class LeaveType(str, Enum):
    ANNUAL = "annual"
    SICK = "sick"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    EMERGENCY = "emergency"
    UNPAID = "unpaid"

class LeaveStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class Employee(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    department: str
    position: str
    hire_date: date
    status: EmployeeStatus
    manager_id: Optional[int] = None
    annual_leave_balance: int = 25  # Default 25 days per year
    sick_leave_balance: int = 10    # Default 10 days per year

class LeaveRequest(BaseModel):
    id: int
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    days_requested: int
    reason: str
    status: LeaveStatus
    requested_date: datetime
    approved_by: Optional[int] = None
    approved_date: Optional[datetime] = None
    comments: Optional[str] = None

# Database setup
def init_database():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create employees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            position TEXT NOT NULL,
            hire_date DATE NOT NULL,
            status TEXT DEFAULT 'active',
            manager_id INTEGER,
            annual_leave_balance INTEGER DEFAULT 25,
            sick_leave_balance INTEGER DEFAULT 10,
            FOREIGN KEY (manager_id) REFERENCES employees (id)
        )
    ''')
    
    # Create leave_requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            leave_type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            days_requested INTEGER NOT NULL,
            reason TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            requested_date DATETIME NOT NULL,
            approved_by INTEGER,
            approved_date DATETIME,
            comments TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees (id),
            FOREIGN KEY (approved_by) REFERENCES employees (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn

# Utility functions
def serialize_date(obj):
    """JSON serializer for date objects"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert SQLite row to dictionary"""
    return dict(row)

def get_employee_full_name(employee_id: int) -> str:
    """Get employee's full name"""
    if not employee_id:
        return "Unknown Employee"
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, last_name FROM employees WHERE id = ?", (employee_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return f"{row['first_name']} {row['last_name']}"
    return "Unknown Employee"

# Employee Management Tools
@mcp.tool()
def create_employee(
    first_name: str,
    last_name: str,
    email: str,
    department: str,
    position: str,
    hire_date: str,
    manager_id: Optional[int] = None
) -> Dict[str, Any]:
    """Create a new employee record"""
    try:
        hire_date_obj = datetime.strptime(hire_date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "Invalid hire_date format. Use YYYY-MM-DD"}
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Validate manager exists if provided
    if manager_id:
        cursor.execute("SELECT id FROM employees WHERE id = ?", (manager_id,))
        if not cursor.fetchone():
            conn.close()
            return {"error": f"Manager with ID {manager_id} does not exist"}
    
    try:
        cursor.execute('''
            INSERT INTO employees (first_name, last_name, email, department, position, hire_date, manager_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, department, position, hire_date_obj.isoformat(), manager_id))
        
        employee_id = cursor.lastrowid
        conn.commit()
        
        # Get the created employee
        cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
        employee_row = cursor.fetchone()
        conn.close()
        
        return {
            "message": f"Employee {first_name} {last_name} created successfully",
            "employee_id": employee_id,
            "employee": row_to_dict(employee_row)
        }
    except sqlite3.IntegrityError as e:
        conn.close()
        return {"error": f"Database error: {str(e)}"}

@mcp.tool()
def get_employee(employee_id: int) -> Dict[str, Any]:
    """Get employee details by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
    employee_row = cursor.fetchone()
    conn.close()
    
    if not employee_row:
        return {"error": f"Employee with ID {employee_id} not found"}
    
    employee_data = row_to_dict(employee_row)
    manager_name = get_employee_full_name(employee_data.get('manager_id'))
    
    return {
        "employee": employee_data,
        "manager_name": manager_name if employee_data.get('manager_id') else None
    }

@mcp.tool()
def list_employees(department: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
    """List all employees with optional filtering by department and status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM employees WHERE 1=1"
    params = []
    
    if department:
        query += " AND LOWER(department) = LOWER(?)"
        params.append(department)
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    cursor.execute(query, params)
    employee_rows = cursor.fetchall()
    conn.close()
    
    employees_list = []
    for row in employee_rows:
        emp_data = row_to_dict(row)
        emp_data["manager_name"] = get_employee_full_name(emp_data.get('manager_id'))
        employees_list.append(emp_data)
    
    return {
        "count": len(employees_list),
        "employees": employees_list
    }

@mcp.tool()
def update_employee(
    employee_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    department: Optional[str] = None,
    position: Optional[str] = None,
    status: Optional[str] = None,
    manager_id: Optional[int] = None
) -> Dict[str, Any]:
    """Update employee information"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if employee exists
    cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
    if not cursor.fetchone():
        conn.close()
        return {"error": f"Employee with ID {employee_id} not found"}
    
    # Validate status if provided
    if status and status not in [s.value for s in EmployeeStatus]:
        conn.close()
        return {"error": f"Invalid status. Must be one of: {[s.value for s in EmployeeStatus]}"}
    
    # Validate manager if provided
    if manager_id is not None and manager_id != 0:
        cursor.execute("SELECT id FROM employees WHERE id = ?", (manager_id,))
        if not cursor.fetchone():
            conn.close()
            return {"error": f"Manager with ID {manager_id} does not exist"}
    
    # Build update query
    update_fields = []
    params = []
    
    if first_name:
        update_fields.append("first_name = ?")
        params.append(first_name)
    if last_name:
        update_fields.append("last_name = ?")
        params.append(last_name)
    if email:
        update_fields.append("email = ?")
        params.append(email)
    if department:
        update_fields.append("department = ?")
        params.append(department)
    if position:
        update_fields.append("position = ?")
        params.append(position)
    if status:
        update_fields.append("status = ?")
        params.append(status)
    if manager_id is not None:
        update_fields.append("manager_id = ?")
        params.append(manager_id if manager_id != 0 else None)
    
    if not update_fields:
        conn.close()
        return {"error": "No fields to update"}
    
    params.append(employee_id)
    query = f"UPDATE employees SET {', '.join(update_fields)} WHERE id = ?"
    
    try:
        cursor.execute(query, params)
        conn.commit()
        
        # Get updated employee
        cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
        updated_employee = cursor.fetchone()
        conn.close()
        
        emp_data = row_to_dict(updated_employee)
        return {
            "message": f"Employee {emp_data['first_name']} {emp_data['last_name']} updated successfully",
            "employee": emp_data
        }
    except sqlite3.IntegrityError as e:
        conn.close()
        return {"error": f"Database error: {str(e)}"}

# Leave Management Tools
@mcp.tool()
def submit_leave_request(
    employee_id: int,
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str
) -> Dict[str, Any]:
    """Submit a new leave request"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if employee exists
    cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
    employee_row = cursor.fetchone()
    if not employee_row:
        conn.close()
        return {"error": f"Employee with ID {employee_id} not found"}
    
    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        conn.close()
        return {"error": "Invalid date format. Use YYYY-MM-DD"}
    
    if start_date_obj > end_date_obj:
        conn.close()
        return {"error": "Start date cannot be after end date"}
    
    if leave_type not in [lt.value for lt in LeaveType]:
        conn.close()
        return {"error": f"Invalid leave type. Must be one of: {[lt.value for lt in LeaveType]}"}
    
    # Calculate days requested
    days_requested = (end_date_obj - start_date_obj).days + 1
    
    # Check leave balance
    employee_data = row_to_dict(employee_row)
    if leave_type == LeaveType.ANNUAL.value and days_requested > employee_data['annual_leave_balance']:
        conn.close()
        return {"error": f"Insufficient annual leave balance. Available: {employee_data['annual_leave_balance']} days"}
    elif leave_type == LeaveType.SICK.value and days_requested > employee_data['sick_leave_balance']:
        conn.close()
        return {"error": f"Insufficient sick leave balance. Available: {employee_data['sick_leave_balance']} days"}
    
    # Insert leave request
    cursor.execute('''
        INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, days_requested, reason, requested_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (employee_id, leave_type, start_date_obj.isoformat(), end_date_obj.isoformat(), 
          days_requested, reason, datetime.now().isoformat()))
    
    leave_request_id = cursor.lastrowid
    conn.commit()
    
    # Get the created leave request
    cursor.execute("SELECT * FROM leave_requests WHERE id = ?", (leave_request_id,))
    leave_request_row = cursor.fetchone()
    conn.close()
    
    return {
        "message": "Leave request submitted successfully",
        "leave_request_id": leave_request_id,
        "leave_request": row_to_dict(leave_request_row)
    }

@mcp.tool()
def approve_leave_request(
    leave_request_id: int,
    approver_id: int,
    comments: Optional[str] = None
) -> Dict[str, Any]:
    """Approve a leave request"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if leave request exists
    cursor.execute("SELECT * FROM leave_requests WHERE id = ?", (leave_request_id,))
    leave_request_row = cursor.fetchone()
    if not leave_request_row:
        conn.close()
        return {"error": f"Leave request with ID {leave_request_id} not found"}
    
    # Check if approver exists
    cursor.execute("SELECT id FROM employees WHERE id = ?", (approver_id,))
    if not cursor.fetchone():
        conn.close()
        return {"error": f"Approver with ID {approver_id} not found"}
    
    leave_request_data = row_to_dict(leave_request_row)
    if leave_request_data['status'] != LeaveStatus.PENDING.value:
        conn.close()
        return {"error": f"Leave request is already {leave_request_data['status']}"}
    
    # Update leave request
    cursor.execute('''
        UPDATE leave_requests 
        SET status = ?, approved_by = ?, approved_date = ?, comments = ?
        WHERE id = ?
    ''', (LeaveStatus.APPROVED.value, approver_id, datetime.now().isoformat(), comments, leave_request_id))
    
    # Deduct from employee's leave balance
    if leave_request_data['leave_type'] == LeaveType.ANNUAL.value:
        cursor.execute('''
            UPDATE employees 
            SET annual_leave_balance = annual_leave_balance - ?
            WHERE id = ?
        ''', (leave_request_data['days_requested'], leave_request_data['employee_id']))
    elif leave_request_data['leave_type'] == LeaveType.SICK.value:
        cursor.execute('''
            UPDATE employees 
            SET sick_leave_balance = sick_leave_balance - ?
            WHERE id = ?
        ''', (leave_request_data['days_requested'], leave_request_data['employee_id']))
    
    conn.commit()
    
    # Get updated leave request
    cursor.execute("SELECT * FROM leave_requests WHERE id = ?", (leave_request_id,))
    updated_leave_request = cursor.fetchone()
    conn.close()
    
    return {
        "message": "Leave request approved successfully",
        "leave_request": row_to_dict(updated_leave_request)
    }

@mcp.tool()
def reject_leave_request(
    leave_request_id: int,
    approver_id: int,
    comments: str
) -> Dict[str, Any]:
    """Reject a leave request"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if leave request exists
    cursor.execute("SELECT * FROM leave_requests WHERE id = ?", (leave_request_id,))
    leave_request_row = cursor.fetchone()
    if not leave_request_row:
        conn.close()
        return {"error": f"Leave request with ID {leave_request_id} not found"}
    
    # Check if approver exists
    cursor.execute("SELECT id FROM employees WHERE id = ?", (approver_id,))
    if not cursor.fetchone():
        conn.close()
        return {"error": f"Approver with ID {approver_id} not found"}
    
    leave_request_data = row_to_dict(leave_request_row)
    if leave_request_data['status'] != LeaveStatus.PENDING.value:
        conn.close()
        return {"error": f"Leave request is already {leave_request_data['status']}"}
    
    # Update leave request
    cursor.execute('''
        UPDATE leave_requests 
        SET status = ?, approved_by = ?, approved_date = ?, comments = ?
        WHERE id = ?
    ''', (LeaveStatus.REJECTED.value, approver_id, datetime.now().isoformat(), comments, leave_request_id))
    
    conn.commit()
    
    # Get updated leave request
    cursor.execute("SELECT * FROM leave_requests WHERE id = ?", (leave_request_id,))
    updated_leave_request = cursor.fetchone()
    conn.close()
    
    return {
        "message": "Leave request rejected",
        "leave_request": row_to_dict(updated_leave_request)
    }

@mcp.tool()
def get_leave_requests(
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    leave_type: Optional[str] = None
) -> Dict[str, Any]:
    """Get leave requests with optional filtering"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM leave_requests WHERE 1=1"
    params = []
    
    if employee_id:
        query += " AND employee_id = ?"
        params.append(employee_id)
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    if leave_type:
        query += " AND leave_type = ?"
        params.append(leave_type)
    
    query += " ORDER BY requested_date DESC"
    
    cursor.execute(query, params)
    leave_request_rows = cursor.fetchall()
    conn.close()
    
    leave_requests_list = []
    for row in leave_request_rows:
        req_data = row_to_dict(row)
        req_data["employee_name"] = get_employee_full_name(req_data['employee_id'])
        req_data["approved_by_name"] = get_employee_full_name(req_data.get('approved_by'))
        leave_requests_list.append(req_data)
    
    return {
        "count": len(leave_requests_list),
        "leave_requests": leave_requests_list
    }

@mcp.tool()
def get_employee_leave_balance(employee_id: int) -> Dict[str, Any]:
    """Get employee's current leave balance"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
    employee_row = cursor.fetchone()
    conn.close()
    
    if not employee_row:
        return {"error": f"Employee with ID {employee_id} not found"}
    
    employee_data = row_to_dict(employee_row)
    return {
        "employee_name": f"{employee_data['first_name']} {employee_data['last_name']}",
        "annual_leave_balance": employee_data['annual_leave_balance'],
        "sick_leave_balance": employee_data['sick_leave_balance']
    }

# Resources
@mcp.resource("employee://{employee_id}")
def get_employee_resource(employee_id: str) -> str:
    """Get employee information as a resource"""
    try:
        emp_id = int(employee_id)
        result = get_employee(emp_id)
        return json.dumps(result, indent=2, default=serialize_date)
    except ValueError:
        return json.dumps({"error": "Invalid employee ID"})

@mcp.resource("leave-requests://pending")
def get_pending_leave_requests() -> str:
    """Get all pending leave requests"""
    result = get_leave_requests(status="pending")
    return json.dumps(result, indent=2, default=serialize_date)

@mcp.resource("department://{department_name}")
def get_department_employees(department_name: str) -> str:
    """Get all employees in a specific department"""
    result = list_employees(department=department_name)
    return json.dumps(result, indent=2, default=serialize_date)

# Demo data function
@mcp.tool()
def load_demo_data() -> Dict[str, Any]:
    """Load some demo data for testing"""
    # Create demo employees
    demo_employees = [
        {
            "first_name": "John", "last_name": "Doe", "email": "john.doe@company.com",
            "department": "Engineering", "position": "Senior Developer", "hire_date": "2020-01-15"
        },
        {
            "first_name": "Jane", "last_name": "Smith", "email": "jane.smith@company.com",
            "department": "Marketing", "position": "Marketing Manager", "hire_date": "2019-03-20"
        },
        {
            "first_name": "Mike", "last_name": "Johnson", "email": "mike.johnson@company.com",
            "department": "Engineering", "position": "Team Lead", "hire_date": "2018-06-10"
        }
    ]
    
    created_employees = []
    for emp_data in demo_employees:
        result = create_employee(**emp_data)
        if "error" not in result:
            created_employees.append(result)
    
    # Create demo leave requests
    leave_requests_created = 0
    if created_employees:
        result1 = submit_leave_request(1, "annual", "2025-07-01", "2025-07-05", "Summer vacation")
        if "error" not in result1:
            leave_requests_created += 1
        
        result2 = submit_leave_request(2, "sick", "2025-06-25", "2025-06-26", "Doctor appointment")
        if "error" not in result2:
            leave_requests_created += 1
    
    return {
        "message": "Demo data loaded successfully",
        "employees_created": len(created_employees),
        "leave_requests_created": leave_requests_created
    }

# Initialize database on startup
init_database()

if __name__ == "__main__":
    # Run the server
    mcp.run()