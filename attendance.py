class AttendanceSystem:
    def __init__(self, df):
        # =========================
        # 🧹 CLEAN DATA
        # =========================
        df.columns = df.columns.str.strip()

        # normalize Registration No
        if "Registration No" in df.columns:
            df["Registration No"] = df["Registration No"].astype(str).str.strip()

        # normalize Faculty Name
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
    def student_view(self, uen):
        uen = str(uen).strip()

        result = self.df[self.df["Registration No"] == uen]

        if result.empty:
            return "No attendance found for this student."

        return self.format_output(result)

    # =========================
    # 👪 PARENT VIEW
    # =========================
    def parent_view(self, child_uen):
        return self.student_view(child_uen)

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
            return "No attendance records found for this teacher."

        return self.format_output(result)

    # =========================
    # 📦 FORMAT OUTPUT (IMPORTANT)
    # =========================
    def format_output(self, df):
        """
        Cleaner output for chatbot (instead of raw table dump)
        """
        try:
            output = []

            for _, row in df.iterrows():
                line = []

                if "Student Name" in df.columns:
                    line.append(f"Name: {row.get('Student Name', '')}")

                if "Registration No" in df.columns:
                    line.append(f"Reg No: {row.get('Registration No', '')}")

                if "Attendance %" in df.columns:
                    line.append(f"Attendance: {row.get('Attendance %', '')}%")

                output.append(" | ".join(line))

            return "\n".join(output)

        except:
            # fallback
            return df.to_string(index=False)