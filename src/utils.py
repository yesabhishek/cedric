import os
import platform
import subprocess
import time
import shutil


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
    activate_script = os.path.join(
        venv_path, "Scripts" if platform.system() == "Windows" else "bin", "activate"
    )

    # Use the "source" command on Linux/Mac or "call" on Windows to activate the virtual environment
    activate_command = (
        f"call {activate_script}"
        if platform.system() == "Windows"
        else f"source {activate_script}"
    )
    subprocess.run(activate_command, shell=True, check=True)

    manage_script = os.path.join(app_path, "manage.py")

    subprocess.run(["pip", "install", "django"], shell=True, check=True)
    subprocess.run(
        ["python", "manage.py", "startapp", "authentication"], shell=True, check=True
    )

    # Install Django Rest Framework (DRF)
    subprocess.run(
        [
            "pip",
            "install",
            "djangorestframework",
            "djangorestframework-simplejwt",
            "python-dotenv",
        ],
        shell=True,
        check=True,
    )

    # Update settings.py with DRF in INSTALLED_APPS
    with open(os.path.join(app_path, app_name, "settings.py"), "a") as settings_file:
        settings_file.write(
            "\nINSTALLED_APPS += ['rest_framework', 'rest_framework_simplejwt', 'authentication']"
        )

    with open(os.path.join(app_path, app_name, "settings.py"), "a") as settings_file:
        settings_file.write("\nAUTH_USER_MODEL = 'authentication.CustomUser'")

    # Update urls.py with DRF
    with open(os.path.join(app_path, app_name, "urls.py"), "a") as urls_file:
        urls_file.write(
            "\nfrom django.urls import include\nfrom rest_framework_simplejwt.views import (TokenObtainPairView,TokenRefreshView,)\n\nurlpatterns += [path('api-auth/', include('rest_framework.urls')),\
                        path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),                            \
                        path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), \
                        path('api/', include('authentication.urls')),]"
        )

    # Update requirements.txt
    subprocess.run(["pip", "freeze", ">", "requirements.txt"], shell=True, check=True)

    parent_directory = os.path.abspath(os.path.dirname(__file__))
    api_folder_path = os.path.join(app_path, "authentication", "api")
    os.makedirs(api_folder_path)

    # models.py
    with open(
        os.path.join(parent_directory, "authentication", "models.py"), "r"
    ) as models_file:
        models_file_content = models_file.read()
        with open(
            os.path.join(app_path, "authentication", "models.py"), "a+"
        ) as new_models_file:
            new_models_file.write(models_file_content)

    # serializers.py
    with open(
        os.path.join(parent_directory, "authentication","serializers.py"), "r"
    ) as serializers_file:
        serializers_file_content = serializers_file.read()
        with open(
            os.path.join(api_folder_path, "serializers.py"), "a+"
        ) as new_serializers_file:
            new_serializers_file.write(serializers_file_content)

    # views.py
    with open(
        os.path.join(parent_directory, "authentication",  "views.py"), "r"
    ) as views_file:
        views_file_content = views_file.read()
        with open(os.path.join(api_folder_path, "views.py"), "a+") as new_views_file:
            new_views_file.write(views_file_content)

    # urls.py
    with open(
        os.path.join(parent_directory, "authentication", "urls.py"), "r"
    ) as urls_file:
        urls_file_content = urls_file.read()
        with open(
            os.path.join(app_path, "authentication", "urls.py"), "a+"
        ) as new_urls_file:
            new_urls_file.write(urls_file_content)

    subprocess.run(["python", "manage.py", "makemigrations", "--noinput"], check=True)

    subprocess.run(["python", "manage.py", "migrate"], shell=True, check=True)
