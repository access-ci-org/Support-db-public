from flask import Flask, jsonify, make_response
from flask_restful import Api, Resource
from config import Config
from app.app_logging import logger


logger.info('Start app')

#Setup flask application
app = Flask(__name__)
app.config.from_object(Config)
app.json.sort_keys = False  # Ensure jsonify in api won't sort keys

from app import routes, errors

# Add import of new versions of the API as they are created
from app.api import Api_0, require_api_key
from app.api_0_1 import API_0_1
api = Api(app)

# Map API version to the appropriate class
api_versions = {
    "api=API_0": Api_0,
    "API_0": Api_0,
    "API_0.1": API_0_1,
    "api=API_0.1": API_0_1
    # You can add more versions as needed
}


# Dynamically select the API version based on the URL
class VersionedAPI(Resource):
    @require_api_key
    def get(self, api_version, api_key, query):

        # Check if the api_version exists in the map
        api_class = api_versions.get(api_version)
        if api_class is None:
            return make_response(
                jsonify({"message": f"API version '{api_version}' not found."}), 404
            )

        # If the version exists, instantiate the class and call its method
        api_instance = api_class()
        return api_instance.get(query, api_key)


# Add the versioned API route to Flask
api.add_resource(VersionedAPI, "/<api_version>/<api_key>/<query>") 

#Link for API_0: url/api_ver/api_key/query -> url/API_0/api_key/software=7z


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
