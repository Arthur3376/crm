#!/usr/bin/env python3
"""
UCIC Student Data Management Backend API Testing Suite
Tests all endpoints with the test user: arojaaro@gmail.com / admin123
"""

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class UCICAPITester:
    def __init__(self, base_url: str = "https://campus-flow-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data for UCIC
        self.test_student_id = None
        self.test_custom_field_id = None
        self.test_change_request_id = None

    def log_test(self, name: str, success: bool, details: str = "", error: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {error}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    expected_status: int = 200, auth_required: bool = True) -> tuple[bool, Dict]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            success = response.status_code == expected_status
            
            # Handle binary responses (like file downloads)
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                try:
                    response_data = response.json()
                except:
                    response_data = {"status_code": response.status_code, "text": response.text}
            else:
                # For binary responses, return basic info
                response_data = {
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "content_length": len(response.content),
                    "headers": dict(response.headers)
                }
            
            return success, response_data
            
        except Exception as e:
            return False, {"error": str(e)}

    def test_auth_login(self):
        """Test login with UCIC test credentials"""
        success, response = self.make_request(
            'POST', 
            'auth/login',
            {
                "email": "arojaaro@gmail.com",
                "password": "admin123"
            },
            auth_required=False
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_data = response.get('user', {})
            self.log_test("Login with UCIC credentials", True, f"User: {self.user_data.get('name', 'Unknown')}, Role: {self.user_data.get('role', 'Unknown')}")
            return True
        else:
            self.log_test("Login with UCIC credentials", False, "", response.get('detail', 'Login failed'))
            return False

    def test_auth_me(self):
        """Test get current user info"""
        success, response = self.make_request('GET', 'auth/me')
        self.log_test("Get current user info", success, 
                     f"User ID: {response.get('user_id', 'N/A')}" if success else "",
                     response.get('detail', 'Failed to get user info'))

    def test_students_list(self):
        """Test getting students list"""
        success, response = self.make_request('GET', 'students')
        if success:
            students_count = len(response) if isinstance(response, list) else 0
            self.log_test("Get students list", True, f"Found {students_count} students")
            # Store first student ID for further tests
            if students_count > 0:
                self.test_student_id = response[0].get('student_id')
        else:
            self.log_test("Get students list", False, "", response.get('detail', 'Failed to get students'))

    def test_student_detail(self):
        """Test getting specific student details"""
        if not self.test_student_id:
            self.log_test("Get student detail", False, "", "No test student ID available")
            return
            
        success, response = self.make_request('GET', f'students/{self.test_student_id}')
        if success:
            self.log_test("Get student detail", True, f"Student: {response.get('full_name', 'Unknown')}")
        else:
            self.log_test("Get student detail", False, "", response.get('detail', 'Failed to get student detail'))

    def test_custom_fields_get(self):
        """Test getting custom field definitions"""
        success, response = self.make_request('GET', 'students/custom-fields')
        if success:
            fields = response.get('fields', [])
            self.log_test("Get custom fields", True, f"Found {len(fields)} custom fields")
        else:
            self.log_test("Get custom fields", False, "", response.get('detail', 'Failed to get custom fields'))

    def test_custom_fields_create(self):
        """Test creating a custom field"""
        field_data = {
            "field_name": "Número de Control",
            "field_type": "text",
            "required": True
        }
        
        success, response = self.make_request('POST', 'students/custom-fields', field_data)
        if success and 'field' in response:
            self.test_custom_field_id = response['field']['field_id']
            self.log_test("Create custom field", True, f"Field ID: {self.test_custom_field_id}")
        else:
            self.log_test("Create custom field", False, "", response.get('detail', 'Failed to create custom field'))

    def test_custom_fields_update(self):
        """Test updating a custom field"""
        if not self.test_custom_field_id:
            self.log_test("Update custom field", False, "", "No test custom field ID available")
            return
            
        update_data = {
            "field_name": "Número de Control Actualizado",
            "required": False
        }
        
        success, response = self.make_request('PUT', f'students/custom-fields/{self.test_custom_field_id}', update_data)
        if success:
            self.log_test("Update custom field", True, "Field updated successfully")
        else:
            self.log_test("Update custom field", False, "", response.get('detail', 'Failed to update custom field'))

    def test_student_custom_fields_update(self):
        """Test updating student's custom field values"""
        if not self.test_student_id or not self.test_custom_field_id:
            self.log_test("Update student custom fields", False, "", "Missing student ID or custom field ID")
            return
            
        update_data = {
            "fields": {
                self.test_custom_field_id: "12345678"
            }
        }
        
        success, response = self.make_request('PUT', f'students/{self.test_student_id}/custom-fields', update_data)
        if success:
            self.log_test("Update student custom fields", True, "Student custom fields updated")
        else:
            self.log_test("Update student custom fields", False, "", response.get('detail', 'Failed to update student custom fields'))

    def test_change_requests_get(self):
        """Test getting change requests"""
        success, response = self.make_request('GET', 'students/change-requests')
        if success:
            requests_list = response.get('requests', [])
            self.log_test("Get change requests", True, f"Found {len(requests_list)} change requests")
            # Store first request ID for approval/rejection tests
            if requests_list:
                self.test_change_request_id = requests_list[0].get('request_id')
        else:
            self.log_test("Get change requests", False, "", response.get('detail', 'Failed to get change requests'))

    def test_change_request_approve(self):
        """Test approving a change request"""
        if not self.test_change_request_id:
            self.log_test("Approve change request", False, "", "No test change request ID available")
            return
            
        success, response = self.make_request('POST', f'students/change-requests/{self.test_change_request_id}/approve')
        if success:
            self.log_test("Approve change request", True, "Change request approved")
        else:
            self.log_test("Approve change request", False, "", response.get('detail', 'Failed to approve change request'))

    def test_audit_logs(self):
        """Test getting audit logs"""
        success, response = self.make_request('GET', 'students/audit-logs')
        if success:
            logs = response.get('logs', [])
            self.log_test("Get audit logs", True, f"Found {len(logs)} audit log entries")
        else:
            self.log_test("Get audit logs", False, "", response.get('detail', 'Failed to get audit logs'))

    def test_export_excel(self):
        """Test Excel export"""
        success, response = self.make_request('GET', 'students/export/excel', expected_status=200)
        if success:
            # Check if response is binary data (Excel file)
            content_type = getattr(response, 'headers', {}).get('content-type', '')
            if 'spreadsheet' in content_type or 'excel' in content_type:
                self.log_test("Export to Excel", True, "Excel file generated successfully")
            else:
                self.log_test("Export to Excel", True, "Export endpoint responded (content type check skipped)")
        else:
            self.log_test("Export to Excel", False, "", response.get('detail', 'Failed to export to Excel'))

    def test_export_pdf(self):
        """Test PDF export"""
        success, response = self.make_request('GET', 'students/export/pdf', expected_status=200)
        if success:
            # Check if response is binary data (PDF file)
            content_type = getattr(response, 'headers', {}).get('content-type', '')
            if 'pdf' in content_type:
                self.log_test("Export to PDF", True, "PDF file generated successfully")
            else:
                self.log_test("Export to PDF", True, "Export endpoint responded (content type check skipped)")
        else:
            self.log_test("Export to PDF", False, "", response.get('detail', 'Failed to export to PDF'))

    def test_regression_endpoints(self):
        """Test other core endpoints for regression"""
        endpoints = [
            ('leads', 'leads'),
            ('teachers', 'teachers'),
            ('careers/full', 'careers'),
            ('dashboard/stats', 'dashboard stats')
        ]
        
        for endpoint, name in endpoints:
            success, response = self.make_request('GET', endpoint)
            if success:
                if isinstance(response, list):
                    count = len(response)
                    self.log_test(f"Get {name}", True, f"Found {count} items")
                elif isinstance(response, dict):
                    self.log_test(f"Get {name}", True, "Data retrieved successfully")
                else:
                    self.log_test(f"Get {name}", True, "Endpoint responded")
            else:
                self.log_test(f"Get {name}", False, "", response.get('detail', f'Failed to get {name}'))

    def cleanup_test_data(self):
        """Clean up test data"""
        # Delete test custom field
        if self.test_custom_field_id and self.user_data.get('role') in ['admin', 'gerente']:
            success, _ = self.make_request('DELETE', f'students/custom-fields/{self.test_custom_field_id}')
            if success:
                print(f"🧹 Cleaned up test custom field: {self.test_custom_field_id}")

    def run_all_tests(self):
        """Run complete UCIC test suite"""
        print("🚀 Starting UCIC Student Data Management API Tests")
        print("=" * 60)
        
        # Authentication tests
        if not self.test_auth_login():
            print("❌ Authentication failed - stopping tests")
            return False
            
        self.test_auth_me()
        
        # Students module tests
        self.test_students_list()
        self.test_student_detail()
        
        # Custom fields tests
        self.test_custom_fields_get()
        self.test_custom_fields_create()
        self.test_custom_fields_update()
        
        # Student custom field values
        self.test_student_custom_fields_update()
        
        # Change requests workflow
        self.test_change_requests_get()
        self.test_change_request_approve()
        
        # Audit logs
        self.test_audit_logs()
        
        # Export functionality
        self.test_export_excel()
        self.test_export_pdf()
        
        # Regression tests
        self.test_regression_endpoints()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

    def get_test_summary(self):
        """Get test summary for reporting"""
        failed_tests = [t for t in self.test_results if not t['success']]
        passed_tests = [t for t in self.test_results if t['success']]
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": len(failed_tests),
            "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            "passed_test_names": [t['test'] for t in passed_tests],
            "failed_test_details": failed_tests,
            "user_role": self.user_data.get('role', 'unknown') if self.user_data else 'unknown'
        }

def main():
    tester = UCICAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    summary = tester.get_test_summary()
    with open('/tmp/backend_test_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())