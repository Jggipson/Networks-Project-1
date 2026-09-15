import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, \
    QToolBar, QLineEdit, QPushButton
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl


# Define the browser window using PyQt6's main window class.
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create the browser view and make it the central widget.
        self.view = QWebEngineView()
        self.view.setUrl(QUrl("https://www.tarleton.edu"))
        self.setCentralWidget(self.view)

        # Add a toolbar to hold browser controls.
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Connect reload button to browser refresh.
        reload_button = QPushButton("↻")
        reload_button.clicked.connect(self.view.reload)
        toolbar.addWidget(reload_button)

        # Create address bar.
        self.address_bar = QLineEdit()
        self.address_bar.returnPressed.connect(self.load_url)
        toolbar.addWidget(self.address_bar)

        self.resize(1200, 800)
        self.show()

        self.view.titleChanged.connect(self.setWindowTitle)
        self.view.urlChanged.connect(self.url_changed)

    def load_url(self):
        url = self.address_bar.text()
        if not url.startswith("http"):
            url = "http://" + url
        self.view.setUrl(QUrl(url))

    def url_changed(self, url):
        self.address_bar.setText(url.toString())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
