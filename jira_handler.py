from dotenv import load_dotenv
import os
from flask import jsonify
import requests
import re
from requests.auth import HTTPBasicAuth

load_dotenv()

JIRA_org=os.getenv("JIRA_ORG_URL")
JIRA_email=os.getenv("JIRA_EMAIL")
JIRA_token=os.getenv("JIRA_TOKEN")

assert JIRA_token , "Environment variable JIRA_TOKEN is not set"

def create_jira_story(request):
        data= request.json
        mr_info=data.get("object_attributes")
        branch_name=mr_info.get("source_branch")
        user=data.get("user")

        title=mr_info.get("title")
        description=mr_info.get("description")
        mr_url=mr_info.get("url")
        author=user.get("name")

        parsed_key=extract_jira_project(branch_name)
        
        if parsed_key is None:
                return jsonify({
                "status": "Failed",
                "event": data.get("object_kind"),
                "result": 400
                }), 400
        project_key = parsed_key.split("-")[0]


        jira_issue_type="Story"
        jira_summary= f"Merge Request Created: {title}"
        jira_description_adf = {
        "type": "doc",
        "version": 1,
        "content": [
        adf_paragraph(adf_text(f"Merge Request: {title} ({mr_url})")),
        adf_paragraph(adf_text(f"Author: {author}")),
        adf_paragraph(adf_text("Description:")),
        adf_paragraph(adf_text(description if description else "No description."))
        ]
        }

        auth=HTTPBasicAuth(JIRA_email, JIRA_token)
        headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
        }

        jira_payload={
                "fields": {
                        "project": {
                                "key": project_key
                        },
                        "summary": jira_summary,
                        "description": jira_description_adf,
                        "issuetype": {
                                "name": jira_issue_type
                        }
                }
        }
        JIRA_url=f"{JIRA_org}/rest/api/3/issue"
        r=requests.post(
                JIRA_url,
                headers=headers,
                json=jira_payload,
                auth=auth
        )
        if r.status_code == 201:
                print(f"JIRA issue created successfully for MR: {title} \n", flush=True)
                return jsonify({
                "status":"JIRA issue created successfully",
                "event": data.get("object_kind"),
                "result": 200
                }), 200
        else:
                print(f"Failed to create JIRA issue for MR: {title}. Status code: {r.status_code} \n", flush=True)
                return jsonify({
                "status":"Failed to create JIRA issue",
                "event": data.get("object_kind"),
                "result": r.status_code
                }), r.status_code

def extract_jira_project(name):
        pattern = r"[A-Z]+-\d+"
        match = re.search(pattern, name)
        return match.group(0) if match else None

# Jira paragraph formatter
def adf_paragraph(*parts):
    return {
        "type": "paragraph",
        "content": list(parts)
    }

def adf_text(text, marks=None):
    node = {"type": "text", "text": text}
    if marks:
        node["marks"] = marks
    return node



def leave_story_comment(request):
        data=request.json
        issue_key=data.get("jira_key")
        job_branch=data.get("branch")
        job_commit=data.get("commit_sha")
        job_initiator=data.get("initiator")
        job_status=data.get("status")
        job_url=data.get("url")
        job_build_number=data.get("build_number")

        comment_payload = {
                "body": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                                adf_paragraph(
                                        adf_text("Jenkins Job #"),
                                        adf_text(str(job_build_number), marks=[{"type": "strong"}]),
                                        adf_text(" Finished"),
                                ),
                                adf_paragraph(
                                        adf_text("Branch: ", marks=[{"type": "strong"}]),
                                        adf_text(job_branch, marks=[{"type": "code"}]),
                                ),
                                adf_paragraph(
                                        adf_text("Commit SHA: ", marks=[{"type": "strong"}]),
                                        adf_text(job_commit, marks=[{"type": "code"}]),
                                ),

                                # Status paragraph
                                adf_paragraph(
                                        adf_text("Status: "),
                                        adf_text(
                                        job_status,
                                        marks=[
                                                {
                                                "type": "textColor",
                                                "attrs": {
                                                        "color": "#36B37E" if job_status == "SUCCESS" else "#FF5630"
                                                }
                                                }
                                        ]
                                        )
                                ),

                                adf_paragraph(
                                        adf_text("Started by: ", marks=[{"type": "strong"}]),
                                        adf_text(job_initiator),
                                ),

                                adf_paragraph(
                                        {
                                        "type": "text",
                                        "text": "Open job in Jenkins",
                                        "marks": [
                                                {
                                                "type": "link",
                                                "attrs": {"href": job_url}
                                                }
                                        ]
                                        }
                                )
                        ]
                }
        }

        auth=HTTPBasicAuth(JIRA_email, JIRA_token)
        headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
        }

        JIRA_url=f"{JIRA_org}/rest/api/3/issue/{issue_key}/comment"
        r=requests.post(
                JIRA_url,
                headers=headers,
                json=comment_payload,
                auth=auth
        )
        if r.status_code == 201:
                print(f"Comment added to JIRA issue {issue_key} successfully. \n", flush=True)
                return jsonify({
                "status":"Comment added successfully",
                "event": data.get("event"),
                "result": 200
                }), 200
        else:
                print(f"Failed to add comment to JIRA issue {issue_key}. Status code: {r.status_code} \n", flush=True)
                print(r.text, flush=True)
                return jsonify({
                "status":"Failed to add comment",
                "event": data.get("event"),
                "result": r.status_code
                }), r.status_code