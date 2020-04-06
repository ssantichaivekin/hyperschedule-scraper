"""
Module containing the Hyperschedule backend Flask app.
"""

import os
import functools

import flask
import flask_cors

import hyperschedule
import hyperschedule.worker as worker
import hyperschedule.auth as token_auth

from hyperschedule.util import Unset

import firebase_admin
from firebase_admin import auth, credentials, firestore

# Hyperschedule Flask app.
app = flask.Flask("hyperschedule")
flask_cors.CORS(app)

# Initialize Firebase app
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="FIREBASE_CREDENTIALS_PATH"
firebase = firebase.FirebaseApplication("hyperschedule-course-info.appspot.com")

cred = credentials.Certificate(os.environ.get("FIREBASE_CREDENTIALS_PATH"))
firebase_admin.initialize_app(cred)

# <http://librelist.com/browser/flask/2011/8/8/add-no-cache-to-response/#952cc027cf22800312168250e59bade4>
def nocache(f):
    """
    Decorator for a Flask view that disables caching.
    """

    def new_func(*args, **kwargs):
        resp = flask.make_response(f(*args, **kwargs))
        resp.cache_control.no_cache = True
        return resp

    return functools.update_wrapper(new_func, f)


class APIError(Exception):
    """
    Exception that is turned into an error response from the API.
    """

    pass


def api_response(data):
    """
    Return a JSONified API response from the given dictionary.
    """
    return flask.jsonify({"error": None, **data,})


@app.errorhandler(APIError)
def handle_api_error(error):
    """
    Return a JSONified API error response with the given error
    message.
    """
    return flask.jsonify({"error": str(error),})


@app.route("/")
def view_index():
    """
    View for the index page redirecting users to
    https://hyperschedule.io.
    """
    return flask.send_from_directory(hyperschedule.ROOT_DIR, "html/index.html")


@app.route("/api/v3/courses")
@nocache
def view_api_v3():
    """
    View for the Hyperschedule API used by the frontend to retrieve
    course information.
    """
    school = flask.request.args.get("school")
    if not school:
        raise APIError("request failed to specify school")
    if school not in ("cmc", "hmc", "pitzer", "pomona", "scripps"):
        raise APIError("unknown school: {}".format(repr(school)))
    since = flask.request.args.get("since")
    if not since:
        until, data = app.worker.get_current_data()
        if data is Unset:
            raise APIError("data not available yet")
        return api_response({"data": data, "until": until, "full": True})
    try:
        since = int(since)
    except ValueError:
        raise APIError("'since' not an integer: {}".format(repr(since)))
    diff, full, until = app.worker.get_diff_to_present(since)
    if diff is Unset:
        raise APIError("data not available yet")
    return api_response({"data": diff, "until": until, "full": full})

@app.route("/upload-syllabus", methods = ['POST'])
@nocache
def upload_syllabus():
    """
    A post method to upload course syllabus. The POST method requires a token
    and a syllabus pdf. It uploads the syllabus to Firebase and return success
    or failure.
    """
    token = flask.request.json.get("token")
    syllabusData = flask.request.json.get("syllabusDataDictionary")
    pdf = flask.request.get_data("PDFFile")

    if token_auth.verify_token(token) == True:
        
        # Upload syllabus
        # Incomplete file upload (untested)
        # TODO: find out how to create bucket for class only once
        # confirm that the PDF is in right location in storage
        # Store link to PDF in database
        # Discuss w/ Santi about currentCourseCode - 
        client = storage.Client()
        bucket = client.create_bucket(bucket_name)

        bucket = client.get_bucket('courseSyllabi/' + syllabusData[courseCode]) 
        # get_bucket needs to exist - how to create bucket just once?
        
        fileBlob = bucket.blob("/")

        fileBlob.upload_from_file(pdf) 

        raise NotImplementedError("Unted")


    
    # TODO: read syllabus to post method
    # TODO: implement syllabus upload to Firebase and its local copy
    raise NotImplementedError("Upload Syllabus feature not implemented")


app.worker = worker.HyperscheduleWorker()
app.worker.start()
