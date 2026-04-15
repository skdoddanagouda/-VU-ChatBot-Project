import pandas as pd
import os

class StudentDataManager:
    def __init__(self, data_root="backend/data"):
        self.data_root = data_root
        self.master_file = os.path.join(data_root, "VidyashilaUniversity_SemII_Dataset.xlsx")
        self.faculty_file = os.path.join(data_root, "Facyalty map.xlsx")
        self.timetable_file = os.path.join(data_root, "Timetable Sem-II_11-01-2026 updated.xlsx")

    def get_student_info(self, uen):
        """Returns student master info based on Registration No (UEN)."""
        try:
            df = pd.read_excel(self.master_file, sheet_name="Students Master")
            student = df[df["Registration No"].str.strip() == uen.strip()]
            if not student.empty:
                return student.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"Error fetching student info: {e}")
            return None

    def get_attendance(self, uen):
        """Returns attendance summary for a student."""
        try:
            df = pd.read_excel(self.master_file, sheet_name="Attendance Summary")
            attendance = df[df["Registration No"].str.strip() == uen.strip()]
            if not attendance.empty:
                # Return multiple rows for different courses
                return attendance.to_dict(orient="records")
            return []
        except Exception as e:
            print(f"Error fetching attendance: {e}")
            return []

    def get_faculty_info(self, section=None, program=None):
        """Returns faculty and classroom details."""
        try:
            df = pd.read_excel(self.faculty_file)
            if section:
                df = df[df["Section"].astype(str).str.contains(str(section), na=False)]
            elif program:
                df = df[df["Program"].astype(str).str.contains(str(program), na=False)]
            
            return df.to_dict(orient="records")
        except Exception as e:
            print(f"Error fetching faculty info: {e}")
            return []

    def get_timetable(self, section, semester):
        """Returns timetable info (currently returning confirmation of lookup)."""
        # Note: Timetable Excel often has complex layouts. Returning summary for now.
        try:
            xl = pd.ExcelFile(self.timetable_file)
            normalized_section = str(section).lower().replace('-', ' ')
            for sheet in xl.sheet_names:
                normalized_sheet = sheet.lower().replace('-', ' ')
                if normalized_section in normalized_sheet:
                    target_sheet = sheet
                    break
            
            if target_sheet:
                df = pd.read_excel(self.timetable_file, sheet_name=target_sheet)
                return {"sheet": target_sheet, "data": df.head(10).to_dict()}
            return None
        except Exception as e:
            print(f"Error fetching timetable: {e}")
            return None

# Initialize global manager
db_manager = StudentDataManager()