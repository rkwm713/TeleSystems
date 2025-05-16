# Heroku Deployment Guide for Make-Ready Report Generator

This guide will walk you through deploying the Make-Ready Report Generator to Heroku.

## Prerequisites

1. [Heroku Account](https://signup.heroku.com/) - Sign up for a free account if you don't have one
2. [Git](https://git-scm.com/downloads) - Make sure Git is installed
3. (Optional) An AWS account with S3 access for file storage

## Key Files for Heroku Deployment

Your project now includes the following files for Heroku deployment:

1. **Procfile**: Tells Heroku how to run your application
2. **.python-version**: Specifies the Python version (3.11)
3. **requirements.txt**: Lists all dependencies with compatible versions
4. **heroku-config.txt**: Lists required environment variables

## Environment Variables Setup (Critical)

Set the following environment variables in your Heroku app:

1. Go to [Heroku Dashboard](https://dashboard.heroku.com/) → Your app → Settings
2. Click on "Reveal Config Vars"
3. Add these variables (as specified in heroku-config.txt):
   - KEY: `SECRET_KEY`, VALUE: `your-random-string-here123`
   - KEY: `USE_S3`, VALUE: `False`

These environment variables are essential for your app to run correctly.

## Deployment Methods

### Method 1: GitHub Integration (Recommended)

1. Go to Heroku Dashboard → Your app → Deploy
2. Select "GitHub" as deployment method
3. Connect to your GitHub repository
4. Choose the branch to deploy
5. Click "Deploy Branch" or enable "Automatic Deploys"

### Method 2: Git Push (Alternative)

If you've set up the Heroku CLI:

```bash
git add .
git commit -m "Ready for Heroku deployment"
git push heroku main
```

## Troubleshooting Common Issues

### Numpy/Pandas Compatibility Issue

We've fixed a common compatibility issue by pinning numpy to version 1.24.3, which is compatible with pandas 2.0.1. If you encounter other dependency issues, check the error logs and update the requirements.txt file accordingly.

### Application Error (H10 Crash)

If your app crashes with an H10 error:

1. Make sure environment variables are set correctly
2. Check the logs for specific errors:
   ```bash
   heroku logs --tail
   ```

### File Storage Limitations

Heroku has an ephemeral filesystem, meaning files saved to the local disk will be lost when:
- The app is redeployed
- The dyno restarts
- The app crashes and restarts

For production use, it's recommended to configure AWS S3 storage:

```
heroku config:set USE_S3=True
heroku config:set S3_BUCKET_NAME=your-s3-bucket-name
heroku config:set AWS_ACCESS_KEY_ID=your-aws-access-key
heroku config:set AWS_SECRET_ACCESS_KEY=your-aws-secret-key
heroku config:set AWS_REGION=us-east-1
```

## AWS S3 Setup (for Production)

1. Create an AWS S3 bucket
2. Create an IAM user with S3 access:
   - Enable programmatic access
   - Attach policies: `AmazonS3FullAccess` (or create a more restricted policy)
   - Save the Access Key ID and Secret Access Key
3. Configure environment variables as shown above

## Additional Resources

- [Heroku Python Support](https://devcenter.heroku.com/articles/python-support)
- [Heroku S3 Integration](https://devcenter.heroku.com/articles/s3)
- [Flask on Heroku](https://devcenter.heroku.com/articles/getting-started-with-python)
