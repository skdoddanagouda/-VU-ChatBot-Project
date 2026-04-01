class TimetableSystem:
    def __init__(self, df):
        # =========================
        # 🧹 CLEAN DATA
        # =========================
        df.columns = df.columns.str.strip()

        # normalize values safely
        if "Semester" in df.columns:
            df["Semester"] = df["Semester"].astype(str).str.strip()

        if "Section" in df.columns:
            df["Section"] = df["Section"].astype(str).str.strip()

        if "Faculty Name" in df.columns:
            df["Faculty Name"] = (
                df["Faculty Name"]
                .astype(str)
                .str.strip()
                .str.lower()
            )

        self.df = df

    # =========================
    # 👨‍🎓 STUDENT VIEW
    # =========================
    def student_view(self, semester, section):
        semester = str(semester).strip()
        section = str(section).strip()

        result = self.df[
            (self.df["Semester"] == semester) &
            (self.df["Section"] == section)
        ]

        if result.empty:
            return "No timetable found for this class."

        return self.format_output(result)

    # =========================
    # 👨‍🏫 TEACHER VIEW
    # =========================
    def teacher_view(self, teacher_name):
        teacher_name = teacher_name.strip().lower()

        if "Faculty Name" not in self.df.columns:
            return "Teacher data not available."

        result = self.df[
            self.df["Faculty Name"].str.contains(teacher_name, na=False)
        ]

        if result.empty:
            return "No classes found for this teacher."

        return self.format_output(result)

    # =========================
    # 👪 PARENT VIEW
    # =========================
    def parent_view(self, semester, section):
        return self.student_view(semester, section)

    # =========================
    # 📦 FORMAT OUTPUT (IMPORTANT)
    # =========================
    def format_output(self, df):
        """
        Clean chatbot-friendly timetable output
        """
        try:
            output = []

            for _, row in df.iterrows():
                line = []

                if "Day" in df.columns:
                    line.append(f"Day: {row.get('Day', '')}")

                if "Time" in df.columns:
                    line.append(f"Time: {row.get('Time', '')}")

                if "Subject" in df.columns:
                    line.append(f"Subject: {row.get('Subject', '')}")

                if "Faculty Name" in df.columns:
                    line.append(f"Faculty: {row.get('Faculty Name', '')}")

                output.append(" | ".join(line))

            return "\n".join(output)

        except:
            # fallback if anything fails
            return df.to_string(index=False)