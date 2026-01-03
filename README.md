# GitLab Webhook Handler

A Flask-based webhook handler that automates CI/CD workflows by integrating GitLab, Jenkins, and Jira.

## Features

- **Automatic Merge Request Creation**: Creates merge requests when new branches are pushed
- **Jenkins Job Triggering**: Automatically triggers Jenkins builds on branch pushes
- **Jira Integration**: Creates Jira stories for merge requests and posts Jenkins job status comments
- **Branch-Based Automation**: Extracts Jira issue keys from branch names for seamless tracking

## Prerequisites

- Python 3.12+
- GitLab instance with webhook and API access
- Jenkins server with API access
- Jira instance with API access
- Docker (optional)

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Jenkins Configuration
JENKINS_URL=http://<your-jenkins-server>
JENKINS_USER=your-jenkins-username
JENKINS_KEY=your-jenkins-api-token

# Jira Configuration
JIRA_ORG_URL=https://your-org.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_TOKEN=your-jira-api-token

# GitLab Configuration
GITLAB_API=https://<gitlab-isntance>/api/v4
GITLAB_PAT=your-gitlab-personal-access-token
```

## Installation

### Local Setup

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create and configure your `.env` file

4. Run the application:
```bash
flask run
```

The server will start on `http://0.0.0.0:5000`

### Docker Setup

1. Build the Docker image:
```bash
docker build -t gitlab-webhook-handler .
```

2. Run the container:
```bash
docker run -d -p 5000:5000  gitlab-webhook-handler
```

## GitLab Webhook Configuration

1. Go to your GitLab project → **Settings** → **Webhooks**
2. Add webhook URL: `http://your-server:5000/gitlab-webhook`
3. Enable the following triggers:
   - **Push events**
   - **Merge request events**
4. Save the webhook

## Jenkins Job Configuration

Your Jenkins job must be configured to accept the following parameters:

- `JIRA_KEY` (String): Jira issue key extracted from branch name
- `BRANCH` (String): Git branch name
- `COMMIT_SHA` (String): Git commit SHA
- `INITIATOR` (String): Username who triggered the build

**To configure parameters in Jenkins:**

1. Open your job → **Configure**
2. Check **"This project is parameterized"**
3. Add the four String parameters listed above
4. Save the configuration

## Webhook Events & Workflows

### Push Event - New Branch

**Trigger**: First push to a new branch (before hash is all zeros)

**Action**: Creates a merge request automatically

### Push Event - Existing Branch

**Trigger**: Push to an existing branch

**Action**: Triggers Jenkins job

**Requirements**: Branch name must contain a Jira key (e.g., `KAN-2-feature-name`)

### Merge Request Event

**Trigger**: Merge request opened

**Action**: Creates Jira story

### Jenkins Job Status Webhook

**Endpoint**: `POST /job-status`

**Purpose**: Receives Jenkins job completion notifications

**Action**: Posts comment to Jira issue

**Required payload**:
```json
{
  "jira_key": "KAN-2",
  "branch": "KAN-2-feature-name",
  "commit_sha": "abc123...",
  "initiator": "username",
  "status": "SUCCESS",
  "url": "http://JENKINS_URL/job/...",
  "build_number": "42"
}
```

**Configure in Jenkins Pipeline**:
```groovy
post {
    ...
    always {
        sh """
        curl -X POST \
                -H "Content-Type: application/json" \
                -d '{
                "jira_key": "${params.JIRA_KEY}",
                "branch": "${params.BRANCH}",
                "commit_sha": "${params.COMMIT_SHA}",
                "initiator": "${params.INITIATOR}",
                "status": "${currentBuild.currentResult}",
                "url": "${env.BUILD_URL}",
                "build_number": "${env.BUILD_NUMBER}"
                }' \
                http://flask.217.182.105.211.sslip.io/job-status 
        """
    }
}
```

## Branch Naming Convention

For automated Jira integration, branch names must follow this pattern:

```
<JIRA_KEY>-<description>
```

**Examples**:
- `KAN-123-add-user-authentication`
- `PROJ-456-fix-login-bug`
- `DEV-789-update-readme`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check endpoint |
| `/gitlab-webhook` | POST | Main webhook handler for GitLab events |
| `/job-status` | POST | Receives Jenkins job status updates |

## Troubleshooting

**Problem**: "No Jira key found in branch name"

**Solutions**:
1. Verify branch name follows pattern: `PROJECT-123-description`
2. Check Jira key has capital letters and numbers
3. Branch must contain full key (e.g., `KAN-2`, not just `2`)

## Project Structure

```
.
├── app.py                    # Main Flask application
├── jenkins_handler.py        # Jenkins job triggering logic
├── jira_handler.py          # Jira API integration
├── repo_events_handler.py   # GitLab merge request creation
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
└── .env                    # Environment variables (not in repo)
```

## Never commit .env to a repository
