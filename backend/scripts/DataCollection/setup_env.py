#!/usr/bin/env python3
"""Environment setup script for repository processor."""

import os
import shutil
from pathlib import Path

def setup_environment():
    """Set up the environment for the repository processor."""
    print("🚀 Setting up Repository Processor environment...")
    
    # Create .env file from template if it doesn't exist
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists() and env_example.exists():
        print("📋 Creating .env file from template...")
        shutil.copy2(env_example, env_file)
        print("✅ .env file created. Please edit it with your actual values.")
    elif env_file.exists():
        print("✅ .env file already exists.")
    else:
        print("❌ .env.example not found. Please create environment configuration.")
    
    # Create output directory
    output_dir = Path('./output')
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
        print("📁 Created output directory.")
    
    # Create cache directory
    cache_dir = Path('./.cache')
    if not cache_dir.exists():
        cache_dir.mkdir(parents=True)
        print("💾 Created cache directory.")
    
    # Check for GitHub token
    if not os.getenv('GITHUB_TOKEN'):
        print("\n⚠️  Important: Set your GitHub token in the .env file!")
        print("   1. Go to https://github.com/settings/tokens")
        print("   2. Generate a new token with 'public_repo' scope")
        print("   3. Add it to your .env file: GITHUB_TOKEN=your_token_here")
    
    print("\n✅ Environment setup complete!")

if __name__ == "__main__":
    setup_environment()
