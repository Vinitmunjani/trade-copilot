#!/bin/bash

echo "🚀 Trade Co-Pilot Frontend Demo"
echo "================================"
echo ""

# Check if running
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend already running at http://localhost:3000"
else
    echo "🔧 Starting development server..."
    npm run dev &
    sleep 5
    echo "✅ Frontend started at http://localhost:3000"
fi

echo ""
echo "📋 Available Pages:"
echo "  🏠 Landing Page:     http://localhost:3000"
echo "  🔐 Login:           http://localhost:3000/login"
echo "  📝 Register:        http://localhost:3000/register"
echo "  📊 Dashboard:       http://localhost:3000/dashboard"
echo "  📈 Trade History:   http://localhost:3000/trades"
echo "  📊 Analytics:       http://localhost:3000/analytics"
echo "  🧠 Patterns:        http://localhost:3000/patterns"
echo "  🛡️ Rules:           http://localhost:3000/rules"
echo "  📄 Reports:         http://localhost:3000/reports"
echo "  ⚙️ Settings:        http://localhost:3000/settings"
echo ""
echo "💡 Use mock credentials:"
echo "  Email: demo@trader.com"
echo "  Password: password123"
echo ""
echo "Press Ctrl+C to stop the server"
