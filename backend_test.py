#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
import uuid

class ShiiiruBETAPITester:
    def __init__(self, base_url="https://game-betting-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.user_token = None
        self.test_user_id = None
        self.test_game_id = None
        self.test_match_id = None
        self.test_bonus_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
            self.failed_tests.append(f"{name}: {details}")

    def make_request(self, method, endpoint, data=None, token=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            success = response.status_code == expected_status
            return success, response.json() if response.content else {}, response.status_code
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}, 0
        except json.JSONDecodeError:
            return False, {"error": "Invalid JSON response"}, response.status_code

    def test_admin_login(self):
        """Test admin login with provided credentials"""
        print("\n🔐 Testing Admin Authentication...")
        
        success, response, status = self.make_request(
            'POST', 'auth/login',
            data={
                "email": "admin@shiiirubet.com",
                "password": "ShiiiruAdmin2025"
            }
        )
        
        if success and 'token' in response:
            self.admin_token = response['token']
            self.log_test("Admin Login", True)
            return True
        else:
            self.log_test("Admin Login", False, f"Status: {status}, Response: {response}")
            return False

    def test_user_registration(self):
        """Test user registration with 150 ECU"""
        print("\n👤 Testing User Registration...")
        
        test_email = f"testuser_{datetime.now().strftime('%H%M%S')}@test.com"
        test_username = f"TestUser_{datetime.now().strftime('%H%M%S')}"
        
        success, response, status = self.make_request(
            'POST', 'auth/register',
            data={
                "email": test_email,
                "username": test_username,
                "password": "TestPassword123"
            }
        )
        
        if success and 'token' in response and response['user']['balance'] == 150.0:
            self.user_token = response['token']
            self.test_user_id = response['user']['id']
            self.log_test("User Registration with 150 ECU", True)
            return True
        else:
            self.log_test("User Registration", False, f"Status: {status}, Response: {response}")
            return False

    def test_user_login(self):
        """Test user login"""
        print("\n🔑 Testing User Login...")
        
        # First register a user
        test_email = f"logintest_{datetime.now().strftime('%H%M%S')}@test.com"
        
        # Register
        success, response, status = self.make_request(
            'POST', 'auth/register',
            data={
                "email": test_email,
                "username": f"LoginTest_{datetime.now().strftime('%H%M%S')}",
                "password": "TestPassword123"
            }
        )
        
        if not success:
            self.log_test("User Login (Registration)", False, "Failed to register test user")
            return False
        
        # Now login
        success, response, status = self.make_request(
            'POST', 'auth/login',
            data={
                "email": test_email,
                "password": "TestPassword123"
            }
        )
        
        if success and 'token' in response:
            self.log_test("User Login", True)
            return True
        else:
            self.log_test("User Login", False, f"Status: {status}, Response: {response}")
            return False

    def test_game_creation(self):
        """Test admin game creation"""
        print("\n🎮 Testing Game Management...")
        
        if not self.admin_token:
            self.log_test("Game Creation", False, "No admin token available")
            return False
        
        success, response, status = self.make_request(
            'POST', 'games',
            data={
                "name": "League of Legends Test",
                "category": "MOBA",
                "icon": "lol-icon"
            },
            token=self.admin_token,
            expected_status=200
        )
        
        if success and 'id' in response:
            self.test_game_id = response['id']
            self.log_test("Game Creation", True)
            return True
        else:
            self.log_test("Game Creation", False, f"Status: {status}, Response: {response}")
            return False

    def test_match_creation(self):
        """Test admin match creation with bet types"""
        print("\n⚔️ Testing Match Creation...")
        
        if not self.admin_token or not self.test_game_id:
            self.log_test("Match Creation", False, "Missing admin token or game ID")
            return False
        
        # Create match with bet types
        match_data = {
            "game_id": self.test_game_id,
            "team1": "Team Alpha",
            "team2": "Team Beta",
            "start_date": (datetime.now() + timedelta(hours=2)).isoformat(),
            "bet_types": [
                {
                    "type_name": "Winner",
                    "description": "Which team will win the match",
                    "options": [
                        {"name": "Team Alpha", "cote": 1.8},
                        {"name": "Team Beta", "cote": 2.1}
                    ]
                },
                {
                    "type_name": "First Blood",
                    "description": "Which team will get first blood",
                    "options": [
                        {"name": "Team Alpha", "cote": 1.9},
                        {"name": "Team Beta", "cote": 1.9}
                    ]
                }
            ]
        }
        
        success, response, status = self.make_request(
            'POST', 'matches',
            data=match_data,
            token=self.admin_token,
            expected_status=200
        )
        
        if success and 'id' in response:
            self.test_match_id = response['id']
            self.log_test("Match Creation with Bet Types", True)
            return True
        else:
            self.log_test("Match Creation", False, f"Status: {status}, Response: {response}")
            return False

    def test_simple_bet_placement(self):
        """Test placing a simple bet"""
        print("\n💰 Testing Simple Bet Placement...")
        
        if not self.user_token or not self.test_match_id:
            self.log_test("Simple Bet Placement", False, "Missing user token or match ID")
            return False
        
        # First get the match to get bet type and option IDs
        success, match_data, status = self.make_request(
            'GET', f'matches/{self.test_match_id}',
            token=self.user_token
        )
        
        if not success:
            self.log_test("Simple Bet Placement", False, "Failed to get match data")
            return False
        
        bet_type = match_data['bet_types'][0]
        option = bet_type['options'][0]
        
        success, response, status = self.make_request(
            'POST', 'bets/place',
            data={
                "match_id": self.test_match_id,
                "bet_type_id": bet_type['id'],
                "option_id": option['id'],
                "amount": 10.0
            },
            token=self.user_token,
            expected_status=200
        )
        
        if success and 'id' in response:
            self.log_test("Simple Bet Placement", True)
            return True
        else:
            self.log_test("Simple Bet Placement", False, f"Status: {status}, Response: {response}")
            return False

    def test_combined_bet_placement(self):
        """Test placing a combined bet (minimum 2 bets)"""
        print("\n🎯 Testing Combined Bet Placement...")
        
        if not self.user_token or not self.test_match_id:
            self.log_test("Combined Bet Placement", False, "Missing user token or match ID")
            return False
        
        # Get match data
        success, match_data, status = self.make_request(
            'GET', f'matches/{self.test_match_id}',
            token=self.user_token
        )
        
        if not success or len(match_data['bet_types']) < 2:
            self.log_test("Combined Bet Placement", False, "Need at least 2 bet types for combined bet")
            return False
        
        # Create combined bet with 2 different bet types
        combined_bets = [
            {
                "match_id": self.test_match_id,
                "bet_type_id": match_data['bet_types'][0]['id'],
                "option_id": match_data['bet_types'][0]['options'][0]['id']
            },
            {
                "match_id": self.test_match_id,
                "bet_type_id": match_data['bet_types'][1]['id'],
                "option_id": match_data['bet_types'][1]['options'][0]['id']
            }
        ]
        
        success, response, status = self.make_request(
            'POST', 'bets/combined',
            data={
                "bets": combined_bets,
                "amount": 15.0
            },
            token=self.user_token,
            expected_status=200
        )
        
        if success and 'id' in response:
            self.log_test("Combined Bet Placement (2+ bets)", True)
            return True
        else:
            self.log_test("Combined Bet Placement", False, f"Status: {status}, Response: {response}")
            return False

    def test_bonus_creation(self):
        """Test admin bonus creation"""
        print("\n🎁 Testing Bonus Creation...")
        
        if not self.admin_token:
            self.log_test("Bonus Creation", False, "No admin token available")
            return False
        
        success, response, status = self.make_request(
            'POST', 'bonuses',
            data={
                "name": "Test Bonus Pack",
                "description": "Test bonus for automated testing",
                "price": 50.0,
                "bonus_type": "free_ecu",
                "value": 25.0,
                "stock": 10
            },
            token=self.admin_token,
            expected_status=200
        )
        
        if success and 'id' in response:
            self.test_bonus_id = response['id']
            self.log_test("Bonus Creation", True)
            return True
        else:
            self.log_test("Bonus Creation", False, f"Status: {status}, Response: {response}")
            return False

    def test_bonus_purchase(self):
        """Test user bonus purchase"""
        print("\n🛒 Testing Bonus Purchase...")
        
        if not self.user_token or not self.test_bonus_id:
            self.log_test("Bonus Purchase", False, "Missing user token or bonus ID")
            return False
        
        success, response, status = self.make_request(
            'POST', f'bonuses/{self.test_bonus_id}/purchase',
            token=self.user_token,
            expected_status=200
        )
        
        if success and 'new_balance' in response:
            self.log_test("Bonus Purchase", True)
            return True
        else:
            self.log_test("Bonus Purchase", False, f"Status: {status}, Response: {response}")
            return False

    def test_bet_validation(self):
        """Test admin bet validation"""
        print("\n✅ Testing Bet Validation...")
        
        if not self.admin_token:
            self.log_test("Bet Validation", False, "No admin token available")
            return False
        
        # Get all bets to find a pending one
        success, bets, status = self.make_request(
            'GET', 'bets/all',
            token=self.admin_token
        )
        
        if not success:
            self.log_test("Bet Validation", False, "Failed to get bets list")
            return False
        
        pending_bets = [bet for bet in bets if bet['status'] == 'pending']
        if not pending_bets:
            self.log_test("Bet Validation", False, "No pending bets to validate")
            return False
        
        bet_id = pending_bets[0]['id']
        
        success, response, status = self.make_request(
            'POST', f'bets/{bet_id}/validate',
            data={"status": "won"},
            token=self.admin_token,
            expected_status=200
        )
        
        if success:
            self.log_test("Bet Validation (Won)", True)
            return True
        else:
            self.log_test("Bet Validation", False, f"Status: {status}, Response: {response}")
            return False

    def test_admin_stats(self):
        """Test admin stats endpoint"""
        print("\n📊 Testing Admin Stats...")
        
        if not self.admin_token:
            self.log_test("Admin Stats", False, "No admin token available")
            return False
        
        success, response, status = self.make_request(
            'GET', 'admin/stats',
            token=self.admin_token
        )
        
        required_fields = ['total_users', 'total_bets', 'total_ecu_in_circulation', 'pending_validations']
        if success and all(field in response for field in required_fields):
            self.log_test("Admin Stats", True)
            return True
        else:
            self.log_test("Admin Stats", False, f"Status: {status}, Missing fields in response")
            return False

    def test_user_dashboard_data(self):
        """Test user dashboard data endpoints"""
        print("\n📱 Testing User Dashboard Data...")
        
        if not self.user_token:
            self.log_test("User Dashboard Data", False, "No user token available")
            return False
        
        endpoints = [
            ('matches?status=upcoming', 'Available Matches'),
            ('bets/my', 'My Bets'),
            ('bets/combined/my', 'My Combined Bets'),
            ('bonuses', 'Available Bonuses'),
            ('transactions/my', 'Transaction History')
        ]
        
        all_success = True
        for endpoint, name in endpoints:
            success, response, status = self.make_request(
                'GET', endpoint,
                token=self.user_token
            )
            
            if success:
                self.log_test(f"User Dashboard - {name}", True)
            else:
                self.log_test(f"User Dashboard - {name}", False, f"Status: {status}")
                all_success = False
        
        return all_success

    def test_balance_updates(self):
        """Test that user balance is updated after bets and validation"""
        print("\n💳 Testing Balance Updates...")
        
        if not self.user_token:
            self.log_test("Balance Updates", False, "No user token available")
            return False
        
        # Get initial balance
        success, user_data, status = self.make_request(
            'GET', 'auth/me',
            token=self.user_token
        )
        
        if not success:
            self.log_test("Balance Updates", False, "Failed to get user data")
            return False
        
        initial_balance = user_data['balance']
        
        # Place a small bet
        if self.test_match_id:
            success, match_data, status = self.make_request(
                'GET', f'matches/{self.test_match_id}',
                token=self.user_token
            )
            
            if success and match_data['bet_types']:
                bet_type = match_data['bet_types'][0]
                option = bet_type['options'][0]
                bet_amount = 5.0
                
                success, response, status = self.make_request(
                    'POST', 'bets/place',
                    data={
                        "match_id": self.test_match_id,
                        "bet_type_id": bet_type['id'],
                        "option_id": option['id'],
                        "amount": bet_amount
                    },
                    token=self.user_token
                )
                
                if success:
                    # Check balance after bet
                    success, user_data, status = self.make_request(
                        'GET', 'auth/me',
                        token=self.user_token
                    )
                    
                    if success and user_data['balance'] == initial_balance - bet_amount:
                        self.log_test("Balance Update After Bet", True)
                        return True
                    else:
                        self.log_test("Balance Update After Bet", False, f"Expected: {initial_balance - bet_amount}, Got: {user_data['balance']}")
                        return False
        
        self.log_test("Balance Updates", False, "Could not test balance updates")
        return False

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting ShiiiruBET API Testing...")
        print(f"Testing against: {self.base_url}")
        
        # Authentication Tests
        admin_login_success = self.test_admin_login()
        user_reg_success = self.test_user_registration()
        user_login_success = self.test_user_login()
        
        # Admin functionality tests
        if admin_login_success:
            self.test_game_creation()
            self.test_match_creation()
            self.test_bonus_creation()
            self.test_admin_stats()
        
        # User functionality tests
        if user_reg_success:
            self.test_simple_bet_placement()
            self.test_combined_bet_placement()
            self.test_bonus_purchase()
            self.test_user_dashboard_data()
            self.test_balance_updates()
        
        # Admin validation tests
        if admin_login_success:
            self.test_bet_validation()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for failure in self.failed_tests:
                print(f"  - {failure}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = ShiiiruBETAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())