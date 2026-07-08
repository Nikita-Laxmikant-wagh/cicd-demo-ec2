import os
import json
import paramiko

# Read configuration
with open("config.json", "r") as f:
    config = json.load(f)

remote_path = config["remote_path"]

# Read GitHub Secrets
host = os.environ["EC2_HOST"]
username = os.environ["EC2_USER"]
pem_data = os.environ["EC2_PEM"]

# Create key.pem from GitHub Secret
with open("key.pem", "w") as f:
    f.write(pem_data)

os.chmod("key.pem", 0o400)

# Connect to EC2
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect(
    hostname=host,
    username=username,
    key_filename="key.pem"
)

print("Connected to EC2")

# Upload files
sftp = ssh.open_sftp()

files = [
    "app.py",
    "requirements.txt"
]

for file in files:
    sftp.put(file, f"{remote_path}/{file}")
    print(f"Uploaded: {file}")

sftp.close()

# Install packages and restart Flask
commands = f"""
cd {remote_path}
source venv/bin/activate
pip install -r requirements.txt
pkill -f app.py || true
nohup python3 app.py > output.log 2>&1 &
"""

stdin, stdout, stderr = ssh.exec_command(commands)

print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()

print("Deployment Successful!")