# This is the class you derive to create a plugin
from airflow.plugins_manager import AirflowPlugin

from flask import Blueprint
from flask_appbuilder import expose, BaseView as AppBuilderBaseView

from plugins import airflow_report

bp = Blueprint(
    "aeroscope",
    __name__,
    template_folder="templates",  # registers airflow/plugins/templates as a Jinja template folder
    static_folder="static",
    static_url_path="/static/test_plugin",
)


# Creating a flask appbuilder BaseView
class Aeroscope(AppBuilderBaseView):
    default_view = "aeroscope"

    @expose("/")
    def aeroscope(self):
        return airflow_report.main()


v_appbuilder_view = Aeroscope()
v_appbuilder_package = {
    "name": "View Results",
    "category": "Aeroscope",
    "view": v_appbuilder_view,
}


# Defining the plugin class
class AirflowTestPlugin(AirflowPlugin):
    name = "test_plugin"
    hooks = []
    macros = []
    flask_blueprints = [bp]
    appbuilder_views = [{
        "name": "View Results",
        "category": "Aeroscope",
        "view": v_appbuilder_view,
    }, {
        "name": "Send Results",
        "category": "Aeroscope",
        "view": v_appbuilder_view,
    }]
    appbuilder_menu_items = []
    global_operator_extra_links = []
    operator_extra_links = []
