# Root project directory

import os
def create_structure():
    root = "project"
    os.makedirs(root, exist_ok=True)

    # Create files in root
    files_root = [
        "main.py",
        "requirements.txt",
        ".env",
        "README.md"
    ]
    for file in files_root:
        with open(os.path.join(root, file), 'w', encoding='utf-8') as f:
            f.write("# This file is created. Add content here.\n")

    # Config directory
    config_dir = os.path.join(root, "config")
    os.makedirs(config_dir, exist_ok=True)
    with open(os.path.join(config_dir, "settings.py"), 'w', encoding='utf-8') as f:
        f.write("# Bot settings (e.g., BOT_TOKEN = 'your_token')\n")

    # Src directory
    src_dir = os.path.join(root, "src")
    os.makedirs(src_dir, exist_ok=True)

    # Handlers directory
    handlers_dir = os.path.join(src_dir, "handlers")
    os.makedirs(handlers_dir, exist_ok=True)
    with open(os.path.join(handlers_dir, "__init__.py"), 'w', encoding='utf-8') as f:
        f.write("from . import onboarding, profile  # Add other handlers\n")

    handlers_files = [
        "onboarding.py",
        "profile.py",
        "visa_card.py",
        "wallet.py",
        "orders.py",
        "support.py",
        "vip.py",
        "admin.py"
    ]
    for file in handlers_files:
        with open(os.path.join(handlers_dir, file), 'w', encoding='utf-8') as f:
            f.write(f"# Handler for {file[:-3]} module\n")

    # Utils directory
    utils_dir = os.path.join(src_dir, "utils")
    os.makedirs(utils_dir, exist_ok=True)
    with open(os.path.join(utils_dir, "__init__.py"), 'w', encoding='utf-8') as f:
        f.write("from .keyboards import *\n")

    utils_files = [
        "keyboards.py",
        "validators.py",
        "payments.py",
        "helpers.py"
    ]
    for file in utils_files:
        with open(os.path.join(utils_dir, file), 'w', encoding='utf-8') as f:
            f.write(f"# Utility for {file[:-3]}\n")

    # Database directory
    db_dir = os.path.join(src_dir, "database")
    os.makedirs(db_dir, exist_ok=True)
    with open(os.path.join(db_dir, "__init__.py"), 'w', encoding='utf-8') as f:
        f.write("from .models import *\nfrom .db_manager import *\n")

    db_files = [
        "models.py",
        "db_manager.py"
    ]
    for file in db_files:
        with open(os.path.join(db_dir, file), 'w', encoding='utf-8') as f:
            f.write(f"# Database {file[:-3]} module\n")

    # Tests directory (optional)
    tests_dir = os.path.join(root, "tests")
    os.makedirs(tests_dir, exist_ok=True)
    with open(os.path.join(tests_dir, "__init__.py"), 'w', encoding='utf-8') as f:
        f.write("# Tests directory\n")

    print(f"✅ Structure created successfully in '{root}/' directory!")
    print("Next: cd project && pip install -r requirements.txt")
