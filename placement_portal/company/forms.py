from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    DecimalField,
    IntegerField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError


class DriveForm(FlaskForm):
    job_title = StringField("Job Title", validators=[DataRequired(), Length(max=200)])
    job_description = TextAreaField("Job Description", validators=[DataRequired(), Length(max=10000)])
    eligibility_criteria = TextAreaField(
        "Eligibility Criteria", validators=[Optional(), Length(max=5000)]
    )
    required_skills = TextAreaField("Required Skills", validators=[Optional(), Length(max=5000)])

    min_cgpa = DecimalField(
        "Minimum CGPA", places=2, validators=[Optional(), NumberRange(min=0, max=10)]
    )
    salary_min = IntegerField("Salary Min (LPA)", validators=[Optional(), NumberRange(min=0)])
    salary_max = IntegerField("Salary Max (LPA)", validators=[Optional(), NumberRange(min=0)])
    location = StringField("Location", validators=[Optional(), Length(max=120)])
    min_experience_years = IntegerField(
        "Minimum Experience (Years)", validators=[Optional(), NumberRange(min=0, max=50)]
    )
    application_deadline = DateField("Application Deadline", validators=[Optional()])

    submit = SubmitField("Save")

    def validate_salary_max(self, field):
        if self.salary_min.data is not None and field.data is not None:
            if field.data < self.salary_min.data:
                raise ValidationError("Salary max must be greater than or equal to salary min.")

    def validate_application_deadline(self, field):
        if field.data is not None and field.data < date.today():
            raise ValidationError("Application deadline cannot be in the past.")
