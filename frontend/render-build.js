const { execSync } = require('child_process');
const fs = require('fs');

// Update API URL for production
const envContent = `VITE_API_BASE_URL="";
fs.writeFileSync('.env.production', envContent);

console.log('Production environment file created');