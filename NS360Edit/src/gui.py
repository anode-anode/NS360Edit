#gui.py
from PyQt6.QtWidgets import (
    QFileDialog, QFormLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QWidget, QComboBox,
)

from filehandler import MWSave, SaveError
from carnames import resolve_car_name_360



class SaveGui(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NS360Edit")
        self.save_obj = None   # the loaded MWSave, or None

        self.layout = QFormLayout(self)
        self.layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.current_car = QComboBox(None)
        self.current_car.setEnabled(False)
        self.layout.addRow("Car:", self.current_car)

        self.bounty = QLineEdit("")
        self.money = QLineEdit("")
        self.file_path_label = QLabel("No file selected")

        self.file_button = QPushButton("Choose File")
        self.save_button = QPushButton("Save")
        self.save_button.setEnabled(False)      # until a file is loaded


        self.layout.addRow("Bounty:", self.bounty)
        self.layout.addRow("Money:", self.money)
        self.layout.addRow("File:", self.file_path_label)
        self.layout.addRow(self.file_button)
        self.layout.addRow(self.save_button)

        self.file_button.clicked.connect(self.choose_file)
        self.save_button.clicked.connect(self.save)
        self.current_car.currentIndexChanged.connect(self.refresh)


    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select a save file", "", "All Files (*)")
        if not path:                    # user pressed Cancel
            return
        try:
            self.save_obj = MWSave(path)
        except (SaveError, OSError) as e:
            QMessageBox.warning(self, "Can't open file", str(e))
            return

        self.file_path_label.setText(self.short_path(path))
        self.fill_cars()
        self.refresh()
        self.save_button.setEnabled(True)

    def refresh(self):
        """Show the values for the loaded file and the selected car."""
        if self.save_obj is None:
            self.bounty.setText("")
            self.money.setText("")
            return
        try:
            self.money.setText(f"{self.save_obj.get_money()}")
            slot = self.current_car.currentData()
            self.bounty.setText("" if slot is None else f"{self.save_obj.get_bounty(slot):,}")
        except SaveError as e:
            self.bounty.setText("?")
            self.money.setText("?")
            QMessageBox.warning(self, "Unexpected save layout", str(e))

    def fill_cars(self, select_slot=None):
        """Rebuild the car list. Keeps `select_slot` selected if given, else the current car."""
        self.current_car.blockSignals(True)
        self.current_car.clear()

        chosen_row = 0
        for row, car in enumerate(self.save_obj.get_cars()):
            name = resolve_car_name_360(car["signature"]) or car["signature"][:8]
            text = f"Slot {car['career_slot']} - {name} - {car['bounty']:,}"
            if car["active"]:
                text += " (current car)"
                if select_slot is None:
                    chosen_row = row
            if car["career_slot"] == select_slot:
                chosen_row = row
            self.current_car.addItem(text, car["career_slot"])

        self.current_car.setCurrentIndex(chosen_row)
        self.current_car.blockSignals(False)
        self.current_car.setEnabled(self.current_car.count() > 0)

    def save(self):
        if self.save_obj is None:
            return
        try:
            self.save_obj.set_bounty(self.bounty.text(), entry=self.current_car.currentData())
            self.save_obj.set_money(self.money.text())

        except SaveError as e:
            QMessageBox.warning(self, "Invalid bounty", str(e))
            return

        out_path, _ = QFileDialog.getSaveFileName(self, "Save edited file as", self.save_obj.path + "_edited")
        if not out_path:
            return
        try:
            self.save_obj.save(out_path)
        except (SaveError, OSError) as e:
            QMessageBox.warning(self, "Couldn't save", str(e))
            return
        slot = self.current_car.currentData()
        self.fill_cars(select_slot=slot)
        self.refresh()
        QMessageBox.information(self, "Saved", f"Wrote {out_path}")

    def short_path(self, file_path):
        """make a shortened file path for UI display"""
        chars = [*file_path]
        nest_idx = [i for i, char in enumerate(chars) if char == "/"]
        shortpath = ("".join(["...", *chars[nest_idx[-2]:]]))

        return shortpath








