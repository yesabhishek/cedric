import argparse
import os
from shutil import copytree, rmtree
import inquirer
import re
from art import *
from pathlib import Path
from utils import *




def configure_django_app(app_name, use_drf, database):
    print(f"Configuring Django app with the following options:")
    print(f"App Name: {app_name}")
    print(f"Use DRF: {use_drf}")
    print(f"Database: {database}")

    # Create a new Django project
    os.system(f"django-admin startproject {app_name}")

    # Modify settings.py based on user choices
    settings_path = os.path.join(app_name, app_name, "settings.py")

    with open(settings_path, "r") as settings_file:
        content = settings_file.read()

    if use_drf == "Yes (Recommended)":
        create_django_app(app_name)
        return True


    if database == "Sqlite3":
        return True

    elif database == "Postgres":
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': app_name,
                'USER': app_name,
                'PASSWORD': '123cls4',
                'HOST': 'localhost',
                'PORT': '5432',
            }
        }

    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': app_name,
                'USER': app_name,
                'PASSWORD': '1234',
                'HOST': 'localhost',
                'PORT': '3306',
            }
        }

    # Use regular expressions to find and replace the DATABASES block
    pattern = re.compile(r'DATABASES\s*=\s*{[^}]+}\s*}', re.DOTALL)
    content = pattern.sub(f"DATABASES = {DATABASES}", content)

    with open(settings_path, "w") as settings_file:
        settings_file.write(content)



def main():
    Art=text2art("CEDRIC")
    print(Art)
    print(
        "🚀 Welcome to CEDRIC Django Template – because even coding wizards need a magic wand! 🧙\n\n"
        "#############################################################################################################################################\n"
        "# Your Django development journey is about to get as smooth as a salsa dancer on roller skates!                                             \n"
        "# Developed by: Abhishek Choudhury (Got so annoyed, decided to create his own helper library, but cool enough to share it with you! 😎)    \n"
        "# Get ready to soar through your coding adventure with a sprinkle of Python magic!\n#\n"
        "# Remember, bugs are just undocumented features waiting to be discovered! 🐞✨\n"
        "#############################################################################################################################################\n\n"
    )

    questions = [
        inquirer.Text(
            "app_name", message="What shall we call your magical application?"
        ),
        #inquirer.List(
        #    "use_docker",
        #    message="Are you ready to embark on a 🚢 Docker adventure?",
        #    choices=["Yes", "No"],
        #    default="Yes",
        #),
        inquirer.List(
            "use_drf",
            message="Shall we add Django DRF with JWT based APIs for authentication?\n (Note: This action will create a new app authentication in the django app, with a custom user model along with required fields like email, name, password)",
            choices=["Yes (Recommended)", "No"],
            default="Yes (Recommended)",
        ),
        #inquirer.List(
        #    "use_jwt",
        #    message="Shall we add JWT based authentication?",
        #    choices=["Yes (Recommended)", "No"],
        #    default="Yes (Recommended)",
        #),
        inquirer.List(
            "database",
            message="Select a Database for your coding kingdom",
            choices=["Postgres", "MySQL", "Sqlite3"],
            default="Postgres",
        ),
    ]

    answers = inquirer.prompt(questions)

    # Validate app name
    app_name = answers["app_name"]
    if not app_name or not app_name.isidentifier() or app_name[0].isdigit():
        print(
            "Error: Please provide a valid app name. It should be a valid Python identifier."
        )
        return

    # Confirm overwrite if the app directory already exists
    app_directory = os.path.join(os.getcwd(), app_name)
    if os.path.exists(app_directory):
        response = inquirer.confirm(
            f"The directory {app_name} already exists. Do you want to overwrite it?",
            default=True,
        )
        if not response:
            print("Aborting setup.")
            return
        else:
            rmtree(app_directory)

    configure_django_app(
        app_name,
        answers["use_drf"],
        answers["database"],
    )

    print("\n\nTa-da! Your Django app has been summoned successfully. 🚀✨ Now go forth and conjure some code magic!")


if __name__ == "__main__":
    main()
