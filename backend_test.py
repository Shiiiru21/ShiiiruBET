import requests
import sys
import json
from datetime import datetime, timedelta

class ShiiruMaxAPITester:
    def __init__(self, base_url="https://bet-admin-manager.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.user_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_resources = {
            'games': [],
            'matches': [],
            'bets': [],
            'user_bets': []
        }

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.text else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@shiirumax.com", "password": "admin123"}
        )
        if success and 'token' in response:
            self.admin_token = response['token']
            print(f"   Admin user: {response['user']['username']} (role: {response['user']['role']})")
            return True
        return False

    def test_user_login(self):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"email": "player1@test.com", "password": "test123"}
        )
        if success and 'token' in response:
            self.user_token = response['token']
            print(f"   User: {response['user']['username']} (balance: {response['user']['balance_ecus']} écus)")
            return True
        return False

    def test_user_registration(self):
        """Test user registration with new user"""
        timestamp = datetime.now().strftime('%H%M%S')
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={
                "username": f"testuser_{timestamp}",
                "email": f"test_{timestamp}@example.com",
                "password": "testpass123"
            }
        )
        return success

    def test_admin_stats(self):
        """Test admin stats endpoint"""
        success, response = self.run_test(
            "Admin Stats",
            "GET",
            "admin/stats",
            200,
            token=self.admin_token
        )
        if success:
            print(f"   Users: {response.get('total_users', 0)}, Matches: {response.get('total_matches', 0)}")
            print(f"   Bets: {response.get('total_bets', 0)}, Écus: {response.get('total_ecus_circulation', 0)}")
        return success

    def test_create_game(self):
        """Test creating a game"""
        game_data = {
            "name": "League of Legends Test",
            "type": "lol",
            "logo_url": "https://example.com/lol-logo.png"
        }
        success, response = self.run_test(
            "Create Game",
            "POST",
            "admin/games",
            200,
            data=game_data,
            token=self.admin_token
        )
        if success and 'id' in response:
            self.created_resources['games'].append(response['id'])
            print(f"   Created game: {response['name']} (ID: {response['id']})")
        return success

    def test_get_games(self):
        """Test getting games list"""
        success, response = self.run_test(
            "Get Games",
            "GET",
            "admin/games",
            200,
            token=self.admin_token
        )
        if success:
            print(f"   Found {len(response)} games")
        return success

    def test_create_match(self):
        """Test creating a match"""
        if not self.created_resources['games']:
            print("❌ No games available to create match")
            return False
            
        match_date = (datetime.now() + timedelta(days=1)).isoformat()
        match_data = {
            "game_id": self.created_resources['games'][0],
            "team1_name": "Team Alpha",
            "team2_name": "Team Beta",
            "match_date": match_date
        }
        success, response = self.run_test(
            "Create Match",
            "POST",
            "admin/matches",
            200,
            data=match_data,
            token=self.admin_token
        )
        if success and 'id' in response:
            self.created_resources['matches'].append(response['id'])
            print(f"   Created match: {response['team1_name']} vs {response['team2_name']}")
        return success

    def test_get_matches(self):
        """Test getting matches"""
        success, response = self.run_test(
            "Get Matches",
            "GET",
            "matches",
            200
        )
        if success:
            print(f"   Found {len(response)} matches")
        return success

    def test_create_bet(self):
        """Test creating a bet"""
        if not self.created_resources['matches']:
            print("❌ No matches available to create bet")
            return False
            
        bet_data = {
            "match_id": self.created_resources['matches'][0],
            "odds_team1": 1.8,
            "odds_team2": 2.2
        }
        success, response = self.run_test(
            "Create Bet",
            "POST",
            "admin/bets",
            200,
            data=bet_data,
            token=self.admin_token
        )
        if success and 'id' in response:
            self.created_resources['bets'].append(response['id'])
            print(f"   Created bet with odds {response['odds_team1']} / {response['odds_team2']}")
        return success

    def test_update_bet_odds(self):
        """Test updating bet odds"""
        if not self.created_resources['bets']:
            print("❌ No bets available to update odds")
            return False
            
        bet_id = self.created_resources['bets'][0]
        odds_data = {
            "odds_team1": 2.0,
            "odds_team2": 1.9
        }
        success, response = self.run_test(
            "Update Bet Odds",
            "PATCH",
            f"admin/bets/{bet_id}/odds",
            200,
            data=odds_data,
            token=self.admin_token
        )
        return success

    def test_get_bets(self):
        """Test getting available bets"""
        success, response = self.run_test(
            "Get Available Bets",
            "GET",
            "bets",
            200
        )
        if success:
            print(f"   Found {len(response)} available bets")
        return success

    def test_user_profile(self):
        """Test getting user profile"""
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            "user/profile",
            200,
            token=self.user_token
        )
        if success:
            print(f"   User balance: {response.get('balance_ecus', 0)} écus")
        return success

    def test_place_bet(self):
        """Test placing a bet as user"""
        if not self.created_resources['bets']:
            print("❌ No bets available to place")
            return False
            
        bet_id = self.created_resources['bets'][0]
        bet_data = {
            "team_selected": "team1",
            "amount_ecus": 50.0
        }
        success, response = self.run_test(
            "Place User Bet",
            "POST",
            f"bets/{bet_id}/place",
            200,
            data=bet_data,
            token=self.user_token
        )
        if success and 'user_bet' in response:
            user_bet = response['user_bet']
            self.created_resources['user_bets'].append(user_bet['id'])
            print(f"   Placed bet: {bet_data['amount_ecus']} écus on {bet_data['team_selected']}")
            print(f"   Potential win: {user_bet['potential_win']} écus")
        return success

    def test_user_bet_history(self):
        """Test getting user bet history"""
        success, response = self.run_test(
            "Get User Bet History",
            "GET",
            "user/bets",
            200,
            token=self.user_token
        )
        if success:
            print(f"   Found {len(response)} user bets")
        return success

    def test_set_match_result(self):
        """Test setting match result and processing winnings"""
        if not self.created_resources['matches']:
            print("❌ No matches available to set result")
            return False
            
        match_id = self.created_resources['matches'][0]
        result_data = {
            "winner": "team1"
        }
        success, response = self.run_test(
            "Set Match Result",
            "PATCH",
            f"admin/matches/{match_id}/result",
            200,
            data=result_data,
            token=self.admin_token
        )
        if success:
            print(f"   Match result set: {result_data['winner']} wins")
        return success

    def test_admin_users(self):
        """Test getting all users (admin only)"""
        success, response = self.run_test(
            "Get All Users",
            "GET",
            "admin/users",
            200,
            token=self.admin_token
        )
        if success:
            print(f"   Found {len(response)} total users")
        return success

    def test_unauthorized_access(self):
        """Test unauthorized access to admin endpoints"""
        success, response = self.run_test(
            "Unauthorized Admin Access",
            "GET",
            "admin/stats",
            401,  # Should fail without token
        )
        return success

    def test_user_access_to_admin(self):
        """Test user trying to access admin endpoints"""
        success, response = self.run_test(
            "User Access to Admin",
            "GET",
            "admin/stats",
            403,  # Should fail with user token
            token=self.user_token
        )
        return success

def main():
    print("🚀 Starting ShiiruMax API Testing...")
    print("=" * 60)
    
    tester = ShiiruMaxAPITester()
    
    # Authentication Tests
    print("\n📋 AUTHENTICATION TESTS")
    print("-" * 30)
    if not tester.test_admin_login():
        print("❌ Admin login failed, stopping tests")
        return 1
    
    if not tester.test_user_login():
        print("❌ User login failed, stopping tests")
        return 1
    
    tester.test_user_registration()
    
    # Authorization Tests
    print("\n🔒 AUTHORIZATION TESTS")
    print("-" * 30)
    tester.test_unauthorized_access()
    tester.test_user_access_to_admin()
    
    # Admin Functionality Tests
    print("\n👑 ADMIN FUNCTIONALITY TESTS")
    print("-" * 30)
    tester.test_admin_stats()
    tester.test_create_game()
    tester.test_get_games()
    tester.test_create_match()
    tester.test_get_matches()
    tester.test_create_bet()
    tester.test_update_bet_odds()
    tester.test_admin_users()
    
    # User Functionality Tests
    print("\n👤 USER FUNCTIONALITY TESTS")
    print("-" * 30)
    tester.test_user_profile()
    tester.test_get_bets()
    tester.test_place_bet()
    tester.test_user_bet_history()
    
    # Betting System Tests
    print("\n🎯 BETTING SYSTEM TESTS")
    print("-" * 30)
    tester.test_set_match_result()
    
    # Final verification
    tester.test_user_profile()  # Check if balance updated after win
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("✅ Backend API testing PASSED")
        return 0
    else:
        print("❌ Backend API testing FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())