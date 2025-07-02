#!/usr/bin/env python3
import requests
import json
import time
import random
from datetime import datetime, timedelta
import unittest
import os

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://3fae46a5-2028-44b5-8b3f-3b12668ee782.preview.emergentagent.com/api"

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
        cls.created_recurring_transaction_ids = []
        cls.created_budget_ids = []
        
        # Income categories
        cls.income_categories = [
            "salary", "freelance", "business", "investment", "other_income"
        ]
        
        # Expense categories
        cls.expense_categories = [
            "food", "transportation", "housing", "utilities", 
            "entertainment", "healthcare", "education", "shopping", "other_expense"
        ]
        
        # Recurrence types
        cls.recurrence_types = [
            "daily", "weekly", "monthly", "yearly"
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

    def test_10_create_transactions_with_tags(self):
        """Test creating transactions with tags"""
        print("\n=== Testing Transaction Creation with Tags ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        
        # Create transactions with tags
        test_tags = [
            ["essential", "monthly"],
            ["entertainment", "weekend", "friends"],
            ["health", "important"],
            ["shopping", "online", "discount"]
        ]
        
        for i, tags in enumerate(test_tags):
            transaction = {
                "type": "expense",
                "category": random.choice(self.expense_categories),
                "amount": round(random.uniform(500, 5000), 2),
                "description": f"Test transaction with tags {', '.join(tags)}",
                "date": datetime.utcnow().isoformat(),
                "tags": tags
            }
            
            response = requests.post(
                f"{BACKEND_URL}/transactions",
                headers=headers,
                json=transaction
            )
            
            self.assertEqual(response.status_code, 200, f"Create transaction with tags failed: {response.text}")
            data = response.json()
            self.__class__.created_transaction_ids.append(data["id"])
            
            # Verify the tags were saved correctly
            self.assertEqual(data["tags"], tags, "Tags mismatch")
            print(f"Successfully created transaction with tags: {tags}")
        
        # Retrieve transactions and verify tags are present
        response = requests.get(
            f"{BACKEND_URL}/transactions",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get transactions failed: {response.text}")
        data = response.json()
        
        # Find the transactions we just created and verify tags
        for transaction in data:
            if transaction["id"] in self.__class__.created_transaction_ids[-len(test_tags):]:
                self.assertIn("tags", transaction, "Tags field missing")
                self.assertIsInstance(transaction["tags"], list, "Tags should be a list")
                print(f"Retrieved transaction has tags: {transaction['tags']}")
        
        print("Tags are correctly stored and retrieved")

    def test_11_recurring_transactions(self):
        """Test creating recurring transactions with different recurrence types"""
        print("\n=== Testing Recurring Transactions ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        
        # Test each recurrence type
        for recurrence_type in self.recurrence_types:
            # Create a recurring transaction
            transaction = {
                "type": "expense",
                "category": random.choice(self.expense_categories),
                "amount": round(random.uniform(1000, 10000), 2),
                "description": f"Recurring {recurrence_type} expense",
                "date": datetime.utcnow().isoformat(),
                "is_recurring": True,
                "recurrence_type": recurrence_type
            }
            
            response = requests.post(
                f"{BACKEND_URL}/transactions",
                headers=headers,
                json=transaction
            )
            
            self.assertEqual(response.status_code, 200, f"Create recurring transaction failed: {response.text}")
            data = response.json()
            self.__class__.created_recurring_transaction_ids.append(data["id"])
            
            # Verify recurring transaction fields
            self.assertEqual(data["is_recurring"], True, "is_recurring should be True")
            self.assertEqual(data["recurrence_type"], recurrence_type, "recurrence_type mismatch")
            self.assertIsNotNone(data["next_occurrence"], "next_occurrence should not be None")
            
            # Verify next_occurrence is calculated correctly
            transaction_date = datetime.fromisoformat(data["date"].replace("Z", "+00:00"))
            next_occurrence = datetime.fromisoformat(data["next_occurrence"].replace("Z", "+00:00"))
            
            if recurrence_type == "daily":
                expected_next = transaction_date + timedelta(days=1)
                self.assertEqual(next_occurrence.date(), expected_next.date(), "Daily next_occurrence incorrect")
            elif recurrence_type == "weekly":
                expected_next = transaction_date + timedelta(weeks=1)
                self.assertEqual(next_occurrence.date(), expected_next.date(), "Weekly next_occurrence incorrect")
            elif recurrence_type == "monthly":
                if transaction_date.month == 12:
                    expected_next = transaction_date.replace(year=transaction_date.year + 1, month=1)
                else:
                    expected_next = transaction_date.replace(month=transaction_date.month + 1)
                self.assertEqual(next_occurrence.date(), expected_next.date(), "Monthly next_occurrence incorrect")
            elif recurrence_type == "yearly":
                expected_next = transaction_date.replace(year=transaction_date.year + 1)
                self.assertEqual(next_occurrence.date(), expected_next.date(), "Yearly next_occurrence incorrect")
            
            print(f"Successfully created {recurrence_type} recurring transaction with next occurrence on {next_occurrence.date()}")
        
        # Test creating a transaction with invalid recurrence type
        transaction = {
            "type": "expense",
            "category": "food",
            "amount": 1000,
            "description": "Invalid recurring transaction",
            "is_recurring": True,
            "recurrence_type": "invalid_type"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/transactions",
            headers=headers,
            json=transaction
        )
        
        self.assertNotEqual(response.status_code, 200, "Creating transaction with invalid recurrence type should fail")
        print("Invalid recurrence type correctly rejected")

    def test_12_process_recurring_transactions(self):
        """Test processing recurring transactions"""
        print("\n=== Testing Process Recurring Transactions ===")
        
        # Call the process-recurring endpoint
        response = requests.post(
            f"{BACKEND_URL}/transactions/process-recurring"
        )
        
        self.assertEqual(response.status_code, 200, f"Process recurring transactions failed: {response.text}")
        data = response.json()
        self.assertIn("message", data, "Response should contain a message")
        print(f"Process recurring transactions response: {data['message']}")
        
        # Get all transactions to verify new ones were created
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        response = requests.get(
            f"{BACKEND_URL}/transactions",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get transactions failed: {response.text}")
        transactions = response.json()
        
        # Check if auto-generated transactions exist
        auto_generated_count = 0
        for transaction in transactions:
            if "(Auto-generated)" in transaction.get("description", ""):
                auto_generated_count += 1
                self.assertEqual(transaction["is_recurring"], False, "Auto-generated transaction should not be recurring")
                print(f"Found auto-generated transaction: {transaction['description']}")
        
        print(f"Found {auto_generated_count} auto-generated transactions")
        
        # Check if original recurring transactions have updated next_occurrence
        for transaction_id in self.__class__.created_recurring_transaction_ids:
            found = False
            for transaction in transactions:
                if transaction["id"] == transaction_id:
                    found = True
                    self.assertEqual(transaction["is_recurring"], True, "Original transaction should still be recurring")
                    self.assertIsNotNone(transaction["next_occurrence"], "next_occurrence should not be None")
                    print(f"Original recurring transaction {transaction_id} has next occurrence: {transaction['next_occurrence']}")
                    break
            
            self.assertTrue(found, f"Original recurring transaction {transaction_id} not found")

    def test_13_budget_management(self):
        """Test budget management system"""
        print("\n=== Testing Budget Management ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        # Create budgets for different expense categories
        for category in self.expense_categories[:3]:  # Test with first 3 categories
            budget_amount = round(random.uniform(5000, 20000), 2)
            budget = {
                "category": category,
                "budget_amount": budget_amount,
                "month": current_month
            }
            
            response = requests.post(
                f"{BACKEND_URL}/budgets",
                headers=headers,
                json=budget
            )
            
            self.assertEqual(response.status_code, 200, f"Create budget failed: {response.text}")
            data = response.json()
            self.__class__.created_budget_ids.append(data["id"])
            
            # Verify budget fields
            self.assertEqual(data["category"], category, "Budget category mismatch")
            self.assertEqual(data["budget_amount"], budget_amount, "Budget amount mismatch")
            self.assertEqual(data["month"], current_month, "Budget month mismatch")
            self.assertIn("spent_amount", data, "spent_amount field missing")
            self.assertIn("remaining_amount", data, "remaining_amount field missing")
            self.assertIn("percentage_used", data, "percentage_used field missing")
            
            # Verify calculations
            self.assertEqual(data["remaining_amount"], budget_amount - data["spent_amount"], 
                           "remaining_amount calculation incorrect")
            
            expected_percentage = (data["spent_amount"] / budget_amount * 100) if budget_amount > 0 else 0
            self.assertAlmostEqual(data["percentage_used"], expected_percentage, places=2, 
                                 msg="percentage_used calculation incorrect")
            
            print(f"Successfully created budget for {category}: ₹{budget_amount} ({data['percentage_used']:.2f}% used)")
        
        # Test retrieving budgets with month filter
        response = requests.get(
            f"{BACKEND_URL}/budgets?month={current_month}",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get budgets failed: {response.text}")
        data = response.json()
        
        # Verify we have the budgets we created
        self.assertGreaterEqual(len(data), len(self.__class__.created_budget_ids), 
                              "Not all created budgets were retrieved")
        
        retrieved_ids = [budget["id"] for budget in data]
        for budget_id in self.__class__.created_budget_ids:
            self.assertIn(budget_id, retrieved_ids, f"Budget {budget_id} not found")
        
        print(f"Successfully retrieved {len(data)} budgets for {current_month}")
        
        # Test updating an existing budget
        if self.__class__.created_budget_ids:
            # Get the first budget we created
            budget_id = self.__class__.created_budget_ids[0]
            budget_data = next((b for b in data if b["id"] == budget_id), None)
            
            if budget_data:
                # Update the budget amount
                new_amount = budget_data["budget_amount"] + 5000
                update_budget = {
                    "category": budget_data["category"],
                    "budget_amount": new_amount,
                    "month": budget_data["month"]
                }
                
                response = requests.post(
                    f"{BACKEND_URL}/budgets",
                    headers=headers,
                    json=update_budget
                )
                
                self.assertEqual(response.status_code, 200, f"Update budget failed: {response.text}")
                updated_data = response.json()
                
                # Verify the budget was updated
                self.assertEqual(updated_data["id"], budget_id, "Budget ID should not change on update")
                self.assertEqual(updated_data["budget_amount"], new_amount, "Budget amount not updated")
                
                print(f"Successfully updated budget for {budget_data['category']} from ₹{budget_data['budget_amount']} to ₹{new_amount}")
        
        # Test overspending scenario by creating an expense that exceeds the budget
        if self.__class__.created_budget_ids:
            # Get the first budget we created
            budget_id = self.__class__.created_budget_ids[0]
            budget_data = next((b for b in data if b["id"] == budget_id), None)
            
            if budget_data:
                # Create an expense that exceeds the budget
                transaction = {
                    "type": "expense",
                    "category": budget_data["category"],
                    "amount": budget_data["budget_amount"] * 1.5,  # 150% of budget
                    "description": "Overspending test transaction",
                    "date": datetime.utcnow().isoformat()
                }
                
                response = requests.post(
                    f"{BACKEND_URL}/transactions",
                    headers=headers,
                    json=transaction
                )
                
                self.assertEqual(response.status_code, 200, f"Create overspending transaction failed: {response.text}")
                transaction_data = response.json()
                self.__class__.created_transaction_ids.append(transaction_data["id"])
                
                # Get the budget again to check if spent_amount and percentage_used are updated
                response = requests.get(
                    f"{BACKEND_URL}/budgets?month={current_month}",
                    headers=headers
                )
                
                self.assertEqual(response.status_code, 200, f"Get budgets after overspending failed: {response.text}")
                updated_budgets = response.json()
                
                # Find our budget
                updated_budget = next((b for b in updated_budgets if b["id"] == budget_id), None)
                
                if updated_budget:
                    # Verify overspending is reflected
                    self.assertGreater(updated_budget["spent_amount"], updated_budget["budget_amount"], 
                                     "spent_amount should exceed budget_amount")
                    self.assertLess(updated_budget["remaining_amount"], 0, 
                                  "remaining_amount should be negative")
                    self.assertGreater(updated_budget["percentage_used"], 100, 
                                     "percentage_used should exceed 100%")
                    
                    print(f"Overspending correctly reflected: spent ₹{updated_budget['spent_amount']} of ₹{updated_budget['budget_amount']} budget ({updated_budget['percentage_used']:.2f}%)")

    def test_14_advanced_search(self):
        """Test advanced search and filtering"""
        print("\n=== Testing Advanced Search & Filtering ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        
        # 1. Test text search in description
        search_term = "test"
        response = requests.post(
            f"{BACKEND_URL}/transactions/search",
            headers=headers,
            json={"query": search_term}
        )
        
        self.assertEqual(response.status_code, 200, f"Search by description failed: {response.text}")
        data = response.json()
        
        # Verify results contain the search term
        for transaction in data:
            self.assertIn(search_term.lower(), transaction["description"].lower(), 
                        f"Transaction description does not contain search term: {transaction['description']}")
        
        print(f"Successfully searched for '{search_term}' in descriptions, found {len(data)} matches")
        
        # 2. Test filtering by category
        category = random.choice(self.expense_categories)
        response = requests.post(
            f"{BACKEND_URL}/transactions/search",
            headers=headers,
            json={"category": category}
        )
        
        self.assertEqual(response.status_code, 200, f"Filter by category failed: {response.text}")
        data = response.json()
        
        # Verify results have the correct category
        for transaction in data:
            self.assertEqual(transaction["category"], category, 
                           f"Transaction category mismatch: {transaction['category']} != {category}")
        
        print(f"Successfully filtered by category '{category}', found {len(data)} matches")
        
        # 3. Test filtering by type
        transaction_type = "expense"
        response = requests.post(
            f"{BACKEND_URL}/transactions/search",
            headers=headers,
            json={"type": transaction_type}
        )
        
        self.assertEqual(response.status_code, 200, f"Filter by type failed: {response.text}")
        data = response.json()
        
        # Verify results have the correct type
        for transaction in data:
            self.assertEqual(transaction["type"], transaction_type, 
                           f"Transaction type mismatch: {transaction['type']} != {transaction_type}")
        
        print(f"Successfully filtered by type '{transaction_type}', found {len(data)} matches")
        
        # 4. Test date range filtering
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        response = requests.post(
            f"{BACKEND_URL}/transactions/search",
            headers=headers,
            json={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )
        
        self.assertEqual(response.status_code, 200, f"Filter by date range failed: {response.text}")
        data = response.json()
        
        # Verify results are within the date range
        for transaction in data:
            transaction_date = datetime.fromisoformat(transaction["date"].replace("Z", "+00:00"))
            self.assertGreaterEqual(transaction_date, start_date, 
                                  f"Transaction date {transaction_date} before start date {start_date}")
            self.assertLessEqual(transaction_date, end_date, 
                               f"Transaction date {transaction_date} after end date {end_date}")
        
        print(f"Successfully filtered by date range {start_date.date()} to {end_date.date()}, found {len(data)} matches")
        
        # 5. Test amount range filtering
        min_amount = 1000
        max_amount = 10000
        
        response = requests.post(
            f"{BACKEND_URL}/transactions/search",
            headers=headers,
            json={
                "min_amount": min_amount,
                "max_amount": max_amount
            }
        )
        
        self.assertEqual(response.status_code, 200, f"Filter by amount range failed: {response.text}")
        data = response.json()
        
        # Verify results are within the amount range
        for transaction in data:
            self.assertGreaterEqual(transaction["amount"], min_amount, 
                                  f"Transaction amount {transaction['amount']} below min amount {min_amount}")
            self.assertLessEqual(transaction["amount"], max_amount, 
                               f"Transaction amount {transaction['amount']} above max amount {max_amount}")
        
        print(f"Successfully filtered by amount range ₹{min_amount} to ₹{max_amount}, found {len(data)} matches")
        
        # 6. Test tag-based filtering
        if hasattr(self, 'test_tags') and self.test_tags:
            tag = self.test_tags[0][0]  # Use the first tag from our test
        else:
            tag = "essential"  # Fallback tag
            
        response = requests.post(
            f"{BACKEND_URL}/transactions/search",
            headers=headers,
            json={"tags": [tag]}
        )
        
        self.assertEqual(response.status_code, 200, f"Filter by tag failed: {response.text}")
        data = response.json()
        
        # Verify results contain the tag
        for transaction in data:
            self.assertIn(tag, transaction["tags"], 
                        f"Transaction tags {transaction['tags']} do not include {tag}")
        
        print(f"Successfully filtered by tag '{tag}', found {len(data)} matches")
        
        # 7. Test complex filter combination
        complex_filter = {
            "type": "expense",
            "min_amount": 500,
            "max_amount": 15000,
            "start_date": (datetime.utcnow() - timedelta(days=60)).isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
        
        response = requests.post(
            f"{BACKEND_URL}/transactions/search",
            headers=headers,
            json=complex_filter
        )
        
        self.assertEqual(response.status_code, 200, f"Complex filter failed: {response.text}")
        data = response.json()
        
        # Verify results match all criteria
        for transaction in data:
            self.assertEqual(transaction["type"], complex_filter["type"], "Transaction type mismatch")
            self.assertGreaterEqual(transaction["amount"], complex_filter["min_amount"], "Transaction amount below min")
            self.assertLessEqual(transaction["amount"], complex_filter["max_amount"], "Transaction amount above max")
            
            transaction_date = datetime.fromisoformat(transaction["date"].replace("Z", "+00:00"))
            start_date = datetime.fromisoformat(complex_filter["start_date"].replace("Z", "+00:00") if "Z" in complex_filter["start_date"] else complex_filter["start_date"])
            end_date = datetime.fromisoformat(complex_filter["end_date"].replace("Z", "+00:00") if "Z" in complex_filter["end_date"] else complex_filter["end_date"])
            
            self.assertGreaterEqual(transaction_date, start_date, "Transaction date before start date")
            self.assertLessEqual(transaction_date, end_date, "Transaction date after end date")
        
        print(f"Successfully applied complex filter, found {len(data)} matches")

    def test_15_daily_trends(self):
        """Test daily trends analytics"""
        print("\n=== Testing Daily Trends Analytics ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        
        # Test with default 30 days
        response = requests.get(
            f"{BACKEND_URL}/transactions/trends/daily",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get daily trends failed: {response.text}")
        data = response.json()
        
        # Verify the structure of the trend data
        for trend in data:
            self.assertIn("date", trend, "Date field missing")
            self.assertIn("income", trend, "Income field missing")
            self.assertIn("expense", trend, "Expense field missing")
            self.assertIn("net", trend, "Net field missing")
            
            # Verify calculations
            self.assertEqual(trend["net"], trend["income"] - trend["expense"], 
                           "Net calculation is incorrect")
            
            # Verify date format
            self.assertRegex(trend["date"], r"^\d{4}-\d{2}-\d{2}$", 
                           f"Date format incorrect: {trend['date']}")
        
        print(f"Successfully retrieved daily trends for default 30 days, got {len(data)} days")
        
        # Test with custom days parameter
        custom_days = 7
        response = requests.get(
            f"{BACKEND_URL}/transactions/trends/daily?days={custom_days}",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get daily trends with custom days failed: {response.text}")
        data = response.json()
        
        # We might not have data for all days, so we can't assert exact length
        print(f"Successfully retrieved daily trends for {custom_days} days, got {len(data)} days with data")
        
        # Verify data is sorted chronologically
        if len(data) > 1:
            for i in range(1, len(data)):
                prev_date = datetime.strptime(data[i-1]["date"], "%Y-%m-%d")
                curr_date = datetime.strptime(data[i]["date"], "%Y-%m-%d")
                self.assertLessEqual(prev_date, curr_date, "Dates are not in chronological order")
            
            print("Daily trends data is correctly sorted chronologically")

    def test_16_delete_transaction(self):
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

    def test_17_multi_currency_transactions(self):
        """Test creating transactions with different currencies"""
        print("\n=== Testing Multi-Currency Transactions ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        
        # Test creating USD income transaction
        usd_income = {
            "type": "income",
            "category": random.choice(self.income_categories),
            "amount": round(random.uniform(100, 1000), 2),  # USD amount
            "currency": "USD",
            "description": "Test USD income transaction",
            "date": datetime.utcnow().isoformat()
        }
        
        response = requests.post(
            f"{BACKEND_URL}/transactions",
            headers=headers,
            json=usd_income
        )
        
        self.assertEqual(response.status_code, 200, f"Create USD income transaction failed: {response.text}")
        usd_income_data = response.json()
        self.__class__.created_transaction_ids.append(usd_income_data["id"])
        
        # Verify USD transaction data
        self.assertEqual(usd_income_data["currency"], "USD", "Currency should be USD")
        self.assertEqual(usd_income_data["amount"], usd_income["amount"], "Amount mismatch")
        print(f"Successfully created USD income transaction of ${usd_income_data['amount']}")
        
        # Test creating USD expense transaction
        usd_expense = {
            "type": "expense",
            "category": random.choice(self.expense_categories),
            "amount": round(random.uniform(50, 500), 2),  # USD amount
            "currency": "USD",
            "description": "Test USD expense transaction",
            "date": datetime.utcnow().isoformat()
        }
        
        response = requests.post(
            f"{BACKEND_URL}/transactions",
            headers=headers,
            json=usd_expense
        )
        
        self.assertEqual(response.status_code, 200, f"Create USD expense transaction failed: {response.text}")
        usd_expense_data = response.json()
        self.__class__.created_transaction_ids.append(usd_expense_data["id"])
        
        # Verify USD transaction data
        self.assertEqual(usd_expense_data["currency"], "USD", "Currency should be USD")
        self.assertEqual(usd_expense_data["amount"], usd_expense["amount"], "Amount mismatch")
        print(f"Successfully created USD expense transaction of ${usd_expense_data['amount']}")
        
        # Test creating INR transaction explicitly
        inr_transaction = {
            "type": "expense",
            "category": random.choice(self.expense_categories),
            "amount": round(random.uniform(1000, 5000), 2),
            "currency": "INR",
            "description": "Test explicit INR transaction",
            "date": datetime.utcnow().isoformat()
        }
        
        response = requests.post(
            f"{BACKEND_URL}/transactions",
            headers=headers,
            json=inr_transaction
        )
        
        self.assertEqual(response.status_code, 200, f"Create explicit INR transaction failed: {response.text}")
        inr_data = response.json()
        self.__class__.created_transaction_ids.append(inr_data["id"])
        
        # Verify INR transaction data
        self.assertEqual(inr_data["currency"], "INR", "Currency should be INR")
        print(f"Successfully created explicit INR transaction of ₹{inr_data['amount']}")
        
        # Test default currency (should be INR)
        default_transaction = {
            "type": "expense",
            "category": random.choice(self.expense_categories),
            "amount": round(random.uniform(1000, 5000), 2),
            "description": "Test default currency transaction",
            "date": datetime.utcnow().isoformat()
        }
        
        response = requests.post(
            f"{BACKEND_URL}/transactions",
            headers=headers,
            json=default_transaction
        )
        
        self.assertEqual(response.status_code, 200, f"Create default currency transaction failed: {response.text}")
        default_data = response.json()
        self.__class__.created_transaction_ids.append(default_data["id"])
        
        # Verify default currency is INR
        self.assertEqual(default_data["currency"], "INR", "Default currency should be INR")
        print(f"Successfully created default currency transaction (INR) of ₹{default_data['amount']}")
        
        # Retrieve transactions and verify currencies are preserved
        response = requests.get(
            f"{BACKEND_URL}/transactions",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get transactions failed: {response.text}")
        transactions = response.json()
        
        # Find our test transactions
        for transaction_id in [usd_income_data["id"], usd_expense_data["id"], inr_data["id"], default_data["id"]]:
            transaction = next((t for t in transactions if t["id"] == transaction_id), None)
            self.assertIsNotNone(transaction, f"Transaction {transaction_id} not found")
            
            if transaction_id in [usd_income_data["id"], usd_expense_data["id"]]:
                self.assertEqual(transaction["currency"], "USD", f"Transaction {transaction_id} should have USD currency")
            else:
                self.assertEqual(transaction["currency"], "INR", f"Transaction {transaction_id} should have INR currency")
        
        print("Multi-currency transactions are correctly stored and retrieved")

    def test_18_currency_conversion(self):
        """Test currency conversion endpoints"""
        print("\n=== Testing Currency Conversion ===")
        
        # Test getting currency rates
        response = requests.get(f"{BACKEND_URL}/currency/rates")
        
        self.assertEqual(response.status_code, 200, f"Get currency rates failed: {response.text}")
        rates_data = response.json()
        
        # Verify rates data structure
        self.assertIn("USD_to_INR", rates_data, "USD to INR rate missing")
        self.assertIn("INR_to_USD", rates_data, "INR to USD rate missing")
        self.assertIn("last_updated", rates_data, "Last updated timestamp missing")
        
        # Verify rates are reasonable
        self.assertGreater(rates_data["USD_to_INR"], 70, "USD to INR rate seems too low")
        self.assertLess(rates_data["USD_to_INR"], 100, "USD to INR rate seems too high")
        self.assertGreater(rates_data["INR_to_USD"], 0.01, "INR to USD rate seems too low")
        self.assertLess(rates_data["INR_to_USD"], 0.02, "INR to USD rate seems too high")
        
        print(f"Successfully retrieved currency rates: 1 USD = {rates_data['USD_to_INR']} INR, 1 INR = {rates_data['INR_to_USD']} USD")
        
        # Test currency conversion endpoint
        test_amount = 100
        
        # USD to INR
        response = requests.post(
            f"{BACKEND_URL}/currency/convert",
            json={
                "amount": test_amount,
                "from_currency": "USD",
                "to_currency": "INR"
            }
        )
        
        self.assertEqual(response.status_code, 200, f"USD to INR conversion failed: {response.text}")
        usd_to_inr = response.json()
        
        # Verify conversion data
        self.assertEqual(usd_to_inr["original_amount"], test_amount, "Original amount mismatch")
        self.assertEqual(usd_to_inr["from_currency"], "USD", "From currency mismatch")
        self.assertEqual(usd_to_inr["to_currency"], "INR", "To currency mismatch")
        self.assertGreater(usd_to_inr["converted_amount"], test_amount, "USD to INR conversion should increase the amount")
        self.assertEqual(usd_to_inr["converted_amount"], round(test_amount * usd_to_inr["rate"], 2), "Conversion calculation incorrect")
        
        print(f"Successfully converted {test_amount} USD to {usd_to_inr['converted_amount']} INR (rate: {usd_to_inr['rate']})")
        
        # INR to USD
        response = requests.post(
            f"{BACKEND_URL}/currency/convert",
            json={
                "amount": test_amount,
                "from_currency": "INR",
                "to_currency": "USD"
            }
        )
        
        self.assertEqual(response.status_code, 200, f"INR to USD conversion failed: {response.text}")
        inr_to_usd = response.json()
        
        # Verify conversion data
        self.assertEqual(inr_to_usd["original_amount"], test_amount, "Original amount mismatch")
        self.assertEqual(inr_to_usd["from_currency"], "INR", "From currency mismatch")
        self.assertEqual(inr_to_usd["to_currency"], "USD", "To currency mismatch")
        self.assertLess(inr_to_usd["converted_amount"], test_amount, "INR to USD conversion should decrease the amount")
        self.assertEqual(inr_to_usd["converted_amount"], round(test_amount * inr_to_usd["rate"], 2), "Conversion calculation incorrect")
        
        print(f"Successfully converted {test_amount} INR to {inr_to_usd['converted_amount']} USD (rate: {inr_to_usd['rate']})")
        
        # Same currency conversion (should return same amount)
        response = requests.post(
            f"{BACKEND_URL}/currency/convert",
            json={
                "amount": test_amount,
                "from_currency": "USD",
                "to_currency": "USD"
            }
        )
        
        self.assertEqual(response.status_code, 200, f"Same currency conversion failed: {response.text}")
        same_currency = response.json()
        
        # Verify same currency conversion
        self.assertEqual(same_currency["converted_amount"], test_amount, "Same currency conversion should return same amount")
        self.assertEqual(same_currency["rate"], 1.0, "Same currency rate should be 1.0")
        
        print(f"Successfully verified same currency conversion: {test_amount} USD = {same_currency['converted_amount']} USD")

    def test_19_multi_currency_budgets(self):
        """Test budgets with different currencies"""
        print("\n=== Testing Multi-Currency Budgets ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        # Create USD budget
        usd_budget = {
            "category": random.choice(self.expense_categories),
            "budget_amount": round(random.uniform(100, 1000), 2),
            "currency": "USD",
            "month": current_month
        }
        
        response = requests.post(
            f"{BACKEND_URL}/budgets",
            headers=headers,
            json=usd_budget
        )
        
        self.assertEqual(response.status_code, 200, f"Create USD budget failed: {response.text}")
        usd_budget_data = response.json()
        self.__class__.created_budget_ids.append(usd_budget_data["id"])
        
        # Verify USD budget
        self.assertEqual(usd_budget_data["currency"], "USD", "Budget currency should be USD")
        self.assertEqual(usd_budget_data["budget_amount"], usd_budget["budget_amount"], "Budget amount mismatch")
        print(f"Successfully created USD budget for {usd_budget_data['category']}: ${usd_budget_data['budget_amount']}")
        
        # Create INR budget for the same category (should be allowed since currency is different)
        inr_budget = {
            "category": usd_budget["category"],  # Same category as USD budget
            "budget_amount": round(random.uniform(5000, 20000), 2),
            "currency": "INR",
            "month": current_month
        }
        
        response = requests.post(
            f"{BACKEND_URL}/budgets",
            headers=headers,
            json=inr_budget
        )
        
        self.assertEqual(response.status_code, 200, f"Create INR budget for same category failed: {response.text}")
        inr_budget_data = response.json()
        self.__class__.created_budget_ids.append(inr_budget_data["id"])
        
        # Verify INR budget
        self.assertEqual(inr_budget_data["currency"], "INR", "Budget currency should be INR")
        self.assertEqual(inr_budget_data["budget_amount"], inr_budget["budget_amount"], "Budget amount mismatch")
        print(f"Successfully created INR budget for same category {inr_budget_data['category']}: ₹{inr_budget_data['budget_amount']}")
        
        # Create USD expense for the budget category
        usd_expense = {
            "type": "expense",
            "category": usd_budget["category"],
            "amount": usd_budget["budget_amount"] * 0.5,  # 50% of budget
            "currency": "USD",
            "description": "Test USD expense for budget",
            "date": datetime.utcnow().isoformat()
        }
        
        response = requests.post(
            f"{BACKEND_URL}/transactions",
            headers=headers,
            json=usd_expense
        )
        
        self.assertEqual(response.status_code, 200, f"Create USD expense for budget failed: {response.text}")
        usd_expense_data = response.json()
        self.__class__.created_transaction_ids.append(usd_expense_data["id"])
        print(f"Created USD expense of ${usd_expense['amount']} for budget category {usd_budget['category']}")
        
        # Create INR expense for the same budget category
        inr_expense = {
            "type": "expense",
            "category": inr_budget["category"],
            "amount": inr_budget["budget_amount"] * 0.5,  # 50% of budget
            "currency": "INR",
            "description": "Test INR expense for budget",
            "date": datetime.utcnow().isoformat()
        }
        
        response = requests.post(
            f"{BACKEND_URL}/transactions",
            headers=headers,
            json=inr_expense
        )
        
        self.assertEqual(response.status_code, 200, f"Create INR expense for budget failed: {response.text}")
        inr_expense_data = response.json()
        self.__class__.created_transaction_ids.append(inr_expense_data["id"])
        print(f"Created INR expense of ₹{inr_expense['amount']} for budget category {inr_budget['category']}")
        
        # Get budgets and verify spent amounts are calculated correctly
        response = requests.get(
            f"{BACKEND_URL}/budgets?month={current_month}",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get budgets failed: {response.text}")
        budgets = response.json()
        
        # Find our test budgets
        usd_budget_updated = next((b for b in budgets if b["id"] == usd_budget_data["id"]), None)
        inr_budget_updated = next((b for b in budgets if b["id"] == inr_budget_data["id"]), None)
        
        self.assertIsNotNone(usd_budget_updated, "USD budget not found")
        self.assertIsNotNone(inr_budget_updated, "INR budget not found")
        
        # Verify USD budget spent amount (should only include USD transactions)
        self.assertAlmostEqual(usd_budget_updated["spent_amount"], usd_expense["amount"], places=2, 
                             msg="USD budget spent amount incorrect")
        self.assertAlmostEqual(usd_budget_updated["percentage_used"], 50.0, places=2, 
                             msg="USD budget percentage used incorrect")
        
        # Verify INR budget spent amount (should only include INR transactions)
        self.assertAlmostEqual(inr_budget_updated["spent_amount"], inr_expense["amount"], places=2, 
                             msg="INR budget spent amount incorrect")
        self.assertAlmostEqual(inr_budget_updated["percentage_used"], 50.0, places=2, 
                             msg="INR budget percentage used incorrect")
        
        print("Multi-currency budgets are correctly tracked with currency-specific expenses")

    def test_20_enhanced_analytics_financial_insights(self):
        """Test financial insights analytics endpoint"""
        print("\n=== Testing Enhanced Analytics: Financial Insights ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        
        # Test with default days parameter
        response = requests.get(
            f"{BACKEND_URL}/analytics/financial-insights",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get financial insights failed: {response.text}")
        insights = response.json()
        
        # Verify insights structure
        self.assertIn("total_income", insights, "total_income field missing")
        self.assertIn("total_expense", insights, "total_expense field missing")
        self.assertIn("net_amount", insights, "net_amount field missing")
        self.assertIn("top_spending_categories", insights, "top_spending_categories field missing")
        self.assertIn("spending_trend", insights, "spending_trend field missing")
        self.assertIn("average_daily_expense", insights, "average_daily_expense field missing")
        self.assertIn("highest_expense_day", insights, "highest_expense_day field missing")
        self.assertIn("savings_rate", insights, "savings_rate field missing")
        
        # Verify currency-specific totals
        self.assertIn("INR", insights["total_income"], "INR income missing")
        self.assertIn("USD", insights["total_income"], "USD income missing")
        self.assertIn("INR", insights["total_expense"], "INR expense missing")
        self.assertIn("USD", insights["total_expense"], "USD expense missing")
        self.assertIn("INR", insights["net_amount"], "INR net amount missing")
        self.assertIn("USD", insights["net_amount"], "USD net amount missing")
        
        # Verify top spending categories
        self.assertIsInstance(insights["top_spending_categories"], list, "top_spending_categories should be a list")
        if insights["top_spending_categories"]:
            category = insights["top_spending_categories"][0]
            self.assertIn("category", category, "category field missing in top spending category")
            self.assertIn("amount", category, "amount field missing in top spending category")
            self.assertIn("currency", category, "currency field missing in top spending category")
        
        # Verify spending trend
        self.assertIn(insights["spending_trend"], ["increasing", "decreasing", "stable"], 
                     f"Invalid spending trend: {insights['spending_trend']}")
        
        # Verify average daily expense
        self.assertIn("INR", insights["average_daily_expense"], "INR average daily expense missing")
        self.assertIn("USD", insights["average_daily_expense"], "USD average daily expense missing")
        
        # Verify savings rate is a percentage
        self.assertGreaterEqual(insights["savings_rate"], 0, "Savings rate should be non-negative")
        self.assertLessEqual(insights["savings_rate"], 100, "Savings rate should be at most 100%")
        
        print(f"Successfully retrieved financial insights with spending trend: {insights['spending_trend']}")
        print(f"Savings rate: {insights['savings_rate']}%")
        print(f"Total income: ₹{insights['total_income']['INR']} / ${insights['total_income']['USD']}")
        print(f"Total expense: ₹{insights['total_expense']['INR']} / ${insights['total_expense']['USD']}")
        
        # Test with custom days parameter
        custom_days = 7
        response = requests.get(
            f"{BACKEND_URL}/analytics/financial-insights?days={custom_days}",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get financial insights with custom days failed: {response.text}")
        custom_insights = response.json()
        
        # Basic verification for custom days
        self.assertIn("total_income", custom_insights, "total_income field missing in custom days response")
        print(f"Successfully retrieved financial insights for {custom_days} days")

    def test_21_enhanced_analytics_category_breakdown(self):
        """Test category breakdown analytics endpoint"""
        print("\n=== Testing Enhanced Analytics: Category Breakdown ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        
        response = requests.get(
            f"{BACKEND_URL}/analytics/category-breakdown",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get category breakdown failed: {response.text}")
        breakdown = response.json()
        
        # Verify breakdown is a list
        self.assertIsInstance(breakdown, list, "Category breakdown should be a list")
        
        # Verify breakdown structure if we have data
        if breakdown:
            for category_data in breakdown:
                self.assertIn("category", category_data, "category field missing")
                self.assertIn("type", category_data, "type field missing")
                self.assertIn("total_amount", category_data, "total_amount field missing")
                self.assertIn("currency", category_data, "currency field missing")
                self.assertIn("percentage", category_data, "percentage field missing")
                self.assertIn("transactions_count", category_data, "transactions_count field missing")
                
                # Verify percentage is valid
                self.assertGreaterEqual(category_data["percentage"], 0, "Percentage should be non-negative")
                self.assertLessEqual(category_data["percentage"], 100, "Percentage should be at most 100%")
                
                # Verify currency is valid
                self.assertIn(category_data["currency"], ["INR", "USD"], f"Invalid currency: {category_data['currency']}")
                
                print(f"{category_data['category']} ({category_data['type']}): " +
                     f"{'₹' if category_data['currency'] == 'INR' else '$'}{category_data['total_amount']} " +
                     f"({category_data['percentage']}%, {category_data['transactions_count']} transactions)")
        
        print(f"Successfully retrieved category breakdown with {len(breakdown)} categories")

    def test_22_enhanced_analytics_spending_trends(self):
        """Test spending trends analytics endpoint with different periods"""
        print("\n=== Testing Enhanced Analytics: Spending Trends ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        
        # Test daily period
        response = requests.get(
            f"{BACKEND_URL}/analytics/spending-trends?period=daily&days=30",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get daily spending trends failed: {response.text}")
        daily_trends = response.json()
        
        # Verify trends structure
        self.assertEqual(daily_trends["period"], "daily", "Period should be daily")
        self.assertIsInstance(daily_trends["data"], list, "Trends data should be a list")
        
        # Verify data structure if we have data
        if daily_trends["data"]:
            for day_data in daily_trends["data"]:
                self.assertIn("date", day_data, "date field missing")
                self.assertIn("income", day_data, "income field missing")
                self.assertIn("expense", day_data, "expense field missing")
                self.assertIn("net", day_data, "net field missing")
                self.assertIn("currency", day_data, "currency field missing")
                
                # Verify net calculation
                self.assertEqual(day_data["net"], day_data["income"] - day_data["expense"], 
                               "Net calculation incorrect")
            
            print(f"Successfully retrieved daily spending trends with {len(daily_trends['data'])} days")
        
        # Test weekly period
        response = requests.get(
            f"{BACKEND_URL}/analytics/spending-trends?period=weekly&days=60",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get weekly spending trends failed: {response.text}")
        weekly_trends = response.json()
        
        # Verify trends structure
        self.assertEqual(weekly_trends["period"], "weekly", "Period should be weekly")
        self.assertIsInstance(weekly_trends["data"], list, "Trends data should be a list")
        
        # Verify data structure if we have data
        if weekly_trends["data"]:
            for week_data in weekly_trends["data"]:
                self.assertIn("date", week_data, "date field missing")
                self.assertRegex(week_data["date"], r"^\d{4}-W\d{2}$", 
                               f"Weekly date format incorrect: {week_data['date']}")
            
            print(f"Successfully retrieved weekly spending trends with {len(weekly_trends['data'])} weeks")
        
        # Test monthly period
        response = requests.get(
            f"{BACKEND_URL}/analytics/spending-trends?period=monthly&days=90",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get monthly spending trends failed: {response.text}")
        monthly_trends = response.json()
        
        # Verify trends structure
        self.assertEqual(monthly_trends["period"], "monthly", "Period should be monthly")
        self.assertIsInstance(monthly_trends["data"], list, "Trends data should be a list")
        
        # Verify data structure if we have data
        if monthly_trends["data"]:
            for month_data in monthly_trends["data"]:
                self.assertIn("date", month_data, "date field missing")
                self.assertRegex(month_data["date"], r"^\d{4}-\d{2}$", 
                               f"Monthly date format incorrect: {month_data['date']}")
            
            print(f"Successfully retrieved monthly spending trends with {len(monthly_trends['data'])} months")
        
        # Test invalid period (should default to daily)
        response = requests.get(
            f"{BACKEND_URL}/analytics/spending-trends?period=invalid&days=30",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get spending trends with invalid period failed: {response.text}")
        invalid_period_trends = response.json()
        
        # Should default to monthly
        self.assertEqual(invalid_period_trends["period"], "monthly", "Invalid period should default to monthly")
        print("Invalid period correctly handled")

    def test_23_enhanced_analytics_budget_progress(self):
        """Test budget progress analytics endpoint"""
        print("\n=== Testing Enhanced Analytics: Budget Progress ===")
        
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        # Test with current month
        response = requests.get(
            f"{BACKEND_URL}/analytics/budget-progress?month={current_month}",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get budget progress failed: {response.text}")
        progress = response.json()
        
        # Verify progress is a list
        self.assertIsInstance(progress, list, "Budget progress should be a list")
        
        # Verify progress structure if we have data
        if progress:
            for budget_progress in progress:
                self.assertIn("category", budget_progress, "category field missing")
                self.assertIn("budget_amount", budget_progress, "budget_amount field missing")
                self.assertIn("spent_amount", budget_progress, "spent_amount field missing")
                self.assertIn("remaining_amount", budget_progress, "remaining_amount field missing")
                self.assertIn("percentage_used", budget_progress, "percentage_used field missing")
                self.assertIn("currency", budget_progress, "currency field missing")
                self.assertIn("status", budget_progress, "status field missing")
                
                # Verify calculations
                self.assertEqual(budget_progress["remaining_amount"], 
                               budget_progress["budget_amount"] - budget_progress["spent_amount"],
                               "remaining_amount calculation incorrect")
                
                # Verify status is valid
                self.assertIn(budget_progress["status"], ["over_budget", "on_track", "warning"], 
                             f"Invalid status: {budget_progress['status']}")
                
                # Verify status logic
                if budget_progress["percentage_used"] > 100:
                    self.assertEqual(budget_progress["status"], "over_budget", "Status should be over_budget")
                elif budget_progress["percentage_used"] < 80:
                    self.assertEqual(budget_progress["status"], "on_track", "Status should be on_track")
                else:
                    self.assertEqual(budget_progress["status"], "warning", "Status should be warning")
                
                print(f"{budget_progress['category']} budget: " +
                     f"{'₹' if budget_progress['currency'] == 'INR' else '$'}{budget_progress['spent_amount']} of " +
                     f"{'₹' if budget_progress['currency'] == 'INR' else '$'}{budget_progress['budget_amount']} " +
                     f"({budget_progress['percentage_used']}%, status: {budget_progress['status']})")
        
        print(f"Successfully retrieved budget progress for {current_month} with {len(progress)} budgets")
        
        # Test with default month (should be current month)
        response = requests.get(
            f"{BACKEND_URL}/analytics/budget-progress",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, f"Get budget progress with default month failed: {response.text}")
        default_progress = response.json()
        
        # Basic verification for default month
        self.assertIsInstance(default_progress, list, "Budget progress with default month should be a list")
        print(f"Successfully retrieved budget progress with default month")

if __name__ == "__main__":
    unittest.main(verbosity=2)