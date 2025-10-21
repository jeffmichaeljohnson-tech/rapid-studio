#!/bin/bash

echo "🔍 VERIFYING RAPID STUDIO SETUP"
echo "===================================="

# Check if we're in the right directory
if [[ ! $(pwd) =~ rapid-studio-1$ ]]; then
    echo "⚠️  Please run this from the rapid-studio-1 directory"
    echo "💡 Run: cd ~/rapid-studio-1"
    exit 1
fi

echo "📁 Current directory: $(pwd)"
echo ""

echo "📦 Checking package.json..."
if [ -f "package.json" ]; then
    echo "✅ package.json found"
    echo "📋 Main dependencies:"
    grep -E '"expo"|"react-native"' package.json || echo "⚠️  Some dependencies may be missing"
else
    echo "❌ package.json not found"
fi

echo ""
echo "📱 Checking Expo app structure..."
if [ -f "app.json" ]; then
    echo "✅ app.json found"
else
    echo "❌ app.json not found"
fi

if [ -f "app/_layout.tsx" ]; then
    echo "✅ app/_layout.tsx found"
else
    echo "❌ app/_layout.tsx not found"
fi

if [ -f "app/index.tsx" ]; then
    echo "✅ app/index.tsx found"
else
    echo "❌ app/index.tsx not found"
fi

echo ""
echo "🎨 Checking SwipeDeck component..."
if [ -f "components/SwipeDeck.tsx" ]; then
    echo "✅ SwipeDeck.tsx found"
    # Check if it has the right imports
    if grep -q "react-native-gesture-handler" components/SwipeDeck.tsx; then
        echo "✅ Gesture handler imported"
    else
        echo "⚠️  Gesture handler import may be missing"
    fi
    if grep -q "react-native-reanimated" components/SwipeDeck.tsx; then
        echo "✅ Reanimated imported"
    else
        echo "⚠️  Reanimated import may be missing"
    fi
else
    echo "❌ SwipeDeck.tsx not found"
fi

echo ""
echo "🔑 Checking environment configuration..."
if [ -f ".env" ]; then
    echo "✅ .env file found"
    if grep -q "EXPO_PUBLIC_API_URL" .env; then
        echo "✅ API URL configured"
    fi
    if grep -q "your_.*_key_here" .env; then
        echo "⚠️  API keys need to be updated with real values"
    fi
else
    echo "❌ .env file not found"
fi

echo ""
echo "🛠️  Checking node_modules..."
if [ -d "node_modules" ]; then
    echo "✅ node_modules found"
    
    # Check key dependencies
    if [ -d "node_modules/expo" ]; then
        echo "✅ Expo installed"
    else
        echo "❌ Expo not installed"
    fi
    
    if [ -d "node_modules/react-native-gesture-handler" ]; then
        echo "✅ Gesture handler installed"
    else
        echo "❌ Gesture handler not installed"
    fi
    
    if [ -d "node_modules/react-native-reanimated" ]; then
        echo "✅ Reanimated installed"
    else
        echo "❌ Reanimated not installed"
    fi
else
    echo "❌ node_modules not found - run npm install"
fi

echo ""
echo "📊 Project health summary:"
echo "========================="

# Count issues
issues=0

[ ! -f "package.json" ] && ((issues++))
[ ! -f "app.json" ] && ((issues++))
[ ! -f "app/_layout.tsx" ] && ((issues++))
[ ! -f "app/index.tsx" ] && ((issues++))
[ ! -f "components/SwipeDeck.tsx" ] && ((issues++))
[ ! -f ".env" ] && ((issues++))
[ ! -d "node_modules" ] && ((issues++))

if [ $issues -eq 0 ]; then
    echo "🎉 PROJECT IS READY!"
    echo ""
    echo "🚀 To start development:"
    echo "1. Update API keys in .env file"
    echo "2. Run: npx expo start"
    echo "3. Scan QR code with Expo Go app"
else
    echo "⚠️  Found $issues issues that need attention"
    echo ""
    echo "🔧 To fix issues, run the setup script first"
fi

echo ""
echo "📋 Quick commands:"
echo "• Install dependencies: npm install"
echo "• Start Expo: npx expo start"
echo "• Clear cache: npx expo start --clear"
echo "• Check Expo status: npx expo whoami"
