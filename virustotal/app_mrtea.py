import base64
import sys
import os
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BASE_URL = "https://www.virustotal.com/api/v3"
# ---- NEW CODE: allow CLI argument key=xxxxx ----
VT_API_KEY = os.getenv("VT_API_KEY")  # default from env
 
# Parse CLI args like: python app.py key=xxxxx
for arg in sys.argv[1:]:
    if arg.startswith("key="):
        VT_API_KEY = arg.split("key=")[1]
        print(f"[+] VT_API_KEY set from command-line argument.")
# ------------------------------------------------


# old code to remove: VT_API_KEY = os.getenv("VT_API_KEY")




def get_headers():
    if not VT_API_KEY:
        # You could also return a 500 in endpoints instead of raising.
        raise RuntimeError("VT_API_KEY environment variable is not set.")
    return {"x-apikey": VT_API_KEY}

def url_to_vt_id(url: str) -> str:
    """
    Convert a plain URL to the VirusTotal URL ID
    (URL-safe base64 without '=' padding).
    """
    return base64.urlsafe_b64encode(url.encode()).decode().strip("=")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/file/<file_hash>", methods=["GET"])
def check_file_hash(file_hash):
    """
    GET /api/file/<hash>
    Example:
      GET /api/file/44d88612fea8a8f36de82e1278abb02f
    """
    try:
        headers = get_headers()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    url = f"{BASE_URL}/files/{file_hash}"
    resp = requests.get(url, headers=headers)

    # Pass through VT status code & JSON content
    try:
        data = resp.json()
    except Exception:
        return jsonify({"error": "Non-JSON response from VirusTotal", "raw": resp.text}), resp.status_code

    return jsonify(data), resp.status_code


@app.route("/api/url/scan", methods=["POST"])
def scan_url():
    """
    POST /api/url/scan
    JSON body: { "url": "https://example.com" }
    """
    payload = request.get_json(silent=True) or {}
    url_to_scan = payload.get("url")

    if not url_to_scan:
        return jsonify({"error": "Missing 'url' in JSON body"}), 400

    try:
        headers = get_headers()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    submit_url = f"{BASE_URL}/urls"

    # 1) Submit URL for analysis
    submit_resp = requests.post(submit_url, headers=headers, data={"url": url_to_scan})

    if submit_resp.status_code not in (200, 201):
        # Forward the VT error
        try:
            details = submit_resp.json()
        except Exception:
            details = {"raw": submit_resp.text}
        return jsonify(
            {
                "error": "Error submitting URL to VirusTotal",
                "status_code": submit_resp.status_code,
                "details": details,
            }
        ), submit_resp.status_code

    try:
        analysis_id = submit_resp.json()["data"]["id"]
    except Exception as e:
        return jsonify(
            {
                "error": "Could not extract analysis ID from VirusTotal response",
                "exception": str(e),
                "raw": submit_resp.text,
            }
        ), 500

    analysis_url = f"{BASE_URL}/analyses/{analysis_id}"

    # 2) Poll analysis a few times (simple synchronous PoC)
    for _ in range(5):  # 5 * 3s = 15 seconds max
        time.sleep(3)
        analysis_resp = requests.get(analysis_url, headers=headers)

        if analysis_resp.status_code != 200:
            try:
                details = analysis_resp.json()
            except Exception:
                details = {"raw": analysis_resp.text}
            return jsonify(
                {
                    "error": "Error polling analysis",
                    "status_code": analysis_resp.status_code,
                    "details": details,
                }
            ), analysis_resp.status_code

        data = analysis_resp.json()
        status = data["data"]["attributes"].get("status")

        if status == "completed":
            # Return full VT analysis JSON
            return jsonify(data), 200

    # If not completed in time, return the analysis_id so caller can poll later if they want
    return jsonify({"analysis_id": analysis_id, "status": "pending"}), 202


@app.route("/api/url/report", methods=["GET"])
def url_report():
    """
    GET /api/url/report?url=https://example.com

    Returns the latest VT report for that URL (does NOT resubmit).
    """
    url_param = request.args.get("url")
    if not url_param:
        return jsonify({"error": "Missing 'url' query parameter"}), 400

    try:
        headers = get_headers()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    vt_id = url_to_vt_id(url_param)
    vt_url = f"{BASE_URL}/urls/{vt_id}"

    resp = requests.get(vt_url, headers=headers)

    try:
        data = resp.json()
    except Exception:
        return jsonify(
            {
                "error": "Non-JSON response from VirusTotal",
                "raw": resp.text,
            }
        ), resp.status_code

    return jsonify(data), resp.status_code

if __name__ == "__main__":
    # host=0.0.0.0 is important so Codespaces can expose the port
    app.run(host="0.0.0.0", port=8000, debug=True)
