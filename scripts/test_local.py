import subprocess
import time
import urllib.request
import urllib.error
import json
import base64
import sys
import os

def check_health(url, retries=10, delay=1):
    for i in range(retries):
        try:
            with urllib.request.urlopen(f"{url}/health") as response:
                if response.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(delay)
    return False

def make_pubsub_payload(filename, bucket, content_type, size):
    gcs_event = {
        "name": filename,
        "bucket": bucket,
        "contentType": content_type,
        "size": str(size)
    }
    event_json = json.dumps(gcs_event)
    encoded_data = base64.b64encode(event_json.encode('utf-8')).decode('utf-8')
    return {
        "message": {
            "data": encoded_data,
            "messageId": "mock-message-id-123"
        },
        "subscription": "projects/mock-project/subscriptions/mock-sub"
    }

def send_post(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            return response.status, json.loads(res_body)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    processor_dir = os.path.join(project_root, "processor")
    
    print("Starting FastAPI app locally...")
    env = os.environ.copy()
    if "PROJECT_ID" in env:
        del env["PROJECT_ID"]
        
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=processor_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    local_url = "http://127.0.0.1:8000"
    
    try:
        print("Waiting for server to start...")
        if not check_health(local_url):
            print("Error: Server failed to start or health check timed out.")
            # Give a moment to read stdout/stderr if any
            try:
                stdout, stderr = proc.communicate(timeout=2)
                print(f"Stdout: {stdout}")
                print(f"Stderr: {stderr}")
            except Exception:
                pass
            sys.exit(1)
            
        print("Server is healthy! Running tests...")
        
        # Test 1: PDF File (Simulated OCR)
        print("\n--- Test 1: PDF File ---")
        pdf_payload = make_pubsub_payload("invoice_998.pdf", "user-invoices-bucket", "application/pdf", 102450)
        status, response = send_post(local_url, pdf_payload)
        print(f"Status Code: {status}")
        print(f"Response: {response}")
        if status != 200 or response.get("status") != "success":
            raise RuntimeError("Test 1 Failed!")
            
        # Test 2: TXT File (Falls back to simulated OCR because bucket/file don't exist in actual GCS)
        print("\n--- Test 2: TXT File (Simulated Fallback) ---")
        txt_payload = make_pubsub_payload("report.txt", "user-invoices-bucket", "text/plain", 543)
        status, response = send_post(local_url, txt_payload)
        print(f"Status Code: {status}")
        print(f"Response: {response}")
        if status != 200 or response.get("status") != "success":
            raise RuntimeError("Test 2 Failed!")
            
        print("\nAll local integration tests passed successfully!")
        
    finally:
        print("Stopping FastAPI server...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            
if __name__ == "__main__":
    main()
