#!/usr/bin/env python3
"""
CURSOR END OF SESSION - Shared Context System
Writes to .ai-context/ for both Cursor and Claude synchronization
"""

import os
import json
import subprocess
import psutil
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Paths
RAPID_STUDIO = Path.home() / "rapid-studio"
CURSOR_CLAUDE = Path.home() / "cursor-claude-github"
SHARED_CONTEXT_DIR = RAPID_STUDIO / ".ai-context"
SESSIONS_DIR = SHARED_CONTEXT_DIR / "sessions"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def run_command(cmd, cwd=None):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def get_git_status(repo_path):
    """Get comprehensive git status"""
    if not repo_path.exists():
        return {"error": f"Repository not found: {repo_path}"}
    
    status = {
        "branch": run_command("git rev-parse --abbrev-ref HEAD", repo_path),
        "last_commit": run_command("git log -1 --oneline", repo_path),
        "uncommitted_changes": run_command("git status --short", repo_path),
        "total_commits_today": run_command(
            f"git log --since='midnight' --oneline | wc -l",
            repo_path
        ),
        "remote_url": run_command("git remote get-url origin", repo_path),
        "last_commit_hash": run_command("git rev-parse HEAD", repo_path),
        "commit_count": run_command("git rev-list --count HEAD", repo_path)
    }
    return status

def get_system_info():
    """Get system information"""
    return {
        "hostname": os.uname().nodename,
        "platform": os.uname().sysname,
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "disk_usage": psutil.disk_usage('/').percent,
        "current_user": os.getenv('USER', 'unknown')
    }

def get_recent_changes():
    """Get recent file changes and git activity"""
    changes = {
        "files_modified": [],
        "files_created": [],
        "files_deleted": [],
        "git_commits": [],
        "commands_executed": []
    }
    
    # Get git diff for both repositories
    for repo_name, repo_path in [("rapid-studio", RAPID_STUDIO), ("cursor-claude-github", CURSOR_CLAUDE)]:
        if repo_path.exists():
            # Get modified files
            modified = run_command("git diff --name-only", repo_path)
            if modified:
                changes["files_modified"].extend([f"{repo_name}/{f}" for f in modified.split('\n') if f])
            
            # Get untracked files
            untracked = run_command("git ls-files --others --exclude-standard", repo_path)
            if untracked:
                changes["files_created"].extend([f"{repo_name}/{f}" for f in untracked.split('\n') if f])
            
            # Get recent commits
            recent_commits = run_command("git log --since='1 hour ago' --oneline", repo_path)
            if recent_commits:
                changes["git_commits"].extend([f"{repo_name}: {commit}" for commit in recent_commits.split('\n') if commit])
    
    return changes

def get_services_status():
    """Get status of running services"""
    services = {
        "docker_containers": [],
        "node_processes": [],
        "python_processes": [],
        "other_services": []
    }
    
    try:
        # Get Docker containers
        docker_ps = run_command("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
        if docker_ps and "NAMES" in docker_ps:
            services["docker_containers"] = [line for line in docker_ps.split('\n')[1:] if line.strip()]
    except:
        pass
    
    try:
        # Get Node processes
        node_procs = run_command("ps aux | grep node | grep -v grep")
        if node_procs:
            services["node_processes"] = [line.strip() for line in node_procs.split('\n') if line.strip()]
    except:
        pass
    
    try:
        # Get Python processes
        python_procs = run_command("ps aux | grep python | grep -v grep")
        if python_procs:
            services["python_processes"] = [line.strip() for line in python_procs.split('\n') if line.strip()]
    except:
        pass
    
    return services

def create_cursor_session_summary():
    """Create Cursor's session summary for shared context"""
    print_section("💻 CREATING CURSOR SESSION SUMMARY")
    
    timestamp = datetime.now()
    session_id = f"cursor_{timestamp.strftime('%Y%m%d_%H%M%S')}"
    
    # Gather comprehensive information
    summary = {
        "agent": "cursor",
        "session_id": session_id,
        "timestamp": timestamp.isoformat(),
        "date": timestamp.strftime("%Y-%m-%d"),
        "time": timestamp.strftime("%H:%M:%S"),
        "repositories": {
            "rapid-studio": get_git_status(RAPID_STUDIO),
            "cursor-claude-github": get_git_status(CURSOR_CLAUDE)
        },
        "system_info": get_system_info(),
        "recent_changes": get_recent_changes(),
        "services_status": get_services_status(),
        "session_metadata": {
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "environment_variables": {
                "PATH": os.getenv('PATH', '')[:200] + "..." if len(os.getenv('PATH', '')) > 200 else os.getenv('PATH', ''),
                "HOME": os.getenv('HOME', ''),
                "USER": os.getenv('USER', '')
            }
        }
    }
    
    return summary, session_id

def create_cursor_last_session_md(summary, session_id):
    """Create Cursor's last session markdown file"""
    print_section("📝 CREATING CURSOR LAST SESSION MARKDOWN")
    
    # Create sessions directory
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    cursor_file = SHARED_CONTEXT_DIR / "CURSOR_LAST_SESSION.md"
    
    content = f"""# Cursor Session End
**Timestamp:** {summary['timestamp']}
**Session ID:** {session_id}

## Changes Made:
- **Modified files:** {', '.join(summary['recent_changes']['files_modified']) if summary['recent_changes']['files_modified'] else 'None'}
- **Created files:** {', '.join(summary['recent_changes']['files_created']) if summary['recent_changes']['files_created'] else 'None'}
- **Deleted files:** {', '.join(summary['recent_changes']['files_deleted']) if summary['recent_changes']['files_deleted'] else 'None'}

## Git Commits:
{chr(10).join(f"- {commit}" for commit in summary['recent_changes']['git_commits']) if summary['recent_changes']['git_commits'] else "- No recent commits"}

## Commands Executed:
{chr(10).join(f"- {cmd}" for cmd in summary['recent_changes']['commands_executed']) if summary['recent_changes']['commands_executed'] else "- No commands recorded"}

## Current Project State:
- **Services running:** {len(summary['services_status']['docker_containers'])} Docker containers, {len(summary['services_status']['node_processes'])} Node processes, {len(summary['services_status']['python_processes'])} Python processes
- **Tests passing:** [To be filled by Cursor during session]
- **Build status:** [To be filled by Cursor during session]
- **Deployment status:** [To be filled by Cursor during session]

## Issues Encountered:
- [To be filled by Cursor during session]

## Next Actions Needed:
- [To be filled by Cursor during session]

## Current Project State:
- **Rapid Studio Branch:** {summary['repositories']['rapid-studio'].get('branch', 'Unknown')}
- **Rapid Studio Last Commit:** {summary['repositories']['rapid-studio'].get('last_commit', 'Unknown')}
- **Cursor-Claude Branch:** {summary['repositories']['cursor-claude-github'].get('branch', 'Unknown')}
- **Cursor-Claude Last Commit:** {summary['repositories']['cursor-claude-github'].get('last_commit', 'Unknown')}

## System Information:
- **Hostname:** {summary['system_info']['hostname']}
- **Platform:** {summary['system_info']['platform']}
- **CPU Cores:** {summary['system_info']['cpu_count']}
- **Memory:** {summary['system_info']['memory_total'] / (1024**3):.1f} GB
- **Disk Usage:** {summary['system_info']['disk_usage']:.1f}%

## Services Status:
### Docker Containers:
{chr(10).join(f"- {container}" for container in summary['services_status']['docker_containers']) if summary['services_status']['docker_containers'] else "- No Docker containers running"}

### Node Processes:
{chr(10).join(f"- {proc}" for proc in summary['services_status']['node_processes'][:3]) if summary['services_status']['node_processes'] else "- No Node processes running"}

### Python Processes:
{chr(10).join(f"- {proc}" for proc in summary['services_status']['python_processes'][:3]) if summary['services_status']['python_processes'] else "- No Python processes running"}

## Files Changed:
```json
{json.dumps(summary['recent_changes'], indent=2)}
```

---

**🎯 Cursor session {session_id} completed - Context preserved for Claude synchronization! 🎯**
"""
    
    with open(cursor_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Cursor last session file created: {cursor_file}")
    return cursor_file

def create_cursor_session_json(summary, session_id):
    """Create Cursor's session JSON file"""
    print_section("💾 CREATING CURSOR SESSION JSON")
    
    json_file = SESSIONS_DIR / f"{session_id}.json"
    
    # Prepare JSON data
    json_data = {
        "agent": "cursor",
        "timestamp": summary['timestamp'],
        "session_id": session_id,
        "changes": {
            "files_modified": summary['recent_changes']['files_modified'],
            "files_created": summary['recent_changes']['files_created'],
            "files_deleted": summary['recent_changes']['files_deleted'],
            "git_commits": summary['recent_changes']['git_commits'],
            "commands_executed": summary['recent_changes']['commands_executed']
        },
        "state": {
            "repositories": summary['repositories'],
            "system_info": summary['system_info'],
            "services_running": {
                "docker_containers": summary['services_status']['docker_containers'],
                "node_processes": summary['services_status']['node_processes'],
                "python_processes": summary['services_status']['python_processes']
            },
            "tests_status": "unknown",  # To be filled by testing
            "build_status": "unknown",   # To be filled by build system
            "deployment_status": "unknown"  # To be filled by deployment
        },
        "issues_encountered": [],
        "next_actions": []
    }
    
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"✅ Cursor session JSON created: {json_file}")
    return json_file

def update_shared_state(summary, session_id):
    """Update the shared state JSON file"""
    print_section("🔄 UPDATING SHARED STATE")
    
    shared_state_file = SHARED_CONTEXT_DIR / "SHARED_STATE.json"
    
    # Try to load existing state
    existing_state = {}
    if shared_state_file.exists():
        try:
            with open(shared_state_file, 'r') as f:
                existing_state = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load existing shared state: {e}")
    
    # Update with Cursor's session
    shared_state = {
        "last_updated": summary['timestamp'],
        "cursor_session": session_id,
        "claude_session": existing_state.get("claude_session", "none"),
        "project_state": {
            "services_running": summary['services_status']['docker_containers'] + summary['services_status']['node_processes'] + summary['services_status']['python_processes'],
            "tests_status": "unknown",  # To be filled by testing
            "build_status": "unknown",   # To be filled by build system
            "deployment_status": "unknown"  # To be filled by deployment
        },
        "next_actions": {
            "cursor": [],
            "claude": existing_state.get("next_actions", {}).get("claude", []),
            "user": existing_state.get("next_actions", {}).get("user", [])
        },
        "files_changed": {
            "modified": summary['recent_changes']['files_modified'],
            "created": summary['recent_changes']['files_created'],
            "deleted": summary['recent_changes']['files_deleted']
        },
        "system_info": summary['system_info'],
        "repositories": summary['repositories']
    }
    
    with open(shared_state_file, 'w') as f:
        json.dump(shared_state, f, indent=2)
    
    print(f"✅ Shared state updated: {shared_state_file}")
    return shared_state_file

def update_master_status(summary, session_id):
    """Update the master status file with Cursor's section"""
    print_section("📊 UPDATING MASTER STATUS")
    
    master_status_file = SHARED_CONTEXT_DIR / "MASTER_STATUS.md"
    
    # Try to load existing master status
    existing_content = ""
    if master_status_file.exists():
        try:
            with open(master_status_file, 'r') as f:
                existing_content = f.read()
        except Exception as e:
            print(f"Warning: Could not load existing master status: {e}")
    
    # Create Cursor's section
    cursor_section = f"""## 💻 Cursor's Last Session
**Session ID:** {session_id}  
**Timestamp:** {summary['timestamp']}

### Changes Made:
- **Modified files:** {', '.join(summary['recent_changes']['files_modified']) if summary['recent_changes']['files_modified'] else 'None'}
- **Created files:** {', '.join(summary['recent_changes']['files_created']) if summary['recent_changes']['files_created'] else 'None'}
- **Deleted files:** {', '.join(summary['recent_changes']['files_deleted']) if summary['recent_changes']['files_deleted'] else 'None'}

### Git Commits:
{chr(10).join(f"- {commit}" for commit in summary['recent_changes']['git_commits']) if summary['recent_changes']['git_commits'] else "- No recent commits"}

### Current Project State:
- **Services running:** {len(summary['services_status']['docker_containers'])} Docker containers, {len(summary['services_status']['node_processes'])} Node processes, {len(summary['services_status']['python_processes'])} Python processes
- **Tests passing:** [To be filled by Cursor during session]
- **Build status:** [To be filled by Cursor during session]
- **Deployment status:** [To be filled by Cursor during session]

### Issues Encountered:
- [To be filled by Cursor during session]

### Next Actions Needed:
- [To be filled by Cursor during session]

---

"""
    
    # If file exists, try to update Cursor's section
    if existing_content and "## 💻 Cursor's Last Session" in existing_content:
        # Replace existing Cursor section
        import re
        pattern = r"## 💻 Cursor's Last Session.*?(?=---|\Z)"
        updated_content = re.sub(pattern, cursor_section.strip(), existing_content, flags=re.DOTALL)
    else:
        # Add Cursor section to existing content
        updated_content = existing_content + "\n" + cursor_section
    
    # Ensure we have a proper header
    if not updated_content.startswith("# Rapid Studio - Master Status"):
        header = f"""# Rapid Studio - Master Status

**Last Updated:** {summary['timestamp']}  
**Cursor Session:** {session_id}  
**Claude Session:** [To be updated by Claude]

---

"""
        updated_content = header + updated_content
    
    with open(master_status_file, 'w') as f:
        f.write(updated_content)
    
    print(f"✅ Master status updated: {master_status_file}")
    return master_status_file

def main():
    """Main execution"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        CURSOR END OF SESSION - SHARED CONTEXT SYSTEM        ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Create Cursor session summary
        summary, session_id = create_cursor_session_summary()
        
        # Create Cursor's last session markdown
        cursor_md = create_cursor_last_session_md(summary, session_id)
        
        # Create Cursor's session JSON
        cursor_json = create_cursor_session_json(summary, session_id)
        
        # Update shared state
        shared_state = update_shared_state(summary, session_id)
        
        # Update master status
        master_status = update_master_status(summary, session_id)
        
        print_section("✅ CURSOR SHARED CONTEXT SESSION COMPLETE")
        print(f"""
🎯 Cursor session context preserved for Claude synchronization!

📁 Files created/updated:
   • CURSOR_LAST_SESSION.md (Cursor's session summary)
   • sessions/{session_id}.json (detailed session data)
   • SHARED_STATE.json (machine-readable state)
   • MASTER_STATUS.md (unified status)

🔄 For Claude: Read .ai-context/CURSOR_LAST_SESSION.md to see what Cursor implemented
🔄 For Cursor: Read .ai-context/CLAUDE_LAST_SESSION.md to see what Claude discussed

👋 Cursor session {session_id} ended with shared context preserved!
        """)
        
    except Exception as e:
        print(f"\n❌ Error during Cursor shared context session end: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
