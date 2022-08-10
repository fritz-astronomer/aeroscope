"""
Google Cloud Composer - https://cloud.google.com/composer/docs/concepts/plugins
AWS Managed Apache Airflow - https://docs.aws.amazon.com/mwaa/latest/userguide/configuring-dag-import-plugins.html
"""
import base64
import json
import logging
import socket
from contextlib import redirect_stdout, redirect_stderr
from json import JSONDecodeError
from typing import Any, Dict, List, Union

from airflow.plugins_manager import AirflowPlugin
from flask import Blueprint
from flask_appbuilder import expose, BaseView as AppBuilderBaseView

bp = Blueprint(
    "aeroscope",
    __name__,
    template_folder="templates",  # registers airflow/plugins/templates as a Jinja template folder
    static_folder="static",
    static_url_path="/static/aeroscope",
)


def clean_airflow_report_output(log_string: str) -> Union[dict, str]:
    r"""Look for the magic string from the Airflow report and then decode the base64 and convert to json
    Or return output as a list, trimmed and split on newlines
    >>> clean_airflow_report_output('INFO 123 - xyz - abc\n\n\nERROR - 1234\n%%%%%%%\naGVsbG8gd29ybGQ=')
    'hello world'
    >>> clean_airflow_report_output('INFO 123 - xyz - abc\n\n\nERROR - 1234\n%%%%%%%\neyJvdXRwdXQiOiAiaGVsbG8gd29ybGQifQ==')
    {'output': 'hello world'}
    """
    log_lines = log_string.split("\n")
    enumerated_log_lines = list(enumerate(log_lines))
    found_i = -1
    for i, line in enumerated_log_lines:
        if "%%%%%%%" in line:
            found_i = i + 1
            break
    if found_i != -1:
        output = base64.decodebytes("\n".join(log_lines[found_i:]).encode("utf-8")).decode("utf-8")
        try:
            return json.loads(output)
        except JSONDecodeError:
            return get_json_or_clean_str(output)
    else:
        return get_json_or_clean_str(log_string)


def get_json_or_clean_str(o: str) -> Union[List[Any], Dict[Any, Any], Any]:
    """Either load JSON (if we can) or strip and split the string, while logging the error"""
    try:
        return json.loads(o)
    except (JSONDecodeError, TypeError) as e:
        log.debug(e)
        log.debug(o)
        return o.strip()


log = logging.getLogger(__name__)


# Creating a flask appbuilder BaseView
class Aeroscope(AppBuilderBaseView):
    default_view = "aeroscope"

    @expose("/")
    def aeroscope(self):
        import runpy
        from urllib.request import urlretrieve as u
        import io

        a = 'airflow_report.pyz'
        u('https://github.com/astronomer/telescope/releases/latest/download/airflow_report.pyz', a)
        s = io.StringIO()
        with redirect_stdout(s), redirect_stderr(s):
            runpy.run_path(a)
        return {
            "local": {
                f"aeroscope_{socket.gethostname()}": {
                    "airflow_report": clean_airflow_report_output(s.getvalue())
                }
            }
        }


v_appbuilder_view = Aeroscope()
v_appbuilder_package = {
    "name": "View Results",
    "category": "Aeroscope",
    "view": v_appbuilder_view,
}


# Defining the plugin class
class AirflowTestPlugin(AirflowPlugin):
    name = "aeroscope"
    hooks = []
    macros = []
    flask_blueprints = [bp]
    appbuilder_views = [{
        "name": "View Results",
        "category": "Aeroscope",
        "view": v_appbuilder_view,
    },
        # {
        # "name": "Send Results",
        # "category": "Aeroscope",
        # "view": v_appbuilder_view,
        # }
    ]
    appbuilder_menu_items = []
    global_operator_extra_links = []
    operator_extra_links = []
