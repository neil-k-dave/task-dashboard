from PyQt5 import QtWidgets, QtCore, QtGui
import sys
from datetime import datetime, timedelta
import json

TASKS_FILE = "test.json"

class Task:
    def __init__(self, name, tmin, tmax, last_updated=None):
        self.name = name
        self.tmin = tmin
        self.tmax = tmax
        self.success_count = 0
        # Use current time if last_updated is None
        self.last_updated = last_updated if last_updated else datetime.now()

    def time_since_last_update(self):
        return (datetime.now() - self.last_updated).total_seconds()

    def reset_task(self):
        self.last_updated = datetime.now()
        self.success_count += 1

    def to_dict(self):
        """Convert task to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "tmin": self.tmin,
            "tmax": self.tmax,
            "success_count": self.success_count,
            "last_updated": self.last_updated.isoformat(),
        }

    @staticmethod
    def from_dict(data):
        """Create a Task object from a dictionary."""
        last_updated = datetime.fromisoformat(data["last_updated"])
        return Task(data["name"], data["tmin"], data["tmax"], last_updated)

class TaskButton(QtWidgets.QPushButton):
    delete_task_signal = QtCore.pyqtSignal(object)
    
    def __init__(self, task):
        super().__init__(task.name)
        self.task = task
        self.update_button_color()

    def update_button_color(self):
        time_diff = self.task.time_since_last_update()
        color_hex = calculate_color(time_diff, self.task.tmin, self.task.tmax)
        self.setStyleSheet(f"background-color: {color_hex}; color: white;")

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.delete_task_signal.emit(self.task)
        else:
            super().mousePressEvent(event)

def calculate_color(time_diff, min_time, max_time):
    light_green = (144, 238, 144)
    bright_red = (255, 0, 0)
    black = (0, 0, 0)
    
    if time_diff < min_time:
        return f'#{light_green[0]:02x}{light_green[1]:02x}{light_green[2]:02x}'
    
    time_diff = min(time_diff - min_time, max_time - min_time)
    proportion = time_diff / (max_time - min_time)
    
    if proportion < 0.5:
        scaled_proportion = proportion * 2
        r = int(light_green[0] + (bright_red[0] - light_green[0]) * scaled_proportion)
        g = int(light_green[1] + (bright_red[1] - light_green[1]) * scaled_proportion)
        b = int(light_green[2] + (bright_red[2] - light_green[2]) * scaled_proportion)
    else:
        scaled_proportion = (proportion - 0.5) * 2
        r = int(bright_red[0] + (black[0] - bright_red[0]) * scaled_proportion)
        g = int(bright_red[1] + (black[1] - bright_red[1]) * scaled_proportion)
        b = int(bright_red[2] + (black[2] - bright_red[2]) * scaled_proportion)

    return f'#{r:02x}{g:02x}{b:02x}'

class TaskManagerApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.load_tasks_json()
        self.initUI()

    def load_tasks_json(self):
        try:
            with open(TASKS_FILE, "r") as file:
                tasks_data = json.load(file)
                self.tasks = [Task.from_dict(data) for data in tasks_data]
        except (FileNotFoundError, json.JSONDecodeError):
            self.tasks = []

    def save_tasks_json(self):
        tasks_data = [task.to_dict() for task in self.tasks]
        with open(TASKS_FILE, "w") as file:
            json.dump(tasks_data, file, indent=4)

    def initUI(self):
        layout = QtWidgets.QVBoxLayout()
        
        self.header = QtWidgets.QLabel("Repeatable Task Manager")
        font = QtGui.QFont("Arial", 16, QtGui.QFont.Bold)
        self.header.setFont(font)
        layout.addWidget(self.header)

        self.task_buttons_layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.task_buttons_layout)
        
        self.new_task_input = QtWidgets.QLineEdit()
        self.new_task_input.setPlaceholderText("Enter new task name...")
        self.new_task_mintime = QtWidgets.QLineEdit()
        self.new_task_mintime.setPlaceholderText("Enter min...")
        self.new_task_maxtime = QtWidgets.QLineEdit()
        self.new_task_maxtime.setPlaceholderText("Enter max...")
        self.add_task_button = QtWidgets.QPushButton("Add Task")
        self.add_task_button.clicked.connect(self.add_task)

        for task in self.tasks:
            task_button = TaskButton(task)
            task_button.clicked.connect(self.task_completed)
            task_button.delete_task_signal.connect(self.delete_task)
            self.task_buttons_layout.addWidget(task_button)

        add_task_layout = QtWidgets.QHBoxLayout()
        add_task_layout.addWidget(self.new_task_input)
        add_task_layout.addWidget(self.new_task_mintime)
        add_task_layout.addWidget(self.new_task_maxtime)
        add_task_layout.addWidget(self.add_task_button)
        layout.addLayout(add_task_layout)
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_tasks)
        self.timer.start(1000)

        self.setLayout(layout)
        self.setWindowTitle("Task Manager")
        self.setGeometry(300, 300, 600, 600)

    def add_task(self):
        task_name = self.new_task_input.text()
        try:
            task_min = int(self.new_task_mintime.text())
            task_max = int(self.new_task_maxtime.text())
            if task_name and task_min < task_max:
                task = Task(task_name, task_min, task_max)
                self.tasks.append(task)
                self.save_tasks_json()
                task_button = TaskButton(task)
                task_button.clicked.connect(self.task_completed)
                task_button.delete_task_signal.connect(self.delete_task)
                self.task_buttons_layout.addWidget(task_button)
                self.new_task_input.clear()
                self.new_task_mintime.clear()
                self.new_task_maxtime.clear()
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Min and Max time must be integers.")

    def task_completed(self):
        button = self.sender()
        button.task.reset_task()
        button.update_button_color()
        self.save_tasks_json()
        QtWidgets.QMessageBox.information(self, "Task Reset", f"{button.task.name} has been reset!\nSuccess Count: {button.task.success_count}")

    def delete_task(self, task):
        reply = QtWidgets.QMessageBox.question(self, "Delete Task",
                                               f"Are you sure you want to delete '{task.name}'?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.tasks.remove(task)
            for i in range(self.task_buttons_layout.count()):
                button = self.task_buttons_layout.itemAt(i).widget()
                if button.task == task:
                    button.deleteLater()
                    self.task_buttons_layout.removeWidget(button)
                    self.save_tasks_json()
                    break

    def update_tasks(self):
        for i in range(self.task_buttons_layout.count()):
            button = self.task_buttons_layout.itemAt(i).widget()
            button.update_button_color()

def main():
    app = QtWidgets.QApplication(sys.argv)
    task_manager = TaskManagerApp()
    task_manager.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
