import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';
import axios from 'axios';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, LineChart, Line, ResponsiveContainer } from 'recharts';
import { Search, Filter, Plus, TrendingUp, TrendingDown, Calendar, Tag, Target, Zap } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';
import Fuse from 'fuse.js';
import { format, startOfMonth, endOfMonth, isWithinInterval } from 'date-fns';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetchUserProfile();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUserProfile = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user profile:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, {
        username,
        password
      });
      const { access_token } = response.data;
      setToken(access_token);
      localStorage.setItem('token', access_token);
      toast.success('Welcome back!');
      return true;
    } catch (error) {
      console.error('Login error:', error);
      toast.error('Invalid credentials');
      return false;
    }
  };

  const register = async (email, username, password) => {
    try {
      const response = await axios.post(`${API}/auth/register`, {
        email,
        username,
        password
      });
      const { access_token } = response.data;
      setToken(access_token);
      localStorage.setItem('token', access_token);
      toast.success('Account created successfully!');
      return true;
    } catch (error) {
      console.error('Registration error:', error);
      toast.error('Registration failed');
      return false;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    toast.success('Logged out successfully');
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading,
      login,
      register,
      logout,
      isAuthenticated: !!token
    }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Enhanced Transaction Form Component
const TransactionForm = ({ onTransactionAdded }) => {
  const [formData, setFormData] = useState({
    type: 'expense',
    category: 'food',
    amount: '',
    description: '',
    date: new Date().toISOString().split('T')[0],
    tags: '',
    is_recurring: false,
    recurrence_type: 'none'
  });
  const [loading, setLoading] = useState(false);
  const { token } = useAuth();

  const categories = {
    income: [
      { value: 'salary', label: '💰 Salary', emoji: '💰' },
      { value: 'freelance', label: '🖥️ Freelance', emoji: '🖥️' },
      { value: 'business', label: '🏢 Business', emoji: '🏢' },
      { value: 'investment', label: '📈 Investment', emoji: '📈' },
      { value: 'other_income', label: '💵 Other Income', emoji: '💵' }
    ],
    expense: [
      { value: 'food', label: '🍽️ Food & Dining', emoji: '🍽️' },
      { value: 'transportation', label: '🚗 Transportation', emoji: '🚗' },
      { value: 'housing', label: '🏠 Housing', emoji: '🏠' },
      { value: 'utilities', label: '💡 Utilities', emoji: '💡' },
      { value: 'entertainment', label: '🎬 Entertainment', emoji: '🎬' },
      { value: 'healthcare', label: '🏥 Healthcare', emoji: '🏥' },
      { value: 'education', label: '📚 Education', emoji: '📚' },
      { value: 'shopping', label: '🛍️ Shopping', emoji: '🛍️' },
      { value: 'other_expense', label: '💸 Other Expense', emoji: '💸' }
    ]
  };

  const recurrenceOptions = [
    { value: 'none', label: 'One-time' },
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'monthly', label: 'Monthly' },
    { value: 'yearly', label: 'Yearly' }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const tagsArray = formData.tags ? formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
      
      await axios.post(`${API}/transactions`, {
        ...formData,
        amount: parseFloat(formData.amount),
        date: new Date(formData.date).toISOString(),
        tags: tagsArray
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setFormData({
        type: 'expense',
        category: 'food',
        amount: '',
        description: '',
        date: new Date().toISOString().split('T')[0],
        tags: '',
        is_recurring: false,
        recurrence_type: 'none'
      });

      toast.success('Transaction added successfully!');
      onTransactionAdded();
    } catch (error) {
      console.error('Error adding transaction:', error);
      toast.error('Failed to add transaction');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
      ...(name === 'type' && { category: categories[value][0].value })
    }));
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
      <div className="flex items-center mb-4">
        <Plus className="w-6 h-6 text-purple-600 mr-2" />
        <h3 className="text-xl font-bold text-gray-800">Add New Transaction</h3>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Type
            </label>
            <select
              name="type"
              value={formData.type}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="income">💰 Income</option>
              <option value="expense">💸 Expense</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              name="category"
              value={formData.category}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              {categories[formData.type].map(cat => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Amount (₹)
            </label>
            <input
              type="number"
              name="amount"
              value={formData.amount}
              onChange={handleChange}
              required
              step="0.01"
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="0.00"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date
            </label>
            <input
              type="date"
              name="date"
              value={formData.date}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <input
            type="text"
            name="description"
            value={formData.description}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            placeholder="Enter transaction description"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Tag className="w-4 h-4 inline mr-1" />
            Tags (comma-separated)
          </label>
          <input
            type="text"
            name="tags"
            value={formData.tags}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            placeholder="e.g., urgent, monthly, bills"
          />
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              name="is_recurring"
              checked={formData.is_recurring}
              onChange={handleChange}
              className="mr-2"
              id="recurring"
            />
            <label htmlFor="recurring" className="text-sm font-medium text-gray-700 flex items-center">
              <Zap className="w-4 h-4 mr-1" />
              Recurring Transaction
            </label>
          </div>

          {formData.is_recurring && (
            <div>
              <select
                name="recurrence_type"
                value={formData.recurrence_type}
                onChange={handleChange}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                {recurrenceOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 px-4 rounded-lg font-medium hover:from-purple-600 hover:to-pink-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-all disabled:opacity-50"
        >
          {loading ? 'Adding...' : 'Add Transaction'}
        </button>
      </form>
    </div>
  );
};

// Budget Management Component
const BudgetManager = ({ currentMonth }) => {
  const [budgets, setBudgets] = useState([]);
  const [newBudget, setNewBudget] = useState({
    category: 'food',
    budget_amount: '',
    month: currentMonth
  });
  const [loading, setLoading] = useState(false);
  const { token } = useAuth();

  const expenseCategories = [
    { value: 'food', label: '🍽️ Food & Dining' },
    { value: 'transportation', label: '🚗 Transportation' },
    { value: 'housing', label: '🏠 Housing' },
    { value: 'utilities', label: '💡 Utilities' },
    { value: 'entertainment', label: '🎬 Entertainment' },
    { value: 'healthcare', label: '🏥 Healthcare' },
    { value: 'education', label: '📚 Education' },
    { value: 'shopping', label: '🛍️ Shopping' },
    { value: 'other_expense', label: '💸 Other Expense' }
  ];

  useEffect(() => {
    fetchBudgets();
  }, [currentMonth]);

  const fetchBudgets = async () => {
    try {
      const response = await axios.get(`${API}/budgets?month=${currentMonth}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBudgets(response.data);
    } catch (error) {
      console.error('Error fetching budgets:', error);
    }
  };

  const handleCreateBudget = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/budgets`, {
        ...newBudget,
        budget_amount: parseFloat(newBudget.budget_amount)
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setNewBudget({
        category: 'food',
        budget_amount: '',
        month: currentMonth
      });

      toast.success('Budget set successfully!');
      fetchBudgets();
    } catch (error) {
      console.error('Error creating budget:', error);
      toast.error('Failed to set budget');
    } finally {
      setLoading(false);
    }
  };

  const getProgressColor = (percentage) => {
    if (percentage <= 50) return 'bg-green-500';
    if (percentage <= 80) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getProgressBgColor = (percentage) => {
    if (percentage <= 50) return 'bg-green-100';
    if (percentage <= 80) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(amount);
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
      <div className="flex items-center mb-4">
        <Target className="w-6 h-6 text-purple-600 mr-2" />
        <h3 className="text-xl font-bold text-gray-800">Budget Management</h3>
      </div>

      {/* Create Budget Form */}
      <form onSubmit={handleCreateBudget} className="mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              value={newBudget.category}
              onChange={(e) => setNewBudget(prev => ({ ...prev, category: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              {expenseCategories.map(cat => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Budget Amount (₹)
            </label>
            <input
              type="number"
              value={newBudget.budget_amount}
              onChange={(e) => setNewBudget(prev => ({ ...prev, budget_amount: e.target.value }))}
              required
              step="0.01"
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="0.00"
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-2 px-4 rounded-lg font-medium hover:from-purple-600 hover:to-pink-600 transition-all disabled:opacity-50"
            >
              {loading ? 'Setting...' : 'Set Budget'}
            </button>
          </div>
        </div>
      </form>

      {/* Budget Progress Bars */}
      <div className="space-y-4">
        {budgets.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No budgets set for this month. Create your first budget above!</p>
        ) : (
          budgets.map((budget) => {
            const category = expenseCategories.find(cat => cat.value === budget.category);
            return (
              <div key={budget.id} className={`p-4 rounded-lg border ${getProgressBgColor(budget.percentage_used)}`}>
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-semibold text-gray-800">
                    {category?.label || budget.category}
                  </h4>
                  <span className="text-sm text-gray-600">
                    {budget.percentage_used.toFixed(1)}% used
                  </span>
                </div>
                
                <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                  <div
                    className={`h-3 rounded-full transition-all duration-300 ${getProgressColor(budget.percentage_used)}`}
                    style={{ width: `${Math.min(budget.percentage_used, 100)}%` }}
                  ></div>
                </div>
                
                <div className="flex justify-between text-sm">
                  <span>Spent: {formatCurrency(budget.spent_amount)}</span>
                  <span>Budget: {formatCurrency(budget.budget_amount)}</span>
                </div>
                
                {budget.remaining_amount < 0 && (
                  <div className="mt-2 text-red-600 text-sm font-medium">
                    ⚠️ Over budget by {formatCurrency(Math.abs(budget.remaining_amount))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

// Enhanced Search and Filter Component
const SearchAndFilter = ({ onFiltersChange }) => {
  const [filters, setFilters] = useState({
    query: '',
    category: '',
    type: '',
    start_date: '',
    end_date: '',
    min_amount: '',
    max_amount: '',
    tags: ''
  });
  const [showFilters, setShowFilters] = useState(false);

  const categories = [
    { value: 'salary', label: '💰 Salary' },
    { value: 'freelance', label: '🖥️ Freelance' },
    { value: 'business', label: '🏢 Business' },
    { value: 'investment', label: '📈 Investment' },
    { value: 'other_income', label: '💵 Other Income' },
    { value: 'food', label: '🍽️ Food & Dining' },
    { value: 'transportation', label: '🚗 Transportation' },
    { value: 'housing', label: '🏠 Housing' },
    { value: 'utilities', label: '💡 Utilities' },
    { value: 'entertainment', label: '🎬 Entertainment' },
    { value: 'healthcare', label: '🏥 Healthcare' },
    { value: 'education', label: '📚 Education' },
    { value: 'shopping', label: '🛍️ Shopping' },
    { value: 'other_expense', label: '💸 Other Expense' }
  ];

  const handleFilterChange = (name, value) => {
    const newFilters = { ...filters, [name]: value };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const clearFilters = () => {
    const clearedFilters = {
      query: '',
      category: '',
      type: '',
      start_date: '',
      end_date: '',
      min_amount: '',
      max_amount: '',
      tags: ''
    };
    setFilters(clearedFilters);
    onFiltersChange(clearedFilters);
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Search className="w-6 h-6 text-purple-600 mr-2" />
          <h3 className="text-xl font-bold text-gray-800">Search & Filter</h3>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center px-3 py-2 text-purple-600 hover:bg-purple-50 rounded-lg"
        >
          <Filter className="w-4 h-4 mr-1" />
          {showFilters ? 'Hide Filters' : 'Show Filters'}
        </button>
      </div>

      {/* Search Bar */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search transactions..."
          value={filters.query}
          onChange={(e) => handleFilterChange('query', e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
      </div>

      {/* Advanced Filters */}
      {showFilters && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Type
              </label>
              <select
                value={filters.type}
                onChange={(e) => handleFilterChange('type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="">All Types</option>
                <option value="income">💰 Income</option>
                <option value="expense">💸 Expense</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category
              </label>
              <select
                value={filters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="">All Categories</option>
                {categories.map(cat => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tags
              </label>
              <input
                type="text"
                placeholder="Enter tags..."
                value={filters.tags}
                onChange={(e) => handleFilterChange('tags', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Start Date
              </label>
              <input
                type="date"
                value={filters.start_date}
                onChange={(e) => handleFilterChange('start_date', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                End Date
              </label>
              <input
                type="date"
                value={filters.end_date}
                onChange={(e) => handleFilterChange('end_date', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Amount Range (₹)
              </label>
              <div className="flex space-x-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={filters.min_amount}
                  onChange={(e) => handleFilterChange('min_amount', e.target.value)}
                  className="w-1/2 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <input
                  type="number"
                  placeholder="Max"
                  value={filters.max_amount}
                  onChange={(e) => handleFilterChange('max_amount', e.target.value)}
                  className="w-1/2 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={clearFilters}
              className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Clear All Filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Charts Component
const ChartsSection = ({ transactions, monthlySummary }) => {
  const [chartType, setChartType] = useState('category');
  
  // Prepare data for different chart types
  const prepareCategoryData = () => {
    const categoryData = {};
    transactions.forEach(transaction => {
      if (!categoryData[transaction.category]) {
        categoryData[transaction.category] = { income: 0, expense: 0 };
      }
      categoryData[transaction.category][transaction.type] += transaction.amount;
    });

    return Object.entries(categoryData).map(([category, data]) => ({
      category: category.replace('_', ' ').toUpperCase(),
      income: data.income,
      expense: data.expense,
      net: data.income - data.expense
    }));
  };

  const prepareTrendData = () => {
    const last30Days = Array.from({ length: 30 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - i);
      return date.toISOString().split('T')[0];
    }).reverse();

    return last30Days.map(date => {
      const dayTransactions = transactions.filter(t => 
        t.date.split('T')[0] === date
      );
      
      const income = dayTransactions
        .filter(t => t.type === 'income')
        .reduce((sum, t) => sum + t.amount, 0);
      
      const expense = dayTransactions
        .filter(t => t.type === 'expense')
        .reduce((sum, t) => sum + t.amount, 0);

      return {
        date: format(new Date(date), 'MMM dd'),
        income,
        expense,
        net: income - expense
      };
    });
  };

  const preparePieData = () => {
    const expensesByCategory = {};
    transactions
      .filter(t => t.type === 'expense')
      .forEach(transaction => {
        expensesByCategory[transaction.category] = 
          (expensesByCategory[transaction.category] || 0) + transaction.amount;
      });

    return Object.entries(expensesByCategory).map(([category, amount]) => ({
      name: category.replace('_', ' ').toUpperCase(),
      value: amount
    }));
  };

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#ff00ff', '#00ffff', '#ff0000', '#0000ff'];

  const formatCurrency = (value) => `₹${value.toLocaleString()}`;

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <TrendingUp className="w-6 h-6 text-purple-600 mr-2" />
          <h3 className="text-xl font-bold text-gray-800">Analytics & Charts</h3>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setChartType('category')}
            className={`px-4 py-2 rounded-lg ${chartType === 'category' ? 'bg-purple-500 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            Category
          </button>
          <button
            onClick={() => setChartType('trend')}
            className={`px-4 py-2 rounded-lg ${chartType === 'trend' ? 'bg-purple-500 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            Trends
          </button>
          <button
            onClick={() => setChartType('pie')}
            className={`px-4 py-2 rounded-lg ${chartType === 'pie' ? 'bg-purple-500 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            Pie Chart
          </button>
        </div>
      </div>

      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'category' && (
            <BarChart data={prepareCategoryData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis tickFormatter={formatCurrency} />
              <Tooltip formatter={(value) => formatCurrency(value)} />
              <Legend />
              <Bar dataKey="income" fill="#10B981" name="Income" />
              <Bar dataKey="expense" fill="#EF4444" name="Expense" />
            </BarChart>
          )}
          
          {chartType === 'trend' && (
            <LineChart data={prepareTrendData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis tickFormatter={formatCurrency} />
              <Tooltip formatter={(value) => formatCurrency(value)} />
              <Legend />
              <Line type="monotone" dataKey="income" stroke="#10B981" strokeWidth={2} name="Income" />
              <Line type="monotone" dataKey="expense" stroke="#EF4444" strokeWidth={2} name="Expense" />
              <Line type="monotone" dataKey="net" stroke="#8B5CF6" strokeWidth={2} name="Net" />
            </LineChart>
          )}
          
          {chartType === 'pie' && (
            <PieChart>
              <Pie
                data={preparePieData()}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={120}
                fill="#8884d8"
                dataKey="value"
              >
                {preparePieData().map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => formatCurrency(value)} />
            </PieChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// Enhanced Transaction List Component
const TransactionList = ({ transactions, onTransactionDeleted }) => {
  const { token } = useAuth();

  const handleDelete = async (transactionId) => {
    if (window.confirm('Are you sure you want to delete this transaction?')) {
      try {
        await axios.delete(`${API}/transactions/${transactionId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Transaction deleted successfully');
        onTransactionDeleted();
      } catch (error) {
        console.error('Error deleting transaction:', error);
        toast.error('Failed to delete transaction');
      }
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getCategoryEmoji = (category) => {
    const emojiMap = {
      salary: '💰', freelance: '🖥️', business: '🏢', investment: '📈', other_income: '💵',
      food: '🍽️', transportation: '🚗', housing: '🏠', utilities: '💡',
      entertainment: '🎬', healthcare: '🏥', education: '📚', shopping: '🛍️', other_expense: '💸'
    };
    return emojiMap[category] || '💰';
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <h3 className="text-xl font-bold text-gray-800 mb-4">Transaction History</h3>
      
      {transactions.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No transactions found. Try adjusting your filters or add your first transaction!</p>
      ) : (
        <div className="space-y-3">
          {transactions.map((transaction) => (
            <div
              key={transaction.id}
              className={`p-4 rounded-lg border-l-4 transition-all hover:shadow-md ${
                transaction.type === 'income' 
                  ? 'border-green-400 bg-green-50 hover:bg-green-100' 
                  : 'border-red-400 bg-red-50 hover:bg-red-100'
              }`}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <span className="text-2xl mr-2">{getCategoryEmoji(transaction.category)}</span>
                    <h4 className="font-semibold text-gray-800">
                      {transaction.description}
                    </h4>
                    {transaction.is_recurring && (
                      <span className="ml-2 px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full flex items-center">
                        <Zap className="w-3 h-3 mr-1" />
                        {transaction.recurrence_type}
                      </span>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-600 capitalize mb-1">
                    {transaction.category.replace('_', ' ')} • {formatDate(transaction.date)}
                  </p>
                  
                  {transaction.tags && transaction.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {transaction.tags.map((tag, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                
                <div className="text-right">
                  <p className={`font-bold text-lg ${
                    transaction.type === 'income' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {transaction.type === 'income' ? '+' : '-'}{formatCurrency(transaction.amount)}
                  </p>
                  <button
                    onClick={() => handleDelete(transaction.id)}
                    className="text-red-500 hover:text-red-700 text-sm mt-1 hover:underline"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Auth Form Component (same as before but with toast notifications)
const AuthForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    let success;
    if (isLogin) {
      success = await login(formData.username, formData.password);
    } else {
      success = await register(formData.email, formData.username, formData.password);
    }

    if (!success) {
      setError(isLogin ? 'Invalid username or password' : 'Registration failed');
    }
    setLoading(false);
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-pink-50 to-blue-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-800 mb-2">
            {isLogin ? 'Welcome Back!' : 'Join Us Today!'}
          </h2>
          <p className="text-gray-600">
            {isLogin ? 'Sign in to your budget planner' : 'Create your budget planner account'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required={!isLogin}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                placeholder="Enter your email"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Username
            </label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              placeholder="Enter your username"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              placeholder="Enter your password"
            />
          </div>

          {error && (
            <div className="text-red-500 text-sm text-center bg-red-50 p-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 px-4 rounded-lg font-medium hover:from-purple-600 hover:to-pink-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-all disabled:opacity-50"
          >
            {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-purple-600 hover:text-purple-700 font-medium"
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
};

// Enhanced Dashboard Component
const Dashboard = () => {
  const [transactions, setTransactions] = useState([]);
  const [filteredTransactions, setFilteredTransactions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentMonth, setCurrentMonth] = useState(format(new Date(), 'yyyy-MM'));
  const { user, logout, token } = useAuth();

  const fetchTransactions = async () => {
    try {
      const response = await axios.get(`${API}/transactions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTransactions(response.data);
      setFilteredTransactions(response.data);
    } catch (error) {
      console.error('Error fetching transactions:', error);
      toast.error('Failed to fetch transactions');
    }
  };

  const fetchMonthlySummary = async () => {
    try {
      const response = await axios.get(`${API}/transactions/summary/monthly`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSummary(response.data[0] || null);
    } catch (error) {
      console.error('Error fetching summary:', error);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      await Promise.all([fetchTransactions(), fetchMonthlySummary()]);
      setLoading(false);
    };
    fetchData();
  }, [token]);

  const handleTransactionAdded = () => {
    fetchTransactions();
    fetchMonthlySummary();
  };

  const handleFiltersChange = async (filters) => {
    if (!filters.query && !filters.category && !filters.type && !filters.start_date && 
        !filters.end_date && !filters.min_amount && !filters.max_amount && !filters.tags) {
      setFilteredTransactions(transactions);
      return;
    }

    try {
      const searchFilters = {
        ...filters,
        start_date: filters.start_date ? new Date(filters.start_date).toISOString() : null,
        end_date: filters.end_date ? new Date(filters.end_date).toISOString() : null,
        min_amount: filters.min_amount ? parseFloat(filters.min_amount) : null,
        max_amount: filters.max_amount ? parseFloat(filters.max_amount) : null,
        tags: filters.tags ? filters.tags.split(',').map(tag => tag.trim()).filter(tag => tag) : []
      };

      // Remove null/empty values
      Object.keys(searchFilters).forEach(key => {
        if (searchFilters[key] === null || searchFilters[key] === '' || 
            (Array.isArray(searchFilters[key]) && searchFilters[key].length === 0)) {
          delete searchFilters[key];
        }
      });

      const response = await axios.post(`${API}/transactions/search`, searchFilters, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setFilteredTransactions(response.data);
    } catch (error) {
      console.error('Error searching transactions:', error);
      toast.error('Search failed');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-100 via-pink-50 to-blue-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-500 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading your budget...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-pink-50 to-blue-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">
              Welcome back, {user?.username}! 🎯
            </h1>
            <p className="text-gray-600">Your intelligent budget companion</p>
          </div>
          <div className="flex items-center space-x-4">
            <select
              value={currentMonth}
              onChange={(e) => setCurrentMonth(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              {Array.from({ length: 12 }, (_, i) => {
                const date = new Date();
                date.setMonth(date.getMonth() - i);
                const monthStr = format(date, 'yyyy-MM');
                return (
                  <option key={monthStr} value={monthStr}>
                    {format(date, 'MMMM yyyy')}
                  </option>
                );
              })}
            </select>
            <button
              onClick={logout}
              className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              Logout
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center">
                <TrendingUp className="w-8 h-8 text-green-600 mr-3" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-700 mb-1">This Month's Income</h3>
                  <p className="text-3xl font-bold text-green-600">
                    {formatCurrency(summary.total_income)}
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center">
                <TrendingDown className="w-8 h-8 text-red-600 mr-3" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-700 mb-1">This Month's Expenses</h3>
                  <p className="text-3xl font-bold text-red-600">
                    {formatCurrency(summary.total_expense)}
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center">
                <Target className="w-8 h-8 text-purple-600 mr-3" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-700 mb-1">Net Amount</h3>
                  <p className={`text-3xl font-bold ${
                    summary.net_amount >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrency(summary.net_amount)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Budget Management */}
        <BudgetManager currentMonth={currentMonth} />

        {/* Transaction Form */}
        <TransactionForm onTransactionAdded={handleTransactionAdded} />

        {/* Charts Section */}
        <ChartsSection transactions={filteredTransactions} monthlySummary={summary} />

        {/* Search and Filter */}
        <SearchAndFilter onFiltersChange={handleFiltersChange} />

        {/* Transaction List */}
        <TransactionList 
          transactions={filteredTransactions} 
          onTransactionDeleted={handleTransactionAdded}
        />
      </div>
      <Toaster position="top-right" />
    </div>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <AppContent />
      <Toaster position="top-right" />
    </AuthProvider>
  );
};

const AppContent = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-100 via-pink-50 to-blue-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return isAuthenticated ? <Dashboard /> : <AuthForm />;
};

export default App;