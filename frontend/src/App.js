import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Area, AreaChart } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, PieChartIcon, BarChart3, Calendar, Target, AlertTriangle } from 'lucide-react';

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
      return true;
    } catch (error) {
      console.error('Login error:', error);
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
      return true;
    } catch (error) {
      console.error('Registration error:', error);
      return false;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
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

// Currency Utils
const CURRENCIES = {
  INR: { symbol: '₹', name: 'Indian Rupee' },
  USD: { symbol: '$', name: 'US Dollar' }
};

const formatCurrency = (amount, currency = 'INR') => {
  const formatter = new Intl.NumberFormat(currency === 'INR' ? 'en-IN' : 'en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2
  });
  return formatter.format(amount);
};

// Components
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

const TransactionForm = ({ onTransactionAdded }) => {
  const [formData, setFormData] = useState({
    type: 'expense',
    category: 'food',
    amount: '',
    currency: 'INR',
    description: '',
    date: new Date().toISOString().split('T')[0],
    tags: [],
    is_recurring: false,
    recurrence_type: 'none'
  });
  const [tagInput, setTagInput] = useState('');
  const [loading, setLoading] = useState(false);
  const { token } = useAuth();

  const categories = {
    income: [
      { value: 'salary', label: '💼 Salary', emoji: '💼' },
      { value: 'freelance', label: '💻 Freelance', emoji: '💻' },
      { value: 'business', label: '🏢 Business', emoji: '🏢' },
      { value: 'investment', label: '📈 Investment', emoji: '📈' },
      { value: 'other_income', label: '💰 Other Income', emoji: '💰' }
    ],
    expense: [
      { value: 'food', label: '🍽️ Food & Dining', emoji: '🍽️' },
      { value: 'transportation', label: '🚗 Transportation', emoji: '🚗' },
      { value: 'housing', label: '🏠 Housing', emoji: '🏠' },
      { value: 'utilities', label: '⚡ Utilities', emoji: '⚡' },
      { value: 'entertainment', label: '🎬 Entertainment', emoji: '🎬' },
      { value: 'healthcare', label: '🏥 Healthcare', emoji: '🏥' },
      { value: 'education', label: '📚 Education', emoji: '📚' },
      { value: 'shopping', label: '🛍️ Shopping', emoji: '🛍️' },
      { value: 'other_expense', label: '📦 Other Expense', emoji: '📦' }
    ]
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        ...formData,
        amount: parseFloat(formData.amount),
        date: new Date(formData.date).toISOString(),
        tags: formData.tags
      };

      await axios.post(`${API}/transactions`, payload, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setFormData({
        type: 'expense',
        category: 'food',
        amount: '',
        currency: 'INR',
        description: '',
        date: new Date().toISOString().split('T')[0],
        tags: [],
        is_recurring: false,
        recurrence_type: 'none'
      });

      onTransactionAdded();
    } catch (error) {
      console.error('Error adding transaction:', error);
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

  const addTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()]
      }));
      setTagInput('');
    }
  };

  const removeTag = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const selectedCategory = categories[formData.type].find(cat => cat.value === formData.category);

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
      <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
        <DollarSign className="mr-2" size={24} />
        Add New Transaction
      </h3>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
            <select
              name="type"
              value={formData.type}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="income">📈 Income</option>
              <option value="expense">📉 Expense</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Amount</label>
            <div className="relative">
              <select
                name="currency"
                value={formData.currency}
                onChange={handleChange}
                className="absolute left-0 top-0 h-full px-3 border-r border-gray-300 bg-gray-50 rounded-l-lg text-sm"
              >
                <option value="INR">INR ₹</option>
                <option value="USD">USD $</option>
              </select>
              <input
                type="number"
                name="amount"
                value={formData.amount}
                onChange={handleChange}
                required
                step="0.01"
                min="0"
                className="w-full pl-20 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="0.00"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Date</label>
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
            Category {selectedCategory && `${selectedCategory.emoji}`}
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
          <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
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
          <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
              placeholder="Add a tag"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
            />
            <button
              type="button"
              onClick={addTag}
              className="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors text-sm"
            >
              Add
            </button>
          </div>
          {formData.tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {formData.tags.map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-purple-100 text-purple-800"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeTag(tag)}
                    className="ml-2 text-purple-600 hover:text-purple-800"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              name="is_recurring"
              checked={formData.is_recurring}
              onChange={handleChange}
              className="mr-2"
            />
            <label className="text-sm font-medium text-gray-700">Recurring Transaction</label>
          </div>

          {formData.is_recurring && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Recurrence</label>
              <select
                name="recurrence_type"
                value={formData.recurrence_type}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
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

const FinancialInsights = ({ insights, currencyRates }) => {
  if (!insights) return null;

  const getInsightIcon = (trend) => {
    switch (trend) {
      case 'increasing': return <TrendingUp className="text-red-500" size={20} />;
      case 'decreasing': return <TrendingDown className="text-green-500" size={20} />;
      default: return <Target className="text-blue-500" size={20} />;
    }
  };

  const getInsightMessage = (trend) => {
    switch (trend) {
      case 'increasing': return 'Your spending is trending upward. Consider reviewing your recent expenses.';
      case 'decreasing': return 'Great! Your spending is trending downward. Keep up the good work!';
      default: return 'Your spending pattern is stable. Maintaining consistency is good!';
    }
  };

  const getSavingsMessage = (rate) => {
    if (rate > 20) return 'Excellent! You\'re saving over 20% of your income.';
    if (rate > 10) return 'Good savings rate! Try to increase it gradually.';
    if (rate > 0) return 'You\'re saving money, but there\'s room for improvement.';
    return 'Warning: You\'re spending more than you earn. Review your expenses.';
  };

  const totalIncomeINR = insights.total_income.INR + (insights.total_income.USD * (currencyRates?.USD_to_INR || 83.5));
  const totalExpenseINR = insights.total_expense.INR + (insights.total_expense.USD * (currencyRates?.USD_to_INR || 83.5));

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
      <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
        <BarChart3 className="mr-2" size={24} />
        Financial Insights
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-green-800 mb-1">Total Income</h4>
          <p className="text-2xl font-bold text-green-700">{formatCurrency(totalIncomeINR, 'INR')}</p>
          <p className="text-xs text-green-600 mt-1">
            {insights.total_income.USD > 0 && `+ ${formatCurrency(insights.total_income.USD, 'USD')}`}
          </p>
        </div>

        <div className="bg-gradient-to-r from-red-50 to-red-100 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-red-800 mb-1">Total Expenses</h4>
          <p className="text-2xl font-bold text-red-700">{formatCurrency(totalExpenseINR, 'INR')}</p>
          <p className="text-xs text-red-600 mt-1">
            {insights.total_expense.USD > 0 && `+ ${formatCurrency(insights.total_expense.USD, 'USD')}`}
          </p>
        </div>

        <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-blue-800 mb-1">Savings Rate</h4>
          <p className="text-2xl font-bold text-blue-700">{insights.savings_rate}%</p>
          <p className="text-xs text-blue-600 mt-1">
            {getSavingsMessage(insights.savings_rate).split('.')[0]}
          </p>
        </div>

        <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-purple-800 mb-1">Daily Avg Expense</h4>
          <p className="text-lg font-bold text-purple-700">
            {formatCurrency(insights.average_daily_expense.INR, 'INR')}
          </p>
          <p className="text-xs text-purple-600 mt-1">
            {insights.average_daily_expense.USD > 0 && `+ ${formatCurrency(insights.average_daily_expense.USD, 'USD')}`}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-800 mb-3 flex items-center">
            {getInsightIcon(insights.spending_trend)}
            <span className="ml-2">Spending Trend</span>
          </h4>
          <p className="text-sm text-gray-600">{getInsightMessage(insights.spending_trend)}</p>
          {insights.highest_expense_day && (
            <p className="text-xs text-gray-500 mt-2">
              Highest expense day: {new Date(insights.highest_expense_day).toLocaleDateString()}
            </p>
          )}
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-800 mb-3">Top Spending Categories</h4>
          <div className="space-y-2">
            {insights.top_spending_categories.slice(0, 3).map((cat, index) => (
              <div key={index} className="flex justify-between items-center">
                <span className="text-sm text-gray-600 capitalize">{cat.category.replace('_', ' ')}</span>
                <span className="text-sm font-medium">{formatCurrency(cat.amount, cat.currency)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const ChartsSection = ({ spendingTrends, categoryData, budgetProgress }) => {
  const [activeChart, setActiveChart] = useState('trends');

  // Prepare data for different charts
  const trendChartData = spendingTrends?.data?.map(item => ({
    date: item.date,
    income: item.income,
    expense: item.expense,
    net: item.net
  })) || [];

  // Combine category data by currency for pie chart
  const pieChartData = categoryData?.reduce((acc, item) => {
    if (item.type === 'expense') {
      const existing = acc.find(a => a.category === item.category);
      if (existing) {
        existing.value += item.total_amount;
      } else {
        acc.push({
          name: item.category.replace('_', ' '),
          category: item.category,
          value: item.total_amount,
          currency: item.currency
        });
      }
    }
    return acc;
  }, []) || [];

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0', '#ffb347'];

  const chartTabs = [
    { id: 'trends', label: 'Spending Trends', icon: <TrendingUp size={16} /> },
    { id: 'categories', label: 'Category Breakdown', icon: <PieChartIcon size={16} /> },
    { id: 'budget', label: 'Budget Progress', icon: <Target size={16} /> }
  ];

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
      <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
        <BarChart3 className="mr-2" size={24} />
        Interactive Analytics
      </h3>

      {/* Chart Tabs */}
      <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
        {chartTabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveChart(tab.id)}
            className={`flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-md transition-all ${
              activeChart === tab.id
                ? 'bg-white shadow-sm text-purple-600 font-medium'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            {tab.icon}
            <span className="text-sm">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Chart Content */}
      <div className="h-80">
        {activeChart === 'trends' && (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trendChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value, name) => [formatCurrency(value), name]} />
              <Legend />
              <Area
                type="monotone"
                dataKey="income"
                stackId="1"
                stroke="#82ca9d"
                fill="#82ca9d"
                fillOpacity={0.7}
                name="Income"
              />
              <Area
                type="monotone"
                dataKey="expense"
                stackId="2"
                stroke="#ff7c7c"
                fill="#ff7c7c"
                fillOpacity={0.7}
                name="Expense"
              />
              <Line
                type="monotone"
                dataKey="net"
                stroke="#8884d8"
                strokeWidth={3}
                name="Net Amount"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}

        {activeChart === 'categories' && (
          <div className="flex items-center justify-center h-full">
            {pieChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [formatCurrency(value), 'Amount']} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-gray-500">
                <PieChartIcon size={48} className="mx-auto mb-4 opacity-50" />
                <p>No expense data available for categories</p>
              </div>
            )}
          </div>
        )}

        {activeChart === 'budget' && (
          <div className="space-y-4 h-full overflow-y-auto">
            {budgetProgress && budgetProgress.length > 0 ? (
              budgetProgress.map((budget, index) => (
                <div key={index} className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-medium capitalize">
                      {budget.category.replace('_', ' ')} ({budget.currency})
                    </h4>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      budget.status === 'over_budget' ? 'bg-red-100 text-red-800' :
                      budget.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {budget.status === 'over_budget' ? 'Over Budget' :
                       budget.status === 'warning' ? 'Near Limit' : 'On Track'}
                    </span>
                  </div>
                  
                  <div className="mb-2">
                    <div className="flex justify-between text-sm text-gray-600 mb-1">
                      <span>Spent: {formatCurrency(budget.spent_amount, budget.currency)}</span>
                      <span>Budget: {formatCurrency(budget.budget_amount, budget.currency)}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          budget.percentage_used > 100 ? 'bg-red-500' :
                          budget.percentage_used > 80 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${Math.min(budget.percentage_used, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="text-sm text-gray-600">
                    {budget.percentage_used}% used • {formatCurrency(budget.remaining_amount, budget.currency)} remaining
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 py-8">
                <Target size={48} className="mx-auto mb-4 opacity-50" />
                <p>No budgets set yet</p>
                <p className="text-sm">Create a budget to track your spending</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [transactions, setTransactions] = useState([]);
  const [financialInsights, setFinancialInsights] = useState(null);
  const [spendingTrends, setSpendingTrends] = useState(null);
  const [categoryData, setCategoryData] = useState([]);
  const [budgetProgress, setBudgetProgress] = useState([]);
  const [currencyRates, setCurrencyRates] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user, logout, token } = useAuth();

  const fetchData = async () => {
    try {
      setLoading(true);
      const [
        transactionsRes,
        insightsRes,
        trendsRes,
        categoriesRes,
        budgetRes,
        ratesRes
      ] = await Promise.all([
        axios.get(`${API}/transactions`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/analytics/financial-insights`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/analytics/spending-trends?period=daily&days=30`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/analytics/category-breakdown`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/analytics/budget-progress`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/currency/rates`)
      ]);

      setTransactions(transactionsRes.data);
      setFinancialInsights(insightsRes.data);
      setSpendingTrends(trendsRes.data);
      setCategoryData(categoriesRes.data);
      setBudgetProgress(budgetRes.data);
      setCurrencyRates(ratesRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [token]);

  const handleTransactionAdded = () => {
    fetchData();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-100 via-pink-50 to-blue-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-500 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading your dashboard...</p>
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
              Welcome back, {user?.username}!
            </h1>
            <p className="text-gray-600">Your multi-currency budget planner with advanced analytics</p>
            {currencyRates && (
              <p className="text-sm text-gray-500 mt-1">
                Exchange Rate: 1 USD = ₹{currencyRates.USD_to_INR} • Last updated: {new Date().toLocaleDateString()}
              </p>
            )}
          </div>
          <button
            onClick={logout}
            className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            Logout
          </button>
        </div>

        {/* Transaction Form */}
        <TransactionForm onTransactionAdded={handleTransactionAdded} />

        {/* Financial Insights */}
        <FinancialInsights insights={financialInsights} currencyRates={currencyRates} />

        {/* Interactive Charts */}
        <ChartsSection 
          spendingTrends={spendingTrends}
          categoryData={categoryData}
          budgetProgress={budgetProgress}
        />

        {/* Recent Transactions */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <Calendar className="mr-2" size={24} />
            Recent Transactions
          </h3>
          
          {transactions.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              No transactions yet. Add your first transaction above!
            </p>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {transactions.slice(0, 10).map((transaction) => (
                <div
                  key={transaction.id}
                  className={`p-4 rounded-lg border-l-4 ${
                    transaction.type === 'income' 
                      ? 'border-green-400 bg-green-50' 
                      : 'border-red-400 bg-red-50'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-800">
                        {transaction.description}
                      </h4>
                      <p className="text-sm text-gray-600 capitalize">
                        {transaction.category.replace('_', ' ')} • {new Date(transaction.date).toLocaleDateString()}
                      </p>
                      {transaction.tags && transaction.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {transaction.tags.map((tag, idx) => (
                            <span key={idx} className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                      {transaction.is_recurring && (
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded mt-1 inline-block">
                          Recurring ({transaction.recurrence_type})
                        </span>
                      )}
                    </div>
                    <div className="text-right">
                      <p className={`font-bold ${
                        transaction.type === 'income' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {transaction.type === 'income' ? '+' : '-'}
                        {formatCurrency(transaction.amount, transaction.currency)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <AppContent />
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