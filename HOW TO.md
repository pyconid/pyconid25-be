# HOW TO: Setup and Configuration Guide

This guide will help you set up and configure the necessary components for your application.

## 1. Prerequisites

Before starting, make sure you have:
- A GitHub account

## 2. GitHub OAuth Setup

To enable GitHub OAuth authentication in your application, you'll need to obtain a GitHub Client ID and Client Secret.

### Step 1: Create a GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click on **"OAuth Apps"** in the left sidebar
3. Click **"New OAuth App"** button

### Step 2: Configure OAuth App Details

Fill in the required information:

- **Application name**: Enter a descriptive name for your application
- **Homepage URL**: Your application's main URL (e.g., `https://yourapp.com`)
- **Application description**: Brief description of your app (optional)
- **Authorization callback URL**: The URL GitHub will redirect to after authorization
  - For development: `http://localhost:3000/auth/github/callback`
  - For production: `https://yourapp.com/auth/github/callback`

**Note:** On this project, callback URL is set to frontend URL, which is `http://localhost:3000/auth/github/callback` for development.

### Step 3: Generate Client Secret

1. After creating the OAuth app, you'll see your **Client ID** displayed
2. Click **"Generate a new client secret"** button
3. Copy and securely store both:
   - `GITHUB_CLIENT_ID` (client ID)
   - `GITHUB_CLIENT_SECRET` (client secret)

### Step 4: Environment Configuration

Create a `.env` file in your project root and add:

```env
GITHUB_CLIENT_ID=your_client_id_here
GITHUB_CLIENT_SECRET=your_client_secret_here
```

### Step 5: Update OAuth App Settings (if needed)

You can modify your OAuth app settings anytime:
1. Go back to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click on your OAuth app name
3. Update URLs or regenerate secrets as needed

### Common Issues:

**Invalid Client ID/Secret:**
- Double-check your environment variables
- Ensure no extra spaces or characters
- Verify the OAuth app is active

**Callback URL Mismatch:**
- Ensure callback URL in GitHub matches your application
- Check for HTTP vs HTTPS differences
- Verify port numbers for local development

**Authorization Denied:**
- Check OAuth app permissions
- Ensure the app isn't suspended
- Verify user has access to the repository (if applicable)

## Additional Resources

- [GitHub OAuth Documentation](https://docs.github.com/en/developers/apps/building-oauth-apps)
- [GitHub OAuth Best Practices](https://docs.github.com/en/developers/apps/building-oauth-apps/best-practices-for-oauth-apps)
