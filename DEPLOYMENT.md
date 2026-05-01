# Deployment Guide: E-Commerce API 🚀

This guide covers deploying your Flask backend to **Render** or **Heroku**, configuring a production PostgreSQL database, and setting up AWS S3 for image storage.

## 🌟 Prerequisites
- A GitHub/GitLab account with this repository pushed.
- An account on [Render](https://render.com) or [Heroku](https://heroku.com).
- An AWS account (for S3 storage).

---

## Option 1: Deploy to Render (Recommended)
Render natively supports PostgreSQL and has a free tier that is perfect for this project.

1. **Connect your Repository:**
   - Log into Render, click **New +**, and select **Blueprint**.
   - Connect your GitHub repository containing this code.

2. **Deploy via `render.yaml`:**
   - Render will detect the `render.yaml` file in the root directory.
   - It will automatically set up two services:
     1. A **PostgreSQL Database** (`ecommerce-db`).
     2. A **Web Service** (`ecommerce-api`).
   - The `DATABASE_URL` will be automatically linked between the DB and the Web service.
   - Wait for the deployment to finish!

3. **Configure S3 Environment Variables:**
   - In the Render dashboard, go to your Web Service -> **Environment**.
   - Fill in the values for the following variables:
     - `S3_BUCKET_NAME`: Your AWS S3 Bucket Name
     - `AWS_REGION`: Your bucket region (e.g., `us-east-1`)
     - `AWS_ACCESS_KEY_ID`: Your IAM user access key
     - `AWS_SECRET_ACCESS_KEY`: Your IAM user secret key

---

## Option 2: Deploy to Heroku

1. **Create Heroku App & DB:**
   - Install the Heroku CLI and login: `heroku login`
   - Create a new app: `heroku create your-ecommerce-app`
   - Add a PostgreSQL database: `heroku addons:create heroku-postgresql:mini`

2. **Push Code to Heroku:**
   - Ensure you commit all changes (including the `Procfile` we created).
   - Push to Heroku: `git push heroku main`

3. **Configure Environment Variables in Heroku:**
   - Set the secret key: `heroku config:set SECRET_KEY="your-random-secret"`
   - Set S3 Variables:
     ```bash
     heroku config:set S3_BUCKET_NAME="your-bucket-name"
     heroku config:set AWS_REGION="us-east-1"
     heroku config:set AWS_ACCESS_KEY_ID="your-access-key"
     heroku config:set AWS_SECRET_ACCESS_KEY="your-secret-key"
     ```

---

## 🛠️ Configuring AWS S3 for Image Storage
The application has been upgraded to automatically detect if S3 is configured. If `S3_BUCKET_NAME` is set in the environment, all product image uploads (and generated thumbnails) will be routed to S3 instead of local storage.

1. **Create an S3 Bucket:**
   - Go to the AWS S3 Console -> Create Bucket.
   - Uncheck "Block all public access" (you will need objects to be readable so the frontend can load images).
   - Acknowledge the warning.

2. **Create an IAM User:**
   - Go to IAM -> Users -> Create User.
   - Attach the policy `AmazonS3FullAccess` (or create a custom policy restricted to your specific bucket).
   - Generate an **Access Key** for the user (CLI/Programmatic access).
   - Save the `Access Key ID` and `Secret Access Key`. Add them to your environment variables on Render/Heroku.

3. **Bucket Policy (Optional but Recommended):**
   - In your S3 Bucket -> Permissions -> Bucket Policy, add a policy to allow public reads so users can view images:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Sid": "PublicReadGetObject",
           "Effect": "Allow",
           "Principal": "*",
           "Action": "s3:GetObject",
           "Resource": "arn:aws:s3:::your-bucket-name/*"
         }
       ]
     }
     ```

## 🚀 Running Migrations / Seeding
If you want to run the seed script on your production database:
- **Render:** In the dashboard for your web service, go to the **Shell** tab and run `python seed.py`.
- **Heroku:** Run `heroku run python seed.py`.

*Note: Since your database is now PostgreSQL, the models are automatically created by `db.create_all()` in `app.py` when the app starts.*
