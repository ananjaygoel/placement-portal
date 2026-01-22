from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import DecimalField, IntegerField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class StudentProfileForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=200)])
    degree = StringField("Degree", validators=[Optional(), Length(max=120)])
    department = StringField("Department", validators=[Optional(), Length(max=120)])
    graduation_year = IntegerField(
        "Graduation Year", validators=[Optional(), NumberRange(min=1900, max=2100)]
    )
    cgpa = DecimalField(
        "CGPA", places=2, validators=[Optional(), NumberRange(min=0, max=10)]
    )
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    skills = TextAreaField("Skills", validators=[Optional(), Length(max=2000)])
    resume = FileField("Resume (PDF)", validators=[Optional(), FileAllowed(["pdf"], "PDF only")])

    submit = SubmitField("Save Profile")

