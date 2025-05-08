import secrets
import json, csv, io
from collections import OrderedDict
from flask import render_template, request, make_response, flash, jsonify
from app import app
from app.forms import QueryForm, APIKeyForm
from core.models.software import Software
from core.models.rps import RPS
from core.models import db_proxy as db, use_db


############
### HOME ###
############
@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html", title="Home")


########################
### API Instructions ###
########################
@app.route("/api_0_instructions")
def api_0_instructions():
    return render_template("api_0_instructions.html", title="API 0 Instructions")

@app.route("/api_0_1_instructions")
def api_0_1_instructions():
    return render_template("api_0_1_instructions.html", title="API0.1 Instructions")

###########
### API ###
###########
@app.route("/API", methods=["GET", "POST"])
def API():
    # Create Form
    form = QueryForm()

    # Populate 'RP Name' Field
    rps_list = []
    # TODO: Will have to reimplement this once we have software data by RP
    #   resource groups
    with use_db("view"):
        query = RPS.select()
        for rp in query:
            rps_list.append(rp.rp_group_id)

    # Populate 'Software Name' Field
    softwares = []
    with use_db("view"):
        query = Software.select()
        for software in query:
            # Truncate Software Name Length
            # Look into how to fix this for API calls before I can implement
            # software.software_name = software.software_name[:21] +
            #   (software.software_name[21:] and '...')
            softwares.append(software.software_name)

    results = None
    results_json = None

    is_output_json = False
    is_output_csv = False
    is_output_html = False

    if form.validate_on_submit():
        print(request.form["export_format"])
        try:
            # Prepare Query
            rp_query = request.form["rp_name"]
            software_query = request.form["software_name"]
            include_raw = request.form["include"]
            if include_raw:
                include_raw = json.loads(include_raw)
            include_query = [
                col["value"].lower().replace(" ", "_") for col in include_raw
            ]

            exclude_raw = request.form["exclude"]
            if exclude_raw:
                exclude_raw = json.loads(exclude_raw)
            exclude_query = [
                col["value"].lower().replace(" ", "_") for col in exclude_raw
            ]

            export_format_raw = request.form["export_format"]
            if export_format_raw:
                export_format_raw = json.loads(export_format_raw)
            export_format_query = [
                col["value"].lower().replace(" ", "_") for col in export_format_raw
            ]

            is_output_json = "json" in export_format_query
            is_output_csv = "csv" in export_format_query
            is_output_html = "html" in export_format_query

            # results = request.form['response']
            # print(results)

            # Execute Query
            # results, error = execute_query(software_query, include_query,
            #   exclude_query)
            # results_json = json.dumps(results, indent=4)

            flash("Your query has been sent!")
            print("Success!")
        except:
            print("Error!")
        return jsonify(
            {"json": is_output_json, "csv": is_output_csv, "html": is_output_html}
        )

    print(is_output_json)

    return render_template(
        "api.html",
        title="API",
        form=form,
        results=results,
        results_json=results_json,
        json=is_output_json,
        csv=is_output_csv,
        html=is_output_html,
        rps_list=rps_list,
        softwares=softwares,
    )


###############
### EXPORTS ###
###############
@app.route("/export/json", methods=["POST"])
def export_json():
    query_results = request.form.get("json_results")
    if not query_results:
        return "No Data to export", 400
    print("QR: " + query_results)

    response = make_response(query_results)
    response.headers["Content-Disposition"] = "attachment; filename=results.json"
    response.headers["Content-type"] = "application/json"
    return response


@app.route("/export/csv", methods=["POST"])
def export_csv():
    query_results = request.form.get("csv_results")

    if not query_results:
        return "No Data to Export", 400

    try:
        # Parse JSON data
        data = json.loads(query_results)
    except json.JSONDecodeError:
        return "Invalid JSON data", 400

    # Check if the data is a single dictionary
    # If so, wrap into a List
    if isinstance(data, dict):
        data = [data]

    # Ensure the Data is a List of Dictionaries
    if not data or not isinstance(data, list):
        print(f"Error: Data is not a list. Data: {data}")
        return "Malformed data", 400

    for row in data:
        if not isinstance(row, dict):
            print(f"Error: Row in data is not a dictionary. Row: {row}")
            return "Malformed data", 400

    # Create CSV output
    output = io.StringIO()
    fieldnames = data[0].keys() if data else []
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    output.seek(0)

    # Create and return the response as a CSV file
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=results.csv"
    response.headers["Content-type"] = "text/csv"
    return response


@app.route("/export/html", methods=["POST"])
def export_html():
    # Retrieve the JSON data from the request
    # Make sure this matches the input name in the form
    html_results = request.form.get("html_results")
    if html_results:
        try:
            # Optionally parse JSON to verify it's valid
            json_data = json.loads(html_results, object_pairs_hook=OrderedDict)

            # Convert back to a formatted JSON string with indentation
            formatted_json = json.dumps(json_data, indent=2)

            # Create HTML content using a template or generate dynamically
            # Assume 'export_template.html' is an HTML file that
            #   knows how to display the data in a nice format
            html_content = render_template("__results_HTML.html", data=formatted_json)

            # Send the generated HTML as a response that opens in a new tab
            response = make_response(html_content)
            response.headers["Content-Type"] = "text/html"
            return response
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format"}), 400
    else:
        return jsonify({"error": "No HTML results provided"}), 400


###############################
# Helper Function for Exports #
###############################
def execute_query(software, include, exclude):
    # Executes the given SQL query and returns the results as a
    #   list of dictionaries.
    with use_db("view"):
        try:
            results = []
            if isinstance(software, list):
                # Query for multiple software names
                for s in software:
                    query = Software.get(Software.software_name == s)
                    results.append(query)
            else:
                # Query for a single software name
                results.append(Software.get(Software.software_name == software))

            if not results:
                return None, "No software found"

            # Include all if no specific columns are selected
            if not include:
                include = [column.name for column in Software.__table__.columns]

            for col in include:
                if col in exclude:
                    include.remove(col)

            results_dict = [
                {col: getattr(result, col) for col in include} for result in results
            ]

            return results_dict, None

        except Exception as e:
            print("Error: " + str(e))
            return None, str(e)


##########################
# Generate API Key Route #
##########################
@app.route("/apikey", methods=["GET", "POST"])
# @require_login - enable once plugged in
def api_keygen():
    form = APIKeyForm()
    api_key = "This is an API Key"
    if form.validate_on_submit():
        #     # Generate Alert for Form Success

        #     # Generate API Key
        api_key = secrets.token_urlsafe(32)

    #     # Store Data in Database
    #     user = User(first_name=form.first_name.data, last_name=form.last_name.data,
    #                    email=form.email.data, organization=form.organization.data,
    #                    api_key=api_key)
    #     db.session.add(user)
    #     db.session.commit()
    return render_template(
        "api_keygen.html", title="Generate API Key", form=form, api_key=api_key
    )
