from cli import CliApp


def main():
    # Initialize the app and run it:
    app: CliApp = CliApp(app_name="compress-py")
    app.run()


if __name__ == '__main__':
    main()
