# Heroku Deployment Guide for Make-Ready Report Generator

This guide will walk you through deploying the Make-Ready Report Generator to Heroku.

## Prerequisites

1. [Heroku Account](https://signup.heroku.com/) - Sign up for a free account if you don't have one
2. [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) - Install the command-line interface
3. [Git](https://git-scm.com/downloads) - Make sure Git is installed
4. (Optional) An AWS account with S3 access for file storage

## Local Setup and Testing

Before deploying to Heroku, it's recommended to test your application locally:

1. Create a local environment file:
   ```bash
   cp .env.sample .env
   ```

2. Edit the `.env` file with your specific configuration values:
   ```
   SECRET_KEY=your_random_secret_key
   USE_S3=False
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Visit `http://localhost:5000` to test the application

## Heroku Deployment Steps

### 1. Login to Heroku

```bash
heroku login
```

### 2. Create a Heroku App (if you haven't already)

```bash
heroku create your-app-name
```

Or connect to an existing app:

```bash
heroku git:remote -a your-app-name
```

### 3. Configure Environment Variables

Set up the required environment variables on Heroku:

```bash
heroku config:set SECRET_KEY=your_random_secret_key
```

If using AWS S3 for file storage (recommended for production):

```bash
heroku config:set USE_S3=True
heroku config:set S3_BUCKET_NAME=your-s3-bucket-name
heroku config:set AWS_ACCESS_KEY_ID=your-aws-access-key
heroku config:set AWS_SECRET_ACCESS_KEY=your-aws-secret-key
heroku config:set AWS_REGION=us-east-1
```

### 4. Deploy to Heroku

If you're deploying using Heroku CLI:

```bash
git add .
git commit -m "Prepare for Heroku deployment"
git push heroku main
```

If you've connected your GitHub repository to Heroku, you can deploy through the Heroku Dashboard by enabling automatic deploys or manually deploying a branch.

### 5. Verify Deployment

```bash
heroku open
```

This will open your application in a browser.

## AWS S3 Setup (Recommended for Production)

For Heroku's ephemeral filesystem, using AWS S3 is recommended:

1. Create an AWS S3 bucket:
   - Go to AWS Management Console > S3 > Create bucket
   - Name the bucket (must be globally unique)
   - Configure permissions to allow appropriate access

2. Create an IAM user with S3 access:
   - Go to IAM > Users > Add user
   - Enable programmatic access
   - Attach policies: `AmazonS3FullAccess` (or create a more restricted policy)
   - Save the Access Key ID and Secret Access Key

3. Configure your Heroku application with these credentials as shown above

## Troubleshooting

### Application Error or Crashed

Check the logs:
```bash
heroku logs --tail
```

### File Upload Issues

Ensure your S3 bucket policy allows uploads and your IAM credentials are correct.

### Slow File Processing

Consider using a worker dyno with a background processing system like Celery for large file processing tasks.

## Additional Resources

- [Heroku Python Support](https://devcenter.heroku.com/articles/python-support)
- [Heroku S3 Integration](https://devcenter.heroku.com/articles/s3)
- [Flask on Heroku](https://devcenter.heroku.com/articles/getting-started-with-python)
