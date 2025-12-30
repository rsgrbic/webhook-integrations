from dotenv import load_dotenv
import os
from flask import jsonify
import requests

load_dotenv()
GITLAB_API=os.getenv("GITLAB_API")
assert GITLAB_API, "Environment variable GITLAB_API is not set"

def create_merge_request(request):
        data=request.json
        ref = data.get("ref")
        branch_name = ref.split("/")[-1]
        default_branch = data.get("project").get("default_branch")
        project_id = data.get("project").get("id")
        headers_pat={"Private-Token": os.getenv("GITLAB_PAT")}
        asignee=data.get("user_id")
        url=f"{GITLAB_API}/projects/{project_id}/merge_requests"
        
        payload={
                "source_branch": branch_name,
                "target_branch": f"{default_branch}",
                "title": f"Auto MR for branch {branch_name}",
                "description": "This merge request was created automatically by the webhook handler.",
                "assignee_id": asignee
        }
        print(f"Creating merge request for branch {branch_name}...", flush=True)
        response = requests.post(url, headers=headers_pat, json=payload)
        if response.status_code == 201:
                print(f"Merge request created successfully for branch {branch_name}.", flush=True)
                return jsonify({
                "status": "Branch creation processed",
                "event": data.get("object_kind"),
                "result": 200
                }), 200
        else:
                print(f"Failed to create merge request for branch {branch_name}.", flush=True)
                print(response.text, flush=True)
                return jsonify({
                "status": "Branch creation failed - GitLab API error",
                "event": data.get("object_kind"),
                "result": 500
                }), 500
        

