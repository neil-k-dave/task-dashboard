from PyQt5 import QtWidgets, QtCore, QtGui
import sys
from datetime import datetime, timedelta

class Task:
    def __init__(self, name, tmin, tmax):
        self.tmin = tmin
        self.tmax = tmax
        self.name = name
        self.last_updated = datetime.now()
        self.success_count = 0

    def time_since_last_update(self):
        return (datetime.now() - self.last_updated).total_seconds()

    def reset_task(self):
        self.last_updated = datetime.now()
        self.success_count += 1

class TaskButton(QtWidgets.QPushButton):
    
    delete_task_signal = QtCore.pyqtSignal(object)
    
    def __init__(self, task):
        super().__init__(task.name)
        self.task = task
        self.tmin = task.tmin
        self.tmax = task.tmax
        self.update_button_color()

    def update_button_color(self):
        # Calculate color based on time since last update
        time_diff = self.task.time_since_last_update()
        color_hex = calculate_color(time_diff,self.tmin,self.tmax)
        self.setStyleSheet(f"background-color: {color_hex}; color: white;")
        
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            # Emit the custom signal with the task as data when right-clicked
            self.delete_task_signal.emit(self.task)
        else:
            super().mousePressEvent(event)

def calculate_color(time_diff, min_time, max_time ): #3 * 24 * 60 * 60
    """
    Calculate a color that gradually changes from light green to red to black 
    based on the time elapsed since the task was last updated.
    """
    # Define RGB colors for light green, bright red, and black
    light_green = (144, 238, 144)  # Light green
    bright_red = (255, 0, 0)       # Bright red
    black = (0, 0, 0)              # Black
    
    if time_diff < min_time:
        # Return the initial color (light green) before min_time has passed
        return f'#{light_green[0]:02x}{light_green[1]:02x}{light_green[2]:02x}'
    
    # Clamp time_diff to max_time for consistent color scaling
    time_diff = min(time_diff - min_time, max_time - min_time)
   
    # Calculate the proportion of time elapsed
    proportion = time_diff / (max_time - min_time)

    # Decide if we are in the green-to-red phase or red-to-black phase
    if proportion < 0.5:
        # First half: Light green to bright red
        # Scale proportion within this range (0 to 1)
        scaled_proportion = proportion * 2
        r = int(light_green[0] + (bright_red[0] - light_green[0]) * scaled_proportion)
        g = int(light_green[1] + (bright_red[1] - light_green[1]) * scaled_proportion)
        b = int(light_green[2] + (bright_red[2] - light_green[2]) * scaled_proportion)
    else:
        # Second half: Bright red to black
        # Scale proportion within this range (0 to 1)
        scaled_proportion = (proportion - 0.5) * 2
        r = int(bright_red[0] + (black[0] - bright_red[0]) * scaled_proportion)
        g = int(bright_red[1] + (black[1] - bright_red[1]) * scaled_proportion)
        b = int(bright_red[2] + (black[2] - bright_red[2]) * scaled_proportion)

    # Convert RGB to hex format
    return f'#{r:02x}{g:02x}{b:02x}'

class TaskManagerApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QVBoxLayout()
        
        # Header
        self.header = QtWidgets.QLabel("Repeatable Task Manager")
        font = QtGui.QFont("Arial", 16, QtGui.QFont.Bold)
        self.header.setFont(font)
        layout.addWidget(self.header)

        # Task buttons
        self.task_buttons_layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.task_buttons_layout)
        
        # Add new task input and button
        self.new_task_input = QtWidgets.QLineEdit()
        self.new_task_input.setPlaceholderText("Enter new task name...")
        self.new_task_mintime = QtWidgets.QLineEdit()
        self.new_task_mintime.setPlaceholderText("Enter min...")
        self.new_task_maxtime = QtWidgets.QLineEdit()
        self.new_task_maxtime.setPlaceholderText("Enter max...")
        self.add_task_button = QtWidgets.QPushButton("Add Task")
        self.add_task_button.clicked.connect(self.add_task)
        add_task_layout = QtWidgets.QHBoxLayout()
        add_task_layout.addWidget(self.new_task_input)
        add_task_layout.addWidget(self.new_task_mintime)
        add_task_layout.addWidget(self.new_task_maxtime)
        add_task_layout.addWidget(self.add_task_button)
        layout.addLayout(add_task_layout)
        
        # Refresh timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_tasks)
        self.timer.start(1000)

        self.setLayout(layout)
        self.setWindowTitle("Task Manager")
        self.setGeometry(300, 300, 600, 600)

    def add_task(self):
        task_name = self.new_task_input.text()
        task_min = int(self.new_task_mintime.text())
        task_max = int(self.new_task_maxtime.text())

        if task_name and task_min < task_max:
            task = Task(task_name,task_min,task_max)
            self.tasks.append(task)
            task_button = TaskButton(task)
            task_button.clicked.connect(self.task_completed)
            task_button.delete_task_signal.connect(self.delete_task)
            self.task_buttons_layout.addWidget(task_button)
            self.new_task_input.clear()
            self.new_task_mintime.clear()
            self.new_task_maxtime.clear()

    def task_completed(self):
        button = self.sender()
        task = button.task
        task.reset_task()
        button.update_button_color()
        QtWidgets.QMessageBox.information(self, "Task Reset", f"{task.name} has been reset!\nSuccess Count: {task.success_count}")

    def delete_task(self, task):
         # Confirm deletion
         reply = QtWidgets.QMessageBox.question(self, "Delete Task",
                                                f"Are you sure you want to delete '{task.name}'?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
         if reply == QtWidgets.QMessageBox.Yes:
             # Find and remove the task from the list and layout
             self.tasks.remove(task)
             for i in range(self.task_buttons_layout.count()):
                 button = self.task_buttons_layout.itemAt(i).widget()
                 if button.task == task:
                     button.deleteLater()  # Remove button from the layout
                     self.task_buttons_layout.removeWidget(button)
                     break

    def update_tasks(self):
        # Update task statuses and button colors
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
