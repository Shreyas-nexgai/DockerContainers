import os
import subprocess
import sys 
def run_command(command, check=True, capture_output=False):

    try:
        result = subprocess.run(
            command,
            check=check,
            capture_output=capture_output,
            text=True 
        )
        if capture_output:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(command)}", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        if capture_output:
            print(f"STDOUT: {e.stdout}", file=sys.stderr)
            print(f"STDERR: {e.stderr}", file=sys.stderr)
        if check: 
             raise
        return e 
    except FileNotFoundError as e:
        print(f"Error: Command not found - {command[0]}. Is Docker installed and in PATH?", file=sys.stderr)
        print(f"Error details: {e}", file=sys.stderr)
        if check:
            raise
        return e


def remove_existing_container(container_name):
    """Stops and removes a Docker container if it exists."""
    print(f"Checking for existing container '{container_name}'...")
    # Stop the container (ignore errors if it doesn't exist or isn't running)
    run_command(["docker", "stop", container_name], check=False)
    # Remove the container (ignore errors if it doesn't exist)
    run_command(["docker", "rm", container_name], check=False)
    print(f"Finished removing existing container (if any): {container_name}")


def start_container(container_name):
    if container_name == "sql":
        remove_existing_container("sql")
        remove_existing_container("pgadmin-container") 

        docker_sql_pull_command = ["docker", "pull", "postgres"]
        docker_sql_start_command = ["docker", "run", "--name", "sql", "-e", "POSTGRES_PASSWORD=marviniscool", "-p", "5432:5432", "-d", "postgres"]
        run_command(docker_sql_pull_command, check=True)
        run_command(docker_sql_start_command, check=True)
        print("PostgreSQL container 'sql' started.")

        docker_pgadmin_pull_command = ["docker", "pull", "dpage/pgadmin4"]
        docker_pgadmin_start_command = ["docker", "run", "--name", "pgadmin-container", "-p", "5050:80", "-e", "PGADMIN_DEFAULT_EMAIL=user@domain.com", "-e", "PGADMIN_DEFAULT_PASSWORD=catsarecool", "-d", "dpage/pgadmin4"]
        run_command(docker_pgadmin_pull_command, check=True)
        run_command(docker_pgadmin_start_command, check=True)
        print("pgAdmin container 'pgadmin-container' started.")

    elif container_name == "weaviate": 
        base_path = os.path.dirname(os.path.abspath(__file__)) # Corrected base path
        container_path = os.path.join(base_path, "containers", container_name) # Assuming subfolder 'containers'
        docker_compose_path = os.path.join(container_path, "docker-compose.yml")

        if not os.path.exists(docker_compose_path):
             # **CRITICAL**: Address the original 'weaviate' error path here
             print(f"Error: 'docker-compose.yml' not found in expected path: '{docker_compose_path}'", file=sys.stderr)
             # Decide how to handle: raise error, skip, etc.
             # raise FileNotFoundError(f"'docker-compose.yml' not found in '{container_path}'")
             print(f"Skipping Weaviate setup due to missing docker-compose.yml.", file=sys.stderr)
             return # Exit this function call for weaviate

        # Optionally run 'down' first to remove containers defined in the compose file
        print(f"Attempting to stop/remove existing Weaviate services defined in {docker_compose_path}...")
        docker_compose_down_command = ["docker", "compose", "-f", docker_compose_path, "down"]
        run_command(docker_compose_down_command, check=False) # Don't fail if nothing is running

        # Now run 'up'
        docker_compose_up_command = ["docker", "compose", "-f", docker_compose_path, "up", "-d", "--build"]

        run_command(docker_compose_up_command, check=True)
        print(f"Weaviate services started via docker-compose: {docker_compose_path}")

    else:
         print(f"Warning: Unknown container type '{container_name}'. No action taken.")


if __name__ == "__main__":
    containers = ["weaviate","sql"]
    print("Starting container setup...")
    for container in containers:
        try:
            start_container(container)
        except Exception as e:
            print(f"ERROR: Failed processing container '{container}': {e}", file=sys.stderr)
    print("Container setup finished.")