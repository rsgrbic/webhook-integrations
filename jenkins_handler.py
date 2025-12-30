from dotenv import load_dotenv
import os
from flask import jsonify
import jenkins
from jira_handler import extract_jira_project
load_dotenv()

JENKINS_URL=os.getenv("JENKINS_URL")
JENKINS_KEY=os.getenv("JENKINS_KEY")
JENKINS_USER=os.getenv("JENKINS_USER")

assert JENKINS_KEY, "Environment variable JENKINS_KEY is not set"
assert JENKINS_URL, "Environment variable JENKINS_URL is not set"
assert JENKINS_USER, "Environment variable JENKINS_USER is not set"

_server = None

def _get_server():
    global _server
    if _server is None:
        _server = jenkins.Jenkins(
            JENKINS_URL,
            username=JENKINS_USER,
            password=JENKINS_KEY)
    return _server

def start_jenkins_job(request):
    data = request.json 
    branch = data.get("ref").removeprefix("refs/heads/")

    jira_key = extract_jira_project(branch)
    if jira_key is None:
        print("No Jira key found in branch name.", flush=True)
        return 400

    commit_sha   = data.get("checkout_sha")
    initiator    = data.get("user_username")

    server = _get_server()

    params = {
        "JIRA_KEY": jira_key,
        "BRANCH": branch,
        "COMMIT_SHA": commit_sha,
        "INITIATOR": initiator,
    }

    try:
        server.build_job("Hello world-maven", params) # Only job with a jenkinsfile script that suits this webhook
    except Exception as e:
        print (f"Failed to trigger Jenkins job: {e}", flush=True)
        print(e.__traceback__, flush=True)
        return jsonify({
        "status": "Failed to trigger Jenkins job",
        "event": data.get("object_kind"),
        "result": 500
        }), 500
    else:
        print(f"Jenkins job triggered for branch {branch}.", flush=True)
        return jsonify({
        "status": "Jenkins job triggered",
        "event": data.get("object_kind"),
        "result": 200
        }), 200