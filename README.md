# 🦎Gecko - Django App Configuration Made Easy

## Overview

Gecko is a Python library designed to streamline the process of setting up a Django application. This library aims to save development time and simplify the configuration of a full-fledged Django project. By taking a few inputs from the user, Gecko automates the creation and configuration of a Django application, allowing developers to focus on building great features rather than spending time on the initial setup.

## Features

- **Interactive CLI:** Gecko provides an interactive command-line interface (CLI) that guides users through the configuration process with a series of well-defined questions.

- **Default Choices:** Gecko comes with sensible default choices for various configuration options, making the setup process quick and straightforward. Users can customize their choices based on project requirements.

- **Docker Integration:** Gecko supports the use of Docker, allowing developers to choose whether to include Docker in their project setup. The default choice is set to use Docker for enhanced development and deployment consistency.

- **Cloud Provider Options:** Users can select their preferred cloud provider from a list of popular choices, including AWS, GCP, Azure, Linode, or none if the application is not hosted on a specific cloud provider.

- **CSS Framework Selection:** Gecko includes options for selecting a CSS framework. TailwindCSS is set as the default choice, but users can opt for Bootstrap or choose not to include any CSS framework in their project.

- **Database Configuration:** Developers can choose their preferred database from a list that includes Postgres, MySQL, and Sqlite3. Sqlite3 is set as the default choice for simplicity, but users can easily select an alternative option.

## Getting Started

### Installation

To use Gecko, install the library using the following command:

```bash
pip install gecko
```

### Usage

1. Open your terminal and navigate to the desired directory where you want to create your Django project.

2. Run the following command to start the Gecko setup:

```bash
gecko setup
```

3. Answer the prompted questions to configure your Django application based on your preferences.

4. Once the setup is complete, Gecko will create and configure your Django project according to the provided choices.

## Example

Here's an example of how Gecko can be used:

```bash
gecko setup
```

Follow the interactive prompts to provide information about your application, such as the application name, whether to use Docker, your preferred cloud provider, CSS framework, and database.

## Contributing

Contributions are welcome! If you encounter issues or have suggestions for improvements, please open an issue or submit a pull request on the [Gecko GitHub repository](https://github.com/yesabhishek/gecko).

## License

This project is licensed under the GNU License - see the [LICENSE](LICENSE) file for details.

---

Happy coding with Gecko! 🦎✨