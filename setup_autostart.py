"""
Windows auto-start setup for Bluesky Twitch Live Bot.
Creates a Windows Task Scheduler task to run the bot at startup.
"""

import os
import sys
import subprocess
import json
from pathlib import Path


class AutoStartSetupError(Exception):
    """Raised when there's an issue setting up auto-start."""
    pass


def get_python_executable() -> str:
    """Get the full path to the Python executable."""
    return sys.executable


def get_script_directory() -> str:
    """Get the directory where this script is located."""
    return str(Path(__file__).parent.absolute())


def get_main_script_path() -> str:
    """Get the full path to main.py."""
    script_dir = get_script_directory()
    main_path = os.path.join(script_dir, "main.py")
    
    if not os.path.exists(main_path):
        raise AutoStartSetupError(f"main.py not found at {main_path}")
    
    return main_path


def create_task_xml(task_name: str, python_exe: str, script_path: str, script_dir: str) -> str:
    """
    Create Windows Task Scheduler XML configuration.
    
    Args:
        task_name: Name of the task
        python_exe: Path to Python executable
        script_path: Path to main.py
        script_dir: Working directory
        
    Returns:
        XML configuration as string
    """
    xml_template = '''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2024-01-01T00:00:00</Date>
    <Author>Bluesky Twitch Live Bot</Author>
    <Description>Automatically post to Bluesky when going live on Twitch</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Delay>PT30S</Delay>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{user_id}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{python_exe}</Command>
      <Arguments>"{script_path}"</Arguments>
      <WorkingDirectory>{script_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
    
    # Get current user
    import getpass
    current_user = getpass.getuser()
    
    return xml_template.format(
        user_id=current_user,
        python_exe=python_exe,
        script_path=script_path,
        script_dir=script_dir
    )


def check_admin_privileges() -> bool:
    """Check if running with administrator privileges."""
    try:
        # Try to access a system directory that requires admin rights
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def create_scheduled_task(task_name: str = "BlueSkyTwitchBot") -> None:
    """
    Create a Windows scheduled task to run the bot at startup.
    
    Args:
        task_name: Name for the scheduled task
    """
    print(f"Setting up auto-start for '{task_name}'...")
    
    # Get paths
    python_exe = get_python_executable()
    script_path = get_main_script_path()
    script_dir = get_script_directory()
    
    print(f"Python executable: {python_exe}")
    print(f"Script path: {script_path}")
    print(f"Working directory: {script_dir}")
    
    # Create XML configuration
    xml_config = create_task_xml(task_name, python_exe, script_path, script_dir)
    
    # Save XML to temporary file
    xml_file = os.path.join(script_dir, f"{task_name}_task.xml")
    try:
        with open(xml_file, 'w', encoding='utf-16') as f:
            f.write(xml_config)
        
        print(f"Created task configuration: {xml_file}")
        
        # Create the scheduled task using schtasks command
        cmd = [
            "schtasks",
            "/create",
            "/tn", task_name,
            "/xml", xml_file,
            "/f"  # Force overwrite if exists
        ]
        
        print("Creating scheduled task...")
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully created scheduled task '{task_name}'")
            print("The bot will now start automatically when Windows boots!")
        else:
            print(f"❌ Failed to create scheduled task: {result.stderr}")
            raise AutoStartSetupError(f"schtasks failed with code {result.returncode}: {result.stderr}")
    
    finally:
        # Clean up temporary XML file
        if os.path.exists(xml_file):
            os.remove(xml_file)


def remove_scheduled_task(task_name: str = "BlueSkyTwitchBot") -> None:
    """
    Remove the scheduled task.
    
    Args:
        task_name: Name of the scheduled task to remove
    """
    print(f"Removing scheduled task '{task_name}'...")
    
    cmd = ["schtasks", "/delete", "/tn", task_name, "/f"]
    
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    
    if result.returncode == 0:
        print(f"✅ Successfully removed scheduled task '{task_name}'")
    else:
        print(f"❌ Failed to remove scheduled task: {result.stderr}")


def check_task_exists(task_name: str = "BlueSkyTwitchBot") -> bool:
    """
    Check if the scheduled task exists.
    
    Args:
        task_name: Name of the scheduled task
        
    Returns:
        True if task exists, False otherwise
    """
    cmd = ["schtasks", "/query", "/tn", task_name]
    
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.returncode == 0


def create_batch_file() -> None:
    """Create a batch file for easy manual execution."""
    script_dir = get_script_directory()
    python_exe = get_python_executable()
    main_script = get_main_script_path()
    
    batch_content = f'''@echo off
echo Starting Bluesky Twitch Live Bot...
cd /d "{script_dir}"
"{python_exe}" "{main_script}"
pause
'''
    
    batch_file = os.path.join(script_dir, "run_bot.bat")
    
    with open(batch_file, 'w') as f:
        f.write(batch_content)
    
    print(f"✅ Created batch file: {batch_file}")
    print("You can double-click this file to run the bot manually")


def check_configuration() -> bool:
    """Check if configuration file exists."""
    script_dir = get_script_directory()
    config_file = os.path.join(script_dir, "config.json")
    
    if not os.path.exists(config_file):
        print("❌ config.json not found!")
        print("Please create your configuration file first:")
        print("1. Run: python main.py --create-config")
        print("2. Copy config.example.json to config.json")
        print("3. Fill in your Twitch and Bluesky credentials")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Check for placeholder values
        placeholders = ["your_twitch_username", "your_twitch_client_id", "your-app-password"]
        
        config_str = json.dumps(config)
        for placeholder in placeholders:
            if placeholder in config_str:
                print(f"❌ Configuration contains placeholder value: {placeholder}")
                print("Please update config.json with your actual credentials")
                return False
        
        print("✅ Configuration file looks good")
        return True
        
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return False


def main():
    """Main setup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup auto-start for Bluesky Twitch Live Bot")
    parser.add_argument("--remove", action="store_true", help="Remove the scheduled task")
    parser.add_argument("--check", action="store_true", help="Check if task exists")
    parser.add_argument("--task-name", default="BlueSkyTwitchBot", help="Name for the scheduled task")
    
    args = parser.parse_args()
    
    try:
        if args.check:
            exists = check_task_exists(args.task_name)
            if exists:
                print(f"✅ Scheduled task '{args.task_name}' exists")
            else:
                print(f"❌ Scheduled task '{args.task_name}' does not exist")
            return
        
        if args.remove:
            remove_scheduled_task(args.task_name)
            return
        
        # Setup auto-start
        print("🚀 Setting up auto-start for Bluesky Twitch Live Bot")
        print("=" * 50)
        
        # Check configuration
        if not check_configuration():
            print("\nPlease fix configuration issues before setting up auto-start")
            return
        
        # Check if we need admin privileges (we don't for user tasks)
        print("ℹ️  This will create a user-level scheduled task (no admin required)")
        
        # Create batch file
        create_batch_file()
        
        # Create scheduled task
        create_scheduled_task(args.task_name)
        
        print("\n✅ Setup complete!")
        print(f"The bot will start automatically when you log into Windows")
        print(f"To manage the task, search for 'Task Scheduler' in Windows")
        print(f"To remove auto-start, run: python {__file__} --remove")
        
    except AutoStartSetupError as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 