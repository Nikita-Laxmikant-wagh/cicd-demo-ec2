import os
import json
import paramiko
import time

# -----------------------------
# Read configuration
# -----------------------------
with open("config.json", "r") as f:
    config = json.load(f)

remote_path = config["remote_path"]


# -----------------------------
# GitHub Secrets
# -----------------------------
host = os.environ["EC2_HOST"]
username = os.environ["EC2_USER"]
pem_data = os.environ["EC2_PEM"]


# -----------------------------
# Create PEM file
# -----------------------------
with open("key.pem", "w") as f:
    f.write(pem_data)

os.chmod("key.pem", 0o400)


# -----------------------------
# Connect EC2
# -----------------------------
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect(
    hostname=host,
    username=username,
    key_filename="key.pem"
)

print("✅ Connected to EC2")


# -----------------------------
# Upload files
# -----------------------------
sftp = ssh.open_sftp()

files = [
    "app.py",
    "requirements.txt"
]

for file in files:
    local_file = file
    remote_file = f"{remote_path}/{file}"

    sftp.put(local_file, remote_file)

    print(f"✅ Uploaded {file}")


sftp.close()


# -----------------------------
# Deployment commands
# -----------------------------
commands = f"""
cd {remote_path}

echo "🚀 Starting deployment"

# Activate virtual environment
source venv/bin/activate


# Install requirements
pip install -r requirements.txt


# Stop old Flask application
pkill -f "python3 app.py" || true


# Wait for process to stop
sleep 3


# Start Flask application
nohup python3 app.py > output.log 2>&1 &


# Wait for startup
sleep 5


echo "--------- PROCESS ---------"
ps -ef | grep app.py


echo "--------- LOGS ---------"
cat output.log

"""


stdin, stdout, stderr = ssh.exec_command(commands)


print("\n========== SERVER OUTPUT ==========")

print(stdout.read().decode())


print("\n========== SERVER ERRORS ==========")

print(stderr.read().decode())


ssh.close()

print("\n🎉 Deployment Successful!")