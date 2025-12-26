#!/usr/bin/env python3
"""
LeadFlow Pro Backend API Testing Suite
Tests all endpoints with the test user: admin@leadflow.com / admin123
"""

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class LeadFlowAPITester:
    def __init__(self, base_url: str = "https://salesconnect-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data
        self.test_lead_id = None
        self.test_appointment_id = None
        self.test_webhook_id = None
        self.test_conversation_id = None

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
            try:
                response_data = response.json()
            except:
                response_data = {"status_code": response.status_code, "text": response.text}
            
            return success, response_data
            
        except Exception as e:
            return False, {"error": str(e)}

    def test_auth_login(self):
        """Test login with test credentials"""
        success, response = self.make_request(
            'POST', 
            'auth/login',
            {
                "email": "admin@leadflow.com",
                "password": "admin123"
            },
            auth_required=False
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_data = response.get('user', {})
            self.log_test("Login with test credentials", True, f"User: {self.user_data.get('name', 'Unknown')}")
            return True
        else:
            self.log_test("Login with test credentials", False, "", response.get('detail', 'Login failed'))
            return False

    def test_auth_me(self):
        """Test get current user info"""
        success, response = self.make_request('GET', 'auth/me')
        self.log_test("Get current user info", success, 
                     f"User ID: {response.get('user_id', 'N/A')}" if success else "",
                     response.get('detail', 'Failed to get user info'))

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        success, response = self.make_request('GET', 'dashboard/stats')
        if success:
            stats = f"Total leads: {response.get('total_leads', 0)}, New today: {response.get('new_leads_today', 0)}"
            self.log_test("Dashboard statistics", True, stats)
        else:
            self.log_test("Dashboard statistics", False, "", response.get('detail', 'Failed to get stats'))

    def test_dashboard_recent_leads(self):
        """Test recent leads endpoint"""
        success, response = self.make_request('GET', 'dashboard/recent-leads?limit=5')
        if success:
            leads_count = len(response) if isinstance(response, list) else 0
            self.log_test("Recent leads", True, f"Found {leads_count} recent leads")
        else:
            self.log_test("Recent leads", False, "", response.get('detail', 'Failed to get recent leads'))

    def test_create_lead(self):
        """Test creating a new lead"""
        lead_data = {
            "full_name": "Test Lead API",
            "email": "testlead@example.com",
            "phone": "+521234567890",
            "career_interest": "Ingeniería",
            "source": "manual",
            "source_detail": "API Test"
        }
        
        success, response = self.make_request('POST', 'leads', lead_data, 200)
        if success and 'lead_id' in response:
            self.test_lead_id = response['lead_id']
            self.log_test("Create lead", True, f"Lead ID: {self.test_lead_id}")
        else:
            self.log_test("Create lead", False, "", response.get('detail', 'Failed to create lead'))

    def test_get_leads(self):
        """Test getting leads list"""
        success, response = self.make_request('GET', 'leads')
        if success:
            leads_count = len(response) if isinstance(response, list) else 0
            self.log_test("Get leads list", True, f"Found {leads_count} leads")
        else:
            self.log_test("Get leads list", False, "", response.get('detail', 'Failed to get leads'))

    def test_get_lead_detail(self):
        """Test getting specific lead details"""
        if not self.test_lead_id:
            self.log_test("Get lead detail", False, "", "No test lead ID available")
            return
            
        success, response = self.make_request('GET', f'leads/{self.test_lead_id}')
        if success:
            self.log_test("Get lead detail", True, f"Lead: {response.get('full_name', 'Unknown')}")
        else:
            self.log_test("Get lead detail", False, "", response.get('detail', 'Failed to get lead detail'))

    def test_update_lead(self):
        """Test updating lead"""
        if not self.test_lead_id:
            self.log_test("Update lead", False, "", "No test lead ID available")
            return
            
        update_data = {
            "status": "contactado",
            "notes": "Updated via API test"
        }
        
        success, response = self.make_request('PUT', f'leads/{self.test_lead_id}', update_data)
        if success:
            self.log_test("Update lead", True, f"Status: {response.get('status', 'Unknown')}")
        else:
            self.log_test("Update lead", False, "", response.get('detail', 'Failed to update lead'))

    def test_lead_filters(self):
        """Test lead filtering"""
        # Test status filter
        success, response = self.make_request('GET', 'leads?status=nuevo')
        if success:
            count = len(response) if isinstance(response, list) else 0
            self.log_test("Lead filter by status", True, f"Found {count} new leads")
        else:
            self.log_test("Lead filter by status", False, "", response.get('detail', 'Filter failed'))

        # Test source filter
        success, response = self.make_request('GET', 'leads?source=manual')
        if success:
            count = len(response) if isinstance(response, list) else 0
            self.log_test("Lead filter by source", True, f"Found {count} manual leads")
        else:
            self.log_test("Lead filter by source", False, "", response.get('detail', 'Filter failed'))

    def test_conversations(self):
        """Test conversation functionality"""
        if not self.test_lead_id:
            self.log_test("Conversation tests", False, "", "No test lead ID available")
            return

        # Get conversation
        success, response = self.make_request('GET', f'conversations/{self.test_lead_id}')
        if success:
            self.log_test("Get conversation", True, f"Messages: {len(response.get('messages', []))}")
        else:
            self.log_test("Get conversation", False, "", response.get('detail', 'Failed to get conversation'))

        # Add message
        message_data = {
            "lead_id": self.test_lead_id,
            "message": "Test message from API",
            "sender": "agent"
        }
        
        success, response = self.make_request('POST', 'conversations', message_data, 201)
        if success:
            self.log_test("Add conversation message", True, "Message added successfully")
        else:
            self.log_test("Add conversation message", False, "", response.get('detail', 'Failed to add message'))

    def test_appointments(self):
        """Test appointment functionality"""
        if not self.test_lead_id:
            self.log_test("Appointment tests", False, "", "No test lead ID available")
            return

        # Create appointment
        appointment_data = {
            "lead_id": self.test_lead_id,
            "agent_id": self.user_data.get('user_id'),
            "title": "Test Appointment",
            "description": "API test appointment",
            "scheduled_at": (datetime.now() + timedelta(days=1)).isoformat()
        }
        
        success, response = self.make_request('POST', 'appointments', appointment_data, 200)
        if success and 'appointment_id' in response:
            self.test_appointment_id = response['appointment_id']
            self.log_test("Create appointment", True, f"Appointment ID: {self.test_appointment_id}")
        else:
            self.log_test("Create appointment", False, "", response.get('detail', 'Failed to create appointment'))

        # Get appointments
        success, response = self.make_request('GET', 'appointments')
        if success:
            count = len(response) if isinstance(response, list) else 0
            self.log_test("Get appointments", True, f"Found {count} appointments")
        else:
            self.log_test("Get appointments", False, "", response.get('detail', 'Failed to get appointments'))

    def test_users_management(self):
        """Test user management (admin/gerente only)"""
        if self.user_data.get('role') not in ['admin', 'gerente']:
            self.log_test("User management", False, "", "Insufficient permissions")
            return

        # Get users
        success, response = self.make_request('GET', 'users')
        if success:
            count = len(response) if isinstance(response, list) else 0
            self.log_test("Get users list", True, f"Found {count} users")
        else:
            self.log_test("Get users list", False, "", response.get('detail', 'Failed to get users'))

        # Get agents
        success, response = self.make_request('GET', 'users/agents')
        if success:
            count = len(response) if isinstance(response, list) else 0
            self.log_test("Get agents list", True, f"Found {count} agents")
        else:
            self.log_test("Get agents list", False, "", response.get('detail', 'Failed to get agents'))

    def test_webhooks(self):
        """Test webhook functionality (admin/gerente only)"""
        if self.user_data.get('role') not in ['admin', 'gerente']:
            self.log_test("Webhook tests", False, "", "Insufficient permissions")
            return

        # Get webhooks
        success, response = self.make_request('GET', 'webhooks')
        if success:
            count = len(response) if isinstance(response, list) else 0
            self.log_test("Get webhooks", True, f"Found {count} webhooks")
        else:
            self.log_test("Get webhooks", False, "", response.get('detail', 'Failed to get webhooks'))

        # Create webhook
        webhook_data = {
            "name": "Test Webhook",
            "url": "https://example.com/webhook",
            "events": ["lead.created"],
            "is_active": True
        }
        
        success, response = self.make_request('POST', 'webhooks', webhook_data, 201)
        if success and 'webhook_id' in response:
            self.test_webhook_id = response['webhook_id']
            self.log_test("Create webhook", True, f"Webhook ID: {self.test_webhook_id}")
        else:
            self.log_test("Create webhook", False, "", response.get('detail', 'Failed to create webhook'))

    def test_incoming_webhook(self):
        """Test incoming webhook for N8N"""
        webhook_payload = {
            "full_name": "N8N Test Lead",
            "email": "n8ntest@example.com",
            "phone": "+521234567891",
            "career_interest": "Marketing",
            "source": "webhook",
            "source_detail": "N8N Integration Test"
        }
        
        success, response = self.make_request(
            'POST', 
            'webhooks/incoming/lead', 
            webhook_payload, 
            200, 
            auth_required=False
        )
        
        if success:
            self.log_test("Incoming webhook (N8N)", True, f"Lead created: {response.get('lead_id', 'Unknown')}")
        else:
            self.log_test("Incoming webhook (N8N)", False, "", response.get('detail', 'Webhook failed'))

    def test_constants(self):
        """Test constants endpoints"""
        endpoints = ['careers', 'sources', 'statuses', 'roles']
        
        for endpoint in endpoints:
            success, response = self.make_request('GET', f'constants/{endpoint}')
            if success:
                data_key = endpoint
                count = len(response.get(data_key, [])) if isinstance(response.get(data_key), list) else 0
                self.log_test(f"Get {endpoint} constants", True, f"Found {count} items")
            else:
                self.log_test(f"Get {endpoint} constants", False, "", response.get('detail', f'Failed to get {endpoint}'))

    def cleanup_test_data(self):
        """Clean up test data"""
        # Delete test webhook
        if self.test_webhook_id and self.user_data.get('role') in ['admin', 'gerente']:
            success, _ = self.make_request('DELETE', f'webhooks/{self.test_webhook_id}')
            if success:
                print(f"🧹 Cleaned up test webhook: {self.test_webhook_id}")

        # Delete test appointment
        if self.test_appointment_id:
            success, _ = self.make_request('DELETE', f'appointments/{self.test_appointment_id}')
            if success:
                print(f"🧹 Cleaned up test appointment: {self.test_appointment_id}")

        # Delete test lead (admin/gerente only)
        if self.test_lead_id and self.user_data.get('role') in ['admin', 'gerente']:
            success, _ = self.make_request('DELETE', f'leads/{self.test_lead_id}')
            if success:
                print(f"🧹 Cleaned up test lead: {self.test_lead_id}")

    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting LeadFlow Pro API Tests")
        print("=" * 50)
        
        # Authentication tests
        if not self.test_auth_login():
            print("❌ Authentication failed - stopping tests")
            return False
            
        self.test_auth_me()
        
        # Dashboard tests
        self.test_dashboard_stats()
        self.test_dashboard_recent_leads()
        
        # Lead management tests
        self.test_create_lead()
        self.test_get_leads()
        self.test_get_lead_detail()
        self.test_update_lead()
        self.test_lead_filters()
        
        # Conversation tests
        self.test_conversations()
        
        # Appointment tests
        self.test_appointments()
        
        # User management tests
        self.test_users_management()
        
        # Webhook tests
        self.test_webhooks()
        self.test_incoming_webhook()
        
        # Constants tests
        self.test_constants()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Results
        print("\n" + "=" * 50)
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
    tester = LeadFlowAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    summary = tester.get_test_summary()
    with open('/tmp/backend_test_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())