#!/bin/bash
# Deploy Apify Actor Script

echo "🚀 Deploying AWS Content Monitor to Apify..."

# Check if Apify CLI is installed
if ! command -v apify &> /dev/null; then
    echo "❌ Apify CLI not found. Installing..."
    npm install -g apify-cli
fi

# Login check
if ! apify info &> /dev/null; then
    echo "🔐 Please login to Apify:"
    apify login
fi

# Deploy the actor
echo "📦 Pushing actor to Apify..."
apify push

# Get actor info
echo "ℹ️ Actor deployed successfully!"
apify info

echo "✅ Deployment complete! Your actor is ready to run."
echo "🔗 View in Apify Console: https://console.apify.com/actors"