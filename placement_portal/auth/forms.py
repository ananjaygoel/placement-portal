from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    DecimalField,
    IntegerField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import Email, EqualTo, Length, NumberRange, Optional, DataRequired


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    submit = SubmitField("Login")


class StudentRegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )

    student_uid = StringField("Student ID / Roll No", validators=[DataRequired(), Length(max=50)])
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=200)])
    degree = StringField("Degree", validators=[Optional(), Length(max=120)])
    department = StringField("Department", validators=[Optional(), Length(max=120)])
    graduation_year = IntegerField(
        "Graduation Year", validators=[Optional(), NumberRange(min=1900, max=2100)]
    )
    cgpa = DecimalField(
        "CGPA", places=2, rounding=None, validators=[Optional(), NumberRange(min=0, max=10)]
    )
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    skills = TextAreaField("Skills", validators=[Optional(), Length(max=2000)])
    resume = FileField("Resume (PDF)", validators=[Optional(), FileAllowed(["pdf"], "PDF only")])

    submit = SubmitField("Create Student Account")


class CompanyRegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )

    company_name = StringField("Company Name", validators=[DataRequired(), Length(max=200)])
    industry = StringField("Industry", validators=[Optional(), Length(max=120)])
    hr_name = StringField("HR Contact Name", validators=[Optional(), Length(max=120)])
    hr_email = StringField("HR Contact Email", validators=[Optional(), Email(), Length(max=255)])
    hr_phone = StringField("HR Contact Phone", validators=[Optional(), Length(max=30)])
    website = StringField("Website", validators=[Optional(), Length(max=255)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=4000)])

    submit = SubmitField("Register Company (Needs Admin Approval)")

