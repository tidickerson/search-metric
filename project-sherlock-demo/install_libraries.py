import subprocess
import sys

def install_requirements():
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("All libraries installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while installing libraries: {e}")

if __name__ == "__main__":
    install_requirements()