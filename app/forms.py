from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, InputRequired


class QueryForm(FlaskForm):
    rp_name = StringField("RP Name: ")
    software_name = StringField("Software:")
    include = StringField("Include:")
    exclude = StringField("Exclude:")
    export_format = SelectField("Format:", choices=["CSV", "HTML", "JSON"])
    api_key = StringField("API Key: ", validators=[DataRequired()])
    regex = StringField("Regex: ")
    response = StringField("Response")
    submit = SubmitField("Submit")


class APIKeyForm(FlaskForm):
    length_max = 50

    def length(min=-1, max=-1):
        message = "Must be between %d and %d characters long." % (min, max)

        def _length(form, field):
            l = field.data and len(field.data) or 0
            if l < min or max != -1 and l > max:
                raise ValidationError(message)

        return _length

    first_name = StringField(
        "First Name: ", validators=[DataRequired(), length(max=length_max)]
    )
    last_name = StringField(
        "Last Name: ", validators=[InputRequired(), length(max=length_max)]
    )
    email = StringField(
        "Email Address: ", validators=[InputRequired(), length(max=length_max)]
    )
    organization = StringField(
        "Organization Name: ", validators=[InputRequired(), length(max=length_max)]
    )
    submit = SubmitField("Submit")
