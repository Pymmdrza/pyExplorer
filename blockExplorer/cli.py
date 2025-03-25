import click
import subprocess
import os
import sys
from typing import Optional

@click.group()
def cli():
    """blockExplorer CLI tool"""
    pass

@cli.command()
@click.argument('mode', type=click.Choice(['local', 'docker']))
def install(mode: str):
    """Install prerequisites for local or docker deployment"""
    if mode == 'local':
        click.echo("Installing local dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            click.echo(click.style("✓ Local installation completed successfully!", fg="green"))
            click.echo("\nTo run the application, use:")
            click.echo(click.style("  blockExplorer run local", fg="blue"))
        except Exception as e:
            click.echo(click.style(f"Error during installation: {str(e)}", fg="red"))
            sys.exit(1)
    
    elif mode == 'docker':
        click.echo("Setting up Docker environment...")
        try:
            # Check if Docker is installed
            subprocess.check_call(["docker", "--version"], stdout=subprocess.DEVNULL)
            click.echo("✓ Docker is installed")
            
            # Check if docker-compose is installed
            subprocess.check_call(["docker-compose", "--version"], stdout=subprocess.DEVNULL)
            click.echo("✓ Docker Compose is installed")
            
            click.echo(click.style("\n✓ Docker setup completed successfully!", fg="green"))
            click.echo("\nTo run the application using Docker, use:")
            click.echo(click.style("  blockExplorer run docker", fg="blue"))
        except subprocess.CalledProcessError:
            click.echo(click.style("Error: Docker or Docker Compose is not installed.", fg="red"))
            click.echo("Please install Docker and Docker Compose first:")
            click.echo("https://docs.docker.com/get-docker/")
            sys.exit(1)
        except Exception as e:
            click.echo(click.style(f"Error during Docker setup: {str(e)}", fg="red"))
            sys.exit(1)

@cli.command()
@click.argument('mode', type=click.Choice(['local', 'docker']))
@click.option('--port', default=5000, help='Port to run the application on')
def run(mode: str, port: int):
    """Run the blockExplorer in local or docker mode"""
    if mode == 'local':
        click.echo(f"Starting blockExplorer locally on port {port}...")
        try:
            os.environ['FLASK_APP'] = 'app'
            subprocess.check_call([sys.executable, "-m", "flask", "run", "--host=0.0.0.0", f"--port={port}"])
        except Exception as e:
            click.echo(click.style(f"Error starting application: {str(e)}", fg="red"))
            sys.exit(1)
    
    elif mode == 'docker':
        click.echo("Starting blockExplorer using Docker...")
        try:
            subprocess.check_call(["docker-compose", "up", "--build"])
        except subprocess.CalledProcessError:
            click.echo(click.style("Error: Failed to start Docker containers.", fg="red"))
            click.echo("Make sure you've run 'blockExplorer install docker' first.")
            sys.exit(1)
        except Exception as e:
            click.echo(click.style(f"Error during Docker startup: {str(e)}", fg="red"))
            sys.exit(1)

@cli.command()
def help():
    click.echo(get_help())

def get_help():
    example = """
    blockExplorer install local
    blockExplorer install docker
    blockExplorer run local
    blockExplorer run docker
    """
    return example

def main():
    if len(sys.argv) < 2:
        click.echo(get_help())
        sys.exit(1)
    cli()




if __name__ == '__main__':
    main()
