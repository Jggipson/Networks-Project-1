import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, \
    QToolBar, QLineEdit, QPushButton
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl


# Define the browser window using PyQt6's main window class.
class MainWindow(QMainWindow):
    def __init__(self):
        # Initialize the parent QMainWindow class.
        super().__init__()

        # Create the browser view, load the starting page,
        # and make it the main content of the window.
        self.view = QWebEngineView()
        self.view.setUrl(QUrl("https://www.tarleton.edu"))
        self.setCentralWidget(self.view)

        # Add a toolbar to hold the browser controls.
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Connect the reload button's clicked signal to the
        # browser's reload method so clicking refreshes the page.
        reload_button = QPushButton("↻")
        reload_button.clicked.connect(self.view.reload)
        toolbar.addWidget(reload_button)

        # Create an address bar that loads the entered URL
        # when the user presses Enter.
        self.address_bar = QLineEdit()
        self.address_bar.returnPressed.connect(self.load_url)
        toolbar.addWidget(self.address_bar)

        # Set the initial window size in pixels and display it.
        self.resize(1200, 800)
        self.show()

        # Update the window title and address bar when the
        # browser reports a change to the page title or URL.
        self.view.titleChanged.connect(self.setWindowTitle)
        self.view.urlChanged.connect(self.url_changed)

    def load_url(self):
        # Read the address entered by the user.
        url = self.address_bar.text()

        # Default to HTTP if the address does not start with "http".
        if not url.startswith("http"):
            url = "http://" + url

        # Convert the address to a Qt URL object and load the page.
        self.view.setUrl(QUrl(url))

    def url_changed(self, url):
        # Show the current URL in the address bar, including
        # changes caused by following links or redirects.
        self.address_bar.setText(url.toString())


# Start the application only when this file is run directly.
if __name__ == "__main__":
    # Create the Qt application and pass in command-line arguments.
    app = QApplication(sys.argv)
    window = MainWindow()

    # Run the event loop to handle user input and browser events.
    # Return Qt's exit code when the application finishes.
    sys.exit(app.exec())
