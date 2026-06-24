import os

# Define the folder structure
folders = [
    os.path.join("data", "raw"),
    os.path.join("data", "processed"),
    os.path.join("models", "trained"),
    os.path.join("models", "src"),
    "notebooks",
    "src",
    os.path.join("static", "css"),
    os.path.join("static", "js"),
    "tests",
]

print("Initializing Fraud Detection System Project Directory Structure...")

for folder in folders:
    os.makedirs(folder, exist_ok=True)
    # Create a .gitkeep file to ensure empty directories are tracked by git
    gitkeep_path = os.path.join(folder, ".gitkeep")
    with open(gitkeep_path, "w") as f:
        f.write("")
    print(f"  [Created] {folder}/")

print("\nProject workspace directories initialized successfully!")
