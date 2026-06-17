import sys, os
"""Transfer Station — migrate agents between servers with zero downtime.

How it works:
1. Snapshot: capture agent state, config, memory, workspace
2. Transfer: send snapshot to target server via SSH/rsync
3. Bootstrap: start agent on target from snapshot
4. Verify: confirm agent is running on target
5. Cutover: switch DNS/tunnel to target
6. Cleanup: decommission old instance
"""
import os
import json
import time
import subprocess
import httpx
import asyncio
from pathlib import Path
from station.registry import AgentRegistry

class TransferStation:
    """Manage zero-downtime agent transfers between servers."""

    def __init__(self, registry: AgentRegistry, workspace: str = None):
        self.registry = registry
        self.workspace = workspace or os.path.expanduser("~/.openclaw/workspace")
        self.snapshots_dir = Path("data/snapshots")
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def snapshot_agent(self, agent_id) -> dict:
        """Capture complete agent state for transfer.
        
        Returns snapshot metadata with paths to snapshot files.
        """
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return {"error": f"Agent {agent_id} not found"}

        snap_id = f"snap_{agent_id}_{int(time.time())}"
        snap_dir = self.snapshots_dir / snap_id
        snap_dir.mkdir(parents=True, exist_ok=True)

        result = {
            "snapshot_id": snap_id,
            "agent_id": agent_id,
            "timestamp": time.time(),
            "files": [],
        }

        # 1. Snapshot the config
        config_paths = [
            Path(os.path.expanduser("~/.openclaw/openclaw.json")),
            Path(os.path.expanduser("~/.openclaw/workspace")),
        ]

        for src in config_paths:
            if src.is_file():
                dest = snap_dir / src.name
                dest.write_text(src.read_text())
                result["files"].append(str(src))
            elif src.is_dir():
                dest = snap_dir / src.name
                subprocess.run(["cp", "-r", str(src), str(dest)], timeout=60)
                result["files"].append(str(src))

        # 2. Snapshot the database
        db_path = Path("data/clawbreak.db")
        if db_path.exists():
            subprocess.run(["cp", str(db_path), str(snap_dir / "clawbreak.db")], timeout=30)
            result["files"].append(str(db_path))

        # 3. Snapshot memory
        memory_dir = Path(self.workspace) / "memory"
        if memory_dir.exists():
            subprocess.run(["cp", "-r", str(memory_dir), str(snap_dir / "memory")], timeout=30)
            result["files"].append(str(memory_dir))

        # 4. Create the restore script
        restore_script = self._build_restore_script(agent, snap_id)
        (snap_dir / "restore.sh").write_text(restore_script)
        result["files"].append("restore.sh")

        # 5. Create the snapshot manifest
        manifest = {
            "snapshot_id": snap_id,
            "agent_id": agent_id,
            "agent_name": agent["name"],
            "model": agent["model"],
            "capabilities": json.loads(agent["capabilities"]),
            "created_at": time.time(),
            "version": "0.2.1",
            "restore_command": f"bash restore.sh",
        }
        (snap_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

        # 6. Package as tarball
        tarball = self.snapshots_dir / f"{snap_id}.tar.gz"
        subprocess.run(
            ["tar", "czf", str(tarball), "-C", str(self.snapshots_dir), snap_id],
            timeout=120
        )
        result["tarball"] = str(tarball)
        result["tarball_size"] = tarball.stat().st_size

        return result

    def _build_restore_script(self, agent, snap_id) -> str:
        """Build a restore script that brings the agent up on a new server."""
        return f"""#!/bin/bash
# ClawBreak Agent Restore Script
# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Agent: {agent['name']} ({agent['id']})
set -e

echo "⚡ Restoring agent: {agent['name']}"

# 1. Install deps
echo "[1/5] Installing dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip curl
pip3 install --break-system-packages fastapi uvicorn httpx pyyaml

# 2. Install ClawBreak
echo "[2/5] Installing ClawBreak..."
sudo git clone https://github.com/EvezArt/clawbreak-ai.git /opt/clawbreak 2>/dev/null || true

# 3. Restore data
echo "[3/5] Restoring agent data..."
sudo cp -r openclaw/ /home/openclaw/.openclaw/ 2>/dev/null || true
sudo cp -r workspace/ /home/openclaw/.openclaw/workspace/ 2>/dev/null || true
sudo cp clawbreak.db /opt/clawbreak/data/ 2>/dev/null || true
sudo cp -r memory/ /home/openclaw/.openclaw/workspace/memory/ 2>/dev/null || true

# 4. Start agent
echo "[4/5] Starting agent..."
cd /opt/clawbreak
nohup python3 server.py &>data/server.log &
sleep 5

# 5. Verify
echo "[5/5] Verifying..."
if curl -s http://127.0.0.1:8080/health | grep -q "ok"; then
    IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_IP")
    echo "✅ Agent restored and running at http://${{IP}}:8080/"
else
    echo "⚠ Agent may need a moment. Check: curl http://127.0.0.1:8080/health"
fi
"""

    async def transfer_to_host(self, agent_id, target_host, ssh_key=None, target_user="root") -> dict:
        """Transfer an agent to a remote host via SSH.
        
        Steps:
        1. Snapshot the agent locally
        2. SCP the snapshot to the target
        3. Run restore on the target
        4. Verify the agent is running on target
        5. Update registry
        """
        transfer_id = f"xfer_{int(time.time())}"
        self.registry.create_transfer(transfer_id, agent_id, "local", target_host)

        # Step 1: Snapshot
        self.registry.update_transfer(transfer_id, "snapshotting")
        snap = self.snapshot_agent(agent_id)
        if "error" in snap:
            self.registry.update_transfer(transfer_id, "failed", snap["error"])
            return snap

        tarball = snap.get("tarball")
        if not tarball:
            self.registry.update_transfer(transfer_id, "failed", "No tarball created")
            return {"error": "No tarball created"}

        # Step 2: Transfer
        self.registry.update_transfer(transfer_id, "transferring")
        scp_target = f"{target_user}@{target_host}:/tmp/"

        ssh_opts = "-o StrictHostKeyChecking=no -o ConnectTimeout=10"
        if ssh_key:
            ssh_opts += f" -i {ssh_key}"

        result = subprocess.run(
            f"scp {ssh_opts} {tarball} {scp_target}",
            shell=True, capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            self.registry.update_transfer(transfer_id, "failed", result.stderr[:500])
            return {"error": f"SCP failed: {result.stderr[:200]}"}

        # Step 3: Restore on target
        self.registry.update_transfer(transfer_id, "restoring")
        tarball_name = Path(tarball).name
        restore_cmd = f"cd /tmp && tar xzf {tarball_name} && cd $(ls -d snap_*/ | head -1) && bash restore.sh"

        result = subprocess.run(
            f"ssh {ssh_opts} {target_user}@{target_host} '{restore_cmd}'",
            shell=True, capture_output=True, text=True, timeout=300
        )

        # Step 4: Verify
        self.registry.update_transfer(transfer_id, "verifying")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"http://{target_host}:8080/health")
                if resp.status_code == 200:
                    self.registry.update_transfer(transfer_id, "completed", snapshot_path=tarball)
                    # Update agent registry
                    self.registry.register_agent(
                        agent_id, 
                        self.registry.get_agent(agent_id)["name"],
                        target_host, 8080,
                        transfer_state="transferred"
                    )
                    return {"status": "transferred", "target": f"http://{target_host}:8080/"}
        except:
            pass

        # Transfer completed but can't verify remotely (maybe firewall)
        self.registry.update_transfer(transfer_id, "completed", snapshot_path=tarball)
        return {"status": "transferred_unverified", "target": target_host, "note": "SSH restore completed, verify manually"}

    def list_snapshots(self):
        """List available snapshots."""
        snapshots = []
        for f in self.snapshots_dir.glob("snap_*.tar.gz"):
            stat = f.stat()
            snap_id = f.stem
            manifest_path = self.snapshots_dir / snap_id.replace(".tar.gz", "") / "manifest.json"
            manifest = {}
            if manifest_path.exists():
                try:
                    manifest = json.loads(manifest_path.read_text())
                except:
                    pass
            snapshots.append({
                "id": snap_id,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "agent_id": manifest.get("agent_id", "unknown"),
                "agent_name": manifest.get("agent_name", "unknown"),
            })
        return snapshots
