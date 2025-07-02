#!/usr/bin/env python3
import requests
import json
import time
import random
from datetime import datetime, timedelta
import unittest
import os

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://9af3cf19-e394-4087-b5b6-9f6d1b23a7f2.preview.emergentagent.com/api"

class BudgetPlannerAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test data and variables that will be used across all tests"""
        cls.test_user = {
            "email": f"testuser{int(time.time())}@example.com",
            "username": f"testuser{int(time.time())}",
            "password": "SecurePassword123!"
        }
        cls.test_user2 = {
            "email": f"testuser2{int(time.time())}@example.com",
            "username": f"testuser2{int(time.time())}",
            "password": "AnotherSecurePassword123!"
        }
        cls.auth_token = None
        cls.auth_token2 = None
        cls.created_transaction_ids = []
        
        # Income categories
        cls.income_categories = [
            "salary", "freelance", "business", "investment", "other_income"
        ]
        
        # Expense categories
        cls.expense_categories = [
            "food", "transportation", "housing", "utilities", 
            "entertainment", "healthcare", "education", "shopping", "other_expense"
        ]
        
        print(f"Testing against backend URL: {BACKEND_URL}")

    def test_01_register_user(self):
        """Test user registration endpoint"""
        print("\n=== Testing User Registration ===")
        
        # Test successful registration
        response = requests.post(
            f"{BACKEND_URL}/auth/register",
            json=self.test_user
        )
        
        self.assertEqual(response.status_code, 200, f"Registration failed: {response.text}")
        data = response.json()
        self.assertIn("access_token", data, "Token not found in response")
        self.assertIn("token_type", data, "Token type not found in response")
        self.__class__.auth_token = data["access_token"]
        
        print(f"Successfully registered user: {self.test_user['username']}")
        
        # Test duplicate registration (should fail)
        response = requests.post(
            f"{BACKEND_URL}/auth/register",
            json=self.test_user
        )
        
        self.assertEqual(response.status_code, 400, "Duplicate registration should fail")
        print("Duplicate registration correctly rejected")
        
        # Register second test user for isolation testing
        response = requests.post(
            f"{BACKEND_URL}/auth/register",
            json=self.test_user2
        )
        
        self.assertEqual(response.status_code, 200, f"Second user registration failed: {response.text}")
        data = response.json()
        self.__class__.auth_token2 = data["access_token"]
        print(f"Successfully registered second user: {self.test_user2['username']}")

    def test_02_login_user(self):
        """Test user login endpoint"""
        print("\n=== Testing User Login ===")
        
        # Test successful login
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
        )
        
        self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
        data = response.json()
        self.assertIn("access_token", data, "Token not found in response")
        self.assertIn("token_type", data, "Token type not found in response")
        print("Login successful")
        
        # Test login with invalid credentials
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={
                "username": self.test_user["username"],
                "password": "WrongPassword123!"
            }
        )
        
        self.assertEqual(response.status_code, 401, "Login with wrong password should fail")
        print("Login with invalid credentials correctly rejected")
        
        # Test login with non-existent user
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={
                "username": "nonexistentuser",
                "password": "SomePassword123!"
            }
        )
        
        self.assertEqual(response.status_code, 401, "Login with non-existent user should fail")
        print("Login with non-existent user correctly rejected")

    def test_03_get_current_user(self):
        """Test getting current user info"""
        print("\n=== Testing Get Current User Info ===")
        
        # Test with valid token
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        response = requests.get(
            f"{BACKEND_URL}/auth/me",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get user info failed: {response.text}")
        data = response.json()
        self.assertEqual(data["username"], self.test_user["username"], "Username mismatch")
        self.assertEqual(data["email"], self.test_user["email"], "Email mismatch")
        print("Successfully retrieved user info")
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalidtoken"}
        response = requests.get(
            f"{BACKEND_URL}/auth/me",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 401, "Request with invalid token should fail")
        print("Request with invalid token correctly rejected")
        
        # Test without token
        response = requests.get(f"{BACKEND_URL}/auth/me")
        self.assertNotEqual(response.status_code, 200, "Request without token should fail")
        print("Request without token correctly rejected")

    def test_04_create_income_transactions(self):
        """Test creating income transactions with different categories"""
        print("\n=== Testing Income Transaction Creation ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        
        # Create one transaction for each income category
        for category in self.income_categories:
            amount = round(random.uniform(5000, 50000), 2)  # Random amount in INR
            transaction = {
                "type": "income",
                "category": category,
                "amount": amount,
                "description": f"Test {category} income in INR",
                "date": (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat()
            }
            
            response = requests.post(
                f"{BACKEND_URL}/transactions",
                headers=headers,
                json=transaction
            )
            
            self.assertEqual(response.status_code, 200, f"Create {category} income failed: {response.text}")
            data = response.json()
            self.__class__.created_transaction_ids.append(data["id"])
            
            # Verify the transaction data
            self.assertEqual(data["type"], "income", "Transaction type mismatch")
            self.assertEqual(data["category"], category, "Transaction category mismatch")
            self.assertEqual(data["amount"], amount, "Transaction amount mismatch")
            self.assertEqual(data["description"], transaction["description"], "Transaction description mismatch")
            
            print(f"Successfully created {category} income transaction of ₹{amount}")

    def test_05_create_expense_transactions(self):
        """Test creating expense transactions with different categories"""
        print("\n=== Testing Expense Transaction Creation ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        
        # Create one transaction for each expense category
        for category in self.expense_categories:
            amount = round(random.uniform(500, 15000), 2)  # Random amount in INR
            transaction = {
                "type": "expense",
                "category": category,
                "amount": amount,
                "description": f"Test {category} expense in INR",
                "date": (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat()
            }
            
            response = requests.post(
                f"{BACKEND_URL}/transactions",
                headers=headers,
                json=transaction
            )
            
            self.assertEqual(response.status_code, 200, f"Create {category} expense failed: {response.text}")
            data = response.json()
            self.__class__.created_transaction_ids.append(data["id"])
            
            # Verify the transaction data
            self.assertEqual(data["type"], "expense", "Transaction type mismatch")
            self.assertEqual(data["category"], category, "Transaction category mismatch")
            self.assertEqual(data["amount"], amount, "Transaction amount mismatch")
            self.assertEqual(data["description"], transaction["description"], "Transaction description mismatch")
            
            print(f"Successfully created {category} expense transaction of ₹{amount}")

    def test_06_get_all_transactions(self):
        """Test retrieving all transactions for the authenticated user"""
        print("\n=== Testing Get All Transactions ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        response = requests.get(
            f"{BACKEND_URL}/transactions",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get transactions failed: {response.text}")
        data = response.json()
        
        # Verify we have at least the number of transactions we created
        self.assertGreaterEqual(len(data), len(self.__class__.created_transaction_ids), 
                              "Not all created transactions were retrieved")
        
        # Verify transaction IDs match what we created
        retrieved_ids = [transaction["id"] for transaction in data]
        for transaction_id in self.__class__.created_transaction_ids:
            self.assertIn(transaction_id, retrieved_ids, f"Transaction {transaction_id} not found")
        
        print(f"Successfully retrieved {len(data)} transactions")

    def test_07_user_isolation(self):
        """Test that users can only access their own transactions"""
        print("\n=== Testing User Isolation ===")
        
        # Create a transaction for the second user
        headers2 = {"Authorization": f"Bearer {self.__class__.auth_token2}"}
        transaction = {
            "type": "income",
            "category": "salary",
            "amount": 25000,
            "description": "Second user salary",
            "date": datetime.utcnow().isoformat()
        }
        
        response = requests.post(
            f"{BACKEND_URL}/transactions",
            headers=headers2,
            json=transaction
        )
        
        self.assertEqual(response.status_code, 200, f"Create transaction for second user failed: {response.text}")
        second_user_transaction = response.json()
        
        # Get transactions for the second user
        response = requests.get(
            f"{BACKEND_URL}/transactions",
            headers=headers2
        )
        
        self.assertEqual(response.status_code, 200, f"Get transactions for second user failed: {response.text}")
        second_user_data = response.json()
        
        # Verify the second user can see their transaction
        second_user_ids = [t["id"] for t in second_user_data]
        self.assertIn(second_user_transaction["id"], second_user_ids, 
                     "Second user cannot see their own transaction")
        
        # Verify the second user cannot see the first user's transactions
        for transaction_id in self.__class__.created_transaction_ids:
            self.assertNotIn(transaction_id, second_user_ids, 
                           f"Second user can see first user's transaction {transaction_id}")
        
        # Get transactions for the first user
        headers1 = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        response = requests.get(
            f"{BACKEND_URL}/transactions",
            headers=headers1
        )
        
        self.assertEqual(response.status_code, 200, f"Get transactions for first user failed: {response.text}")
        first_user_data = response.json()
        
        # Verify the first user cannot see the second user's transaction
        first_user_ids = [t["id"] for t in first_user_data]
        self.assertNotIn(second_user_transaction["id"], first_user_ids, 
                        "First user can see second user's transaction")
        
        print("User isolation is working correctly")

    def test_08_monthly_summary(self):
        """Test monthly summary analytics"""
        print("\n=== Testing Monthly Summary ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        response = requests.get(
            f"{BACKEND_URL}/transactions/summary/monthly",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get monthly summary failed: {response.text}")
        data = response.json()
        
        # Verify we have summary data
        self.assertGreater(len(data), 0, "No monthly summary data returned")
        
        # Verify the structure of the summary data
        for summary in data:
            self.assertIn("month", summary, "Month field missing")
            self.assertIn("year", summary, "Year field missing")
            self.assertIn("total_income", summary, "Total income field missing")
            self.assertIn("total_expense", summary, "Total expense field missing")
            self.assertIn("net_amount", summary, "Net amount field missing")
            self.assertIn("transactions_count", summary, "Transactions count field missing")
            
            # Verify calculations
            self.assertEqual(summary["net_amount"], summary["total_income"] - summary["total_expense"], 
                           "Net amount calculation is incorrect")
        
        print(f"Successfully retrieved monthly summary with {len(data)} months")

    def test_09_category_summary(self):
        """Test category summary analytics"""
        print("\n=== Testing Category Summary ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        response = requests.get(
            f"{BACKEND_URL}/transactions/summary/categories",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get category summary failed: {response.text}")
        data = response.json()
        
        # Verify we have summary data
        self.assertGreater(len(data), 0, "No category summary data returned")
        
        # Verify the structure of the summary data
        for summary in data:
            self.assertIn("category", summary, "Category field missing")
            self.assertIn("type", summary, "Type field missing")
            self.assertIn("total_amount", summary, "Total amount field missing")
            self.assertIn("transactions_count", summary, "Transactions count field missing")
            
            # Verify the category is valid
            if summary["type"] == "income":
                self.assertIn(summary["category"], self.income_categories, f"Invalid income category: {summary['category']}")
            else:
                self.assertIn(summary["category"], self.expense_categories, f"Invalid expense category: {summary['category']}")
        
        print(f"Successfully retrieved category summary with {len(data)} categories")

    def test_10_delete_transaction(self):
        """Test transaction deletion"""
        print("\n=== Testing Transaction Deletion ===")
        
        if not self.__class__.created_transaction_ids:
            self.skipTest("No transactions to delete")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        transaction_id = self.__class__.created_transaction_ids[0]
        
        # Delete the transaction
        response = requests.delete(
            f"{BACKEND_URL}/transactions/{transaction_id}",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Delete transaction failed: {response.text}")
        print(f"Successfully deleted transaction {transaction_id}")
        
        # Verify the transaction is deleted
        response = requests.get(
            f"{BACKEND_URL}/transactions",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get transactions failed: {response.text}")
        data = response.json()
        retrieved_ids = [transaction["id"] for transaction in data]
        self.assertNotIn(transaction_id, retrieved_ids, "Deleted transaction still exists")
        
        # Try to delete a non-existent transaction
        response = requests.delete(
            f"{BACKEND_URL}/transactions/nonexistenttransactionid",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 404, "Deleting non-existent transaction should return 404")
        print("Deleting non-existent transaction correctly returns 404")
        
        # Try to delete another user's transaction
        if len(self.__class__.created_transaction_ids) > 1:
            transaction_id = self.__class__.created_transaction_ids[1]
            headers2 = {"Authorization": f"Bearer {self.__class__.auth_token2}"}
            
            response = requests.delete(
                f"{BACKEND_URL}/transactions/{transaction_id}",
                headers=headers2
            )
            
            self.assertEqual(response.status_code, 404, "Deleting another user's transaction should return 404")
            print("Deleting another user's transaction correctly returns 404")

if __name__ == "__main__":
    unittest.main(verbosity=2)