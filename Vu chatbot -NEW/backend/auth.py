import os
import pandas as pd

class AuthSystem:
    def __init__(self):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # ✅ Point to backend/
        DATA_FILE = os.path.join(BASE_DIR, "data", "VidyashilaUniversity_SemII_Dataset.xlsx")

        try:
            # Load students from Students Master sheet
            self.students = pd.read_excel(DATA_FILE, sheet_name="Students Master")
            # Load faculty from Faculty Map sheet
            self.faculty = pd.read_excel(DATA_FILE, sheet_name="Faculty Map")

            print("[OK] Auth data loaded")

        except Exception as e:
            print("[ERROR] Error loading auth data:", e)
            self.students = pd.DataFrame()
            self.faculty = pd.DataFrame()

    def login(self, uen):
        uen = str(uen).strip()

        # =========================
        # 👨‍🎓 STUDENT LOGIN
        # =========================
        student = self.students[
            self.students["Registration No"].astype(str) == uen
        ]

        if not student.empty:
            s = student.iloc[0]

            return {
                "role": "student",
                "name": str(s.get("Student Name", "")),
                "semester": str(s.get("Semester", "")),
                "section": str(s.get("Section", "")),
                "uen": str(s.get("Registration No", ""))
            }

        # =========================
        # 👨‍🏫 TEACHER LOGIN
        # (by name OR ID if present)
        # =========================
        teacher = self.faculty[
            (self.faculty["Faculty Name"].astype(str) == uen) |
            (self.faculty.get("Faculty ID", pd.Series()).astype(str) == uen)
        ]

        if not teacher.empty:
            t = teacher.iloc[0]

            return {
                "role": "teacher",
                "name": str(t.get("Faculty Name", ""))
            }

        # =========================
        # ❌ NOT FOUND
        # =========================
        return None