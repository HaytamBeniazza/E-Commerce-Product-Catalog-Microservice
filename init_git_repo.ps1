# PowerShell script to safely initialize and push to GitHub
# Run this script after creating your GitHub repository

Write-Host "🔒 E-Commerce Microservice - GitHub Setup Script" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Check if Git is installed
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git is not installed. Please install Git first." -ForegroundColor Red
    exit 1
}

# Check if we're already in a Git repository
if (Test-Path ".git") {
    Write-Host "⚠️  Git repository already exists." -ForegroundColor Yellow
    $continue = Read-Host "Do you want to continue? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "❌ Aborted." -ForegroundColor Red
        exit 1
    }
}

# Security check reminder
Write-Host "`n🔍 Security Check Reminder:" -ForegroundColor Yellow
Write-Host "1. Have you reviewed SECURITY_CHECKLIST.md?" -ForegroundColor White
Write-Host "2. Are all credentials in .env file placeholder values?" -ForegroundColor White
Write-Host "3. Have you verified no real API keys are in the code?" -ForegroundColor White

$securityConfirm = Read-Host "`nConfirm security review completed (y/N)"
if ($securityConfirm -ne "y" -and $securityConfirm -ne "Y") {
    Write-Host "❌ Please complete security review first." -ForegroundColor Red
    Write-Host "📋 Review the SECURITY_CHECKLIST.md file" -ForegroundColor Yellow
    exit 1
}

# Get GitHub repository URL
Write-Host "`n📝 GitHub Repository Setup:" -ForegroundColor Cyan
$repoUrl = Read-Host "Enter your GitHub repository URL (e.g., https://github.com/username/repo.git)"

if (-not $repoUrl) {
    Write-Host "❌ Repository URL is required." -ForegroundColor Red
    exit 1
}

# Validate URL format
if ($repoUrl -notmatch "^https://github\.com/.+/.+\.git$") {
    Write-Host "⚠️  URL format should be: https://github.com/username/repository.git" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

try {
    Write-Host "`n🚀 Initializing Git repository..." -ForegroundColor Green
    
    # Initialize Git repository if not exists
    if (-not (Test-Path ".git")) {
        git init
        Write-Host "✅ Git repository initialized" -ForegroundColor Green
    }
    
    # Add remote origin
    Write-Host "🔗 Adding remote origin..." -ForegroundColor Green
    git remote remove origin 2>$null  # Remove if exists
    git remote add origin $repoUrl
    Write-Host "✅ Remote origin added: $repoUrl" -ForegroundColor Green
    
    # Create .gitignore if not exists (should already exist)
    if (-not (Test-Path ".gitignore")) {
        Write-Host "⚠️  .gitignore not found, creating basic one..." -ForegroundColor Yellow
        @"
.env
__pycache__/
*.pyc
.vscode/
.idea/
node_modules/
"@ | Out-File -FilePath ".gitignore" -Encoding UTF8
    }
    
    # Stage all files
    Write-Host "📦 Staging files..." -ForegroundColor Green
    git add .
    
    # Show what will be committed
    Write-Host "`n📋 Files to be committed:" -ForegroundColor Cyan
    git status --porcelain
    
    # Final confirmation
    Write-Host "`n⚠️  FINAL SECURITY CHECK:" -ForegroundColor Red
    Write-Host "The following files will be pushed to PUBLIC GitHub:" -ForegroundColor Yellow
    git ls-files --cached | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }
    
    $finalConfirm = Read-Host "`nProceed with commit and push? (y/N)"
    if ($finalConfirm -ne "y" -and $finalConfirm -ne "Y") {
        Write-Host "❌ Aborted by user." -ForegroundColor Red
        exit 1
    }
    
    # Commit
    Write-Host "`n💾 Creating initial commit..." -ForegroundColor Green
    git commit -m "🚀 Initial commit: E-Commerce Product Catalog Microservice

✨ Features:
- FastAPI-based microservice architecture
- JWT authentication with refresh tokens
- PostgreSQL database with async SQLAlchemy
- Redis caching and session management
- Comprehensive API documentation
- Docker containerization
- Multi-database microservice setup
- Security best practices implemented

🔒 Security:
- All sensitive data uses environment variables
- No hardcoded secrets or credentials
- Comprehensive .gitignore for sensitive files
- Security checklist included

📚 Documentation:
- Complete API documentation
- Setup and deployment guides
- Multi-service architecture examples
- Production deployment notes"
    
    Write-Host "✅ Initial commit created" -ForegroundColor Green
    
    # Push to GitHub
    Write-Host "🌐 Pushing to GitHub..." -ForegroundColor Green
    git branch -M main
    git push -u origin main
    
    Write-Host "`n🎉 SUCCESS!" -ForegroundColor Green
    Write-Host "✅ Repository successfully pushed to GitHub" -ForegroundColor Green
    Write-Host "🔗 Repository URL: $repoUrl" -ForegroundColor Cyan
    
    Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Set up GitHub Actions for CI/CD" -ForegroundColor White
    Write-Host "2. Enable Dependabot for security updates" -ForegroundColor White
    Write-Host "3. Configure branch protection rules" -ForegroundColor White
    Write-Host "4. Add repository description and topics" -ForegroundColor White
    Write-Host "5. Create production environment variables" -ForegroundColor White
    
} catch {
    Write-Host "`n❌ Error occurred:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "`n🔧 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check if Git is properly installed" -ForegroundColor White
    Write-Host "2. Verify GitHub repository exists and URL is correct" -ForegroundColor White
    Write-Host "3. Ensure you have push permissions to the repository" -ForegroundColor White
    Write-Host "4. Check your Git credentials (git config --global user.name/email)" -ForegroundColor White
    exit 1
}

Write-Host "`n🔒 Security Reminder:" -ForegroundColor Yellow
Write-Host "Remember to set up production environment variables!" -ForegroundColor White
Write-Host "Never commit real secrets to the repository!" -ForegroundColor Red