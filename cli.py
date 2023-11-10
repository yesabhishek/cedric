import argparse
import os
from shutil import copytree, rmtree
import inquirer
from art import *


def configure_django_app(app_name, use_docker, cloud_provider, css_framework, database):
    print(f"Configuring Django app with the following options:")
    print(f"App Name: {app_name}")
    print(f"Use Docker: {use_docker}")
    print(f"Cloud Provider: {cloud_provider}")
    print(f"CSS Framework: {css_framework}")
    print(f"Database: {database}")

    # Create a new Django project
    os.system(f"django-admin startproject {app_name}")

    # Modify settings.py based on user choices
    settings_path = os.path.join(app_name, app_name, "settings.py")
    with open(settings_path, "a") as settings_file:
        settings_file.write(f"\n# Custom Configuration\n")
        settings_file.write(f"USE_DOCKER = {use_docker}\n")
        settings_file.write(f"CLOUD_PROVIDER = '{cloud_provider}'\n")
        settings_file.write(f"CSS_FRAMEWORK = '{css_framework}'\n")
        settings_file.write(f"DATABASE_ENGINE = '{database.lower()}'\n")


def main():
    tprint("GECKO", font="rnd-large")
    print(
        "🚀 Welcome to GECKO Django Template – because even coding wizards need a magic wand! 🧙\n\n"
        "Your Django development journey is about to get as smooth as a salsa dancer on roller skates!\n\n"
        "Developed by: Abhishek Choudhury (Annoyed enough to create his own helper library, but cool enough to share it with you! 😎)\n\n"
        "Get ready to soar through your coding adventure with a sprinkle of Python magic!\n\n"
        "Remember, bugs are just undocumented features waiting to be discovered! 🐞✨\n\n"
    )

    questions = [
        inquirer.Text(
            "app_name", message="What shall we call your magical application?"
        ),
        inquirer.List(
            "use_docker",
            message="Are you ready to embark on a Docker adventure?",
            choices=["Yes, lets set sail!", "No, I prefer to stay on land."],
            default="Yes, lets set sail!",
        ),
        inquirer.List(
            "cloud_provider",
            message="Pick a cloud, any cloud! (Or none)",
            choices=["AWS", "GCP", "Azure", "Linode", "None"],
            default="AWS",
        ),
        inquirer.List(
            "css_framework",
            message="Choose your style: Fashionable, Bootstraped, or None at all?",
            choices=["TailwindCSS", "Bootstrap", "None"],
            default="TailwindCSS",
        ),
        inquirer.List(
            "database",
            message="Select a Database for your coding kingdom",
            choices=["Postgres", "MySQL", "Sqlite3"],
            default="Sqlite3",
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

    # Configure Django app
    configure_django_app(
        app_name,
        answers["use_docker"],
        answers["cloud_provider"],
        answers["css_framework"],
        answers["database"],
    )

    print("\n\nTa-da! Your Django app has been summoned successfully. 🚀✨ Now go forth and conjure some code magic!")


if __name__ == "__main__":
    main()
