import os
import platform
import subprocess
import time


def create_django_app(app_name):
    # Use os.path.join to join paths in a platform-independent way
    app_path = os.path.join(os.getcwd(), app_name)
    venv_path = os.path.join(app_path, "venv")
    
    # Create the app directory if it doesn't exist
    os.makedirs(app_path, exist_ok=True)

    # Move to the app directory
    os.chdir(app_path)

    # Use subprocess.run for running commands to capture the output and handle errors
    subprocess.run(["python", "-m", "venv", "venv"], shell=True, check=True)

    # Use os.path.join to create the path to the activate script
    activate_script = os.path.join(venv_path, "Scripts" if platform.system() == "Windows" else "bin", "activate")

    # Use the "source" command on Linux/Mac or "call" on Windows to activate the virtual environment
    activate_command = f"call {activate_script}" if platform.system() == "Windows" else f"source {activate_script}"
    subprocess.run(activate_command, shell=True, check=True)

    manage_script = os.path.join(app_path, "manage.py")

    subprocess.run(["pip", "install", "django"], shell=True, check=True)
    subprocess.run(["python", "manage.py", "startapp", "authentication"], shell=True, check=True)

    # Install Django Rest Framework (DRF)
    subprocess.run(["pip", "install", "djangorestframework"], shell=True, check=True)

    # Update settings.py with DRF in INSTALLED_APPS
    with open(os.path.join(app_path, app_name, "settings.py"), "a") as settings_file:
        settings_file.write("\nINSTALLED_APPS += ['rest_framework']")

    # Update urls.py with DRF
    with open(os.path.join(app_path, app_name, "urls.py"), "a") as urls_file:
        urls_file.write("\nfrom django.urls import include\n\nurlpatterns += [path('api-auth/', include('rest_framework.urls'))]")

    # Update requirements.txt
    subprocess.run(["pip", "freeze", ">", "requirements.txt"], shell=True, check=True)


def write_code_for_api():
    # TODO: create CustomerUser models in models.py, views.py API code for sign up, login, token, logout abd update urls.py in authentication app, add the app authentication in settings.py installed apps, and in urls.py, then finally run migrations
    pass


def install_jwt():
    # TODO: install drf package, update settings.py with installed apps, backend_model , update urls.py create/update requirements.txt inside django-project
    pass
