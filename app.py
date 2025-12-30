from flask import Flask, jsonify, request
from repo_events_handler import create_merge_request
from jenkins_handler import start_jenkins_job
from jira_handler import create_jira_story, leave_story_comment
import logging
app = Flask(__name__)

zero_push_hash="0000000000000000000000000000000000000000"

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.get("/")
def home():
    return "Welcome to the Flask API!"

@app.post("/gitlab-webhook")
def gitlab_webhook():
    data=request.json
    response=jsonify({
    "status": "Let through",
    "event": data.get("object_kind"),
    "result": 200
    }), 200
    print(f"Received GitLab webhook - trigger: {data.get('object_kind')}", flush=True)
    if data.get("object_kind") == "push":
        if data.get("before") == zero_push_hash :
            response=create_merge_request(request)
        else:
            response=start_jenkins_job(request)

    elif data.get("object_kind") == "merge_request": 
        action = data.get("object_attributes").get("action")
        if action in ["open"]:
            response=create_jira_story(request)

    return response


@app.post("/job-status")
def job_status():
    response = leave_story_comment(request)
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

