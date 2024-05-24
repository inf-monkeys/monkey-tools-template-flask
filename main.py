from flask import Flask, request, jsonify
import requests
from flask_restx import Api, Resource, fields
import traceback
import logging

app = Flask(__name__)
api = Api(
    app,
    version="1.0",
    title="Monkeys Weather API",
    description="Monkeys Weather API",
)

weather_ns = api.namespace("weather", description="Weather API")


class NoSuccessfulRequestLoggingFilter(logging.Filter):
    def filter(self, record):
        return "GET /" not in record.getMessage()


# 获取 Flask 的默认日志记录器
log = logging.getLogger("werkzeug")
# 创建并添加过滤器
log.addFilter(NoSuccessfulRequestLoggingFilter())


@app.before_request
def before_request():
    request.app_id = request.headers.get("x-monkeys-appid")
    request.user_id = request.headers.get("x-monkeys-userid")
    request.team_id = request.headers.get("x-monkeys-teamid")
    request.workflow_id = request.headers.get("x-monkeys-workflowid")
    request.workflow_instance_id = request.headers.get("x-monkeys-workflow-instanceid")


@api.errorhandler(Exception)
def handle_exception(error):
    return {'message': str(error)}, 500


@app.get("/manifest.json")
def get_manifest():
    return {
        "schema_version": "v1",
        "display_name": "My Awesome Weather Tool",
        "namespace": "monkey_tools_my_awesome_weather_tool",
        "auth": {"type": "none"},
        "api": {"type": "openapi", "url": "/swagger.json"},
        "contact_email": "dev@inf-monkeys.com",
    }



@weather_ns.route("/")
class WeatherLookUpResource(Resource):
    @weather_ns.doc("get_weather")
    @weather_ns.vendor(
        {
            "x-monkey-tool-name": "get_weather",
            "x-monkey-tool-categories": ["weather"],
            "x-monkey-tool-display-name": "Get Weather",
            "x-monkey-tool-description": "Get Weather By Latitude and Longitude",
            "x-monkey-tool-icon": "emoji:💿:#e58c3a",
            "x-monkey-tool-input": [
                {
                    "displayName": "Latitude",
                    "name": "latitude",
                    "type": "number",
                    "required": True,
                },
                {
                    "displayName": "Longitude",
                    "name": "longitude",
                    "type": "number",
                    "required": True,
                }
            ],
            "x-monkey-tool-output": [
               {
                "displayName": "Latitude",
                "name": "latitude",
                "type": "number",
               },
               {
                "displayName": "Longitude",
                "name": "longitude",
                "type": "number",
               },
               {
                "displayName": "Generation Time",
                "name": "generationtime_ms",
                "type": "number",
               },
               {
                "displayName": "UTC Offset",
                "name": "utc_offset_seconds",
                "type": "number",
               },
               {
                "displayName": "Timezone",
                "name": "timezone",
                "type": "string",
               },
               {
                "displayName": "Timezone Abbreviation",
                "name": "timezone_abbreviation",
                "type": "string",
               },
               {
                "displayName": "Elevation",
                "name": "elevation",
                "type": "number",
               },
               {
                "displayName": "Current Units",
                "name": "current_units",
                "type": "object",
               },
               {
                "displayName": "Current",
                "name": "current",
                "type": "object",
               },
               {
                "displayName": "Hourly Units",
                "name": "hourly_units",
                "type": "object",
               },
               {
                "displayName": "Hourly",
                "name": "hourly",
                "type": "object",
               }
            ],
            "x-monkey-tool-extra": {
                "estimateTime": 5,
            },
        }
    )
    @weather_ns.expect(
        weather_ns.model(
            "GetWeatherRequest",
            {
                "latitude": fields.Float(required=True, description="Latitude"),
                "longitude": fields.Float(required=True, description="Longitude"),
            },
        )
    )
    @weather_ns.response(
        200,
        "Success",
        weather_ns.model(
            "GetWeatherResult",
            {
                "latitude": fields.Float(description="Latitude"),
                "longitude": fields.Float(description="Longitude"),
                "generationtime_ms": fields.Float(description="Generation Time"),
                "utc_offset_seconds": fields.Integer(description="UTC Offset"),
                "timezone": fields.String(description="Timezone"),
                "timezone_abbreviation": fields.String(description="Timezone Abbreviation"),
                "elevation": fields.Float(description="Elevation"),
                "current_units": fields.Nested(
                    weather_ns.model(
                        "CurrentUnits",
                        {
                            "time": fields.String(description="Time"),
                            "interval": fields.String(description="Interval"),
                            "temperature_2m": fields.String(description="Temperature 2m"),
                            "wind_speed_10m": fields.String(description="Wind Speed 10m"),
                        },
                    )
                ),
                "current": fields.Nested(
                    weather_ns.model(
                        "Current",
                        {
                            "time": fields.String(description="Time"),
                            "interval": fields.Integer(description="Interval"),
                            "temperature_2m": fields.Float(description="Temperature 2m"),
                            "wind_speed_10m": fields.Float(description="Wind Speed 10m"),
                        },
                    )
                ),
                "hourly_units": fields.Nested(
                    weather_ns.model(
                        "HourlyUnits",
                        {
                            "time": fields.String(description="Time"),
                            "temperature_2m": fields.String(description="Temperature 2m"),
                            "relative_humidity_2m": fields.String(description="Relative Humidity 2m"),
                            "wind_speed_10m": fields.String(description="Wind Speed 10m"),
                        },
                    )
                ),
                "hourly": fields.Nested(
                    weather_ns.model(
                        "Hourly",
                        {
                            "time": fields.List(fields.String, description="Time"),
                            "temperature_2m": fields.List(fields.Float, description="Temperature 2m"),
                            "relative_humidity_2m": fields.List(fields.Integer, description="Relative Humidity 2m"),
                            "wind_speed_10m": fields.List(fields.Float, description="Wind Speed 10m"),
                        },
                    )
                ),
            },
        ),
    )
    def post(self):
        """
        Example output:
{
    "latitude": 52.52,
    "longitude": 13.419998,
    "generationtime_ms": 0.1291036605834961,
    "utc_offset_seconds": 0,
    "timezone": "GMT",
    "timezone_abbreviation": "GMT",
    "elevation": 38.0,
    "current_units": {
        "time": "iso8601",
        "interval": "seconds",
        "temperature_2m": "°C",
        "wind_speed_10m": "km/h"
    },
    "current": {
        "time": "2024-04-12T10:15",
        "interval": 900,
        "temperature_2m": 17.5,
        "wind_speed_10m": 16.4
    },
    "hourly_units": {
        "time": "iso8601",
        "temperature_2m": "°C",
        "relative_humidity_2m": "%",
        "wind_speed_10m": "km/h"
    },
    "hourly": {
        "time": [
            "2024-04-12T00:00",
            "2024-04-12T01:00",
            "2024-04-12T02:00",
            "2024-04-12T03:00",
            "2024-04-12T04:00",
            "2024-04-12T05:00",
        ],
        "temperature_2m": [
            13.1,
            12.9,
            12.6,
            12.9,
            12.8,
            12.9,
        ],
        "relative_humidity_2m": [
            78,
            80,
            82,
            81,
            81,
            81,
        ],
        "wind_speed_10m": [
            3.6,
            5.9,
            7.2,
            7.7,
            7.4,
            6.4,
        ]
    }
}
        """
        json = request.json
        latitude = json.get("latitude")
        longitude = json.get("longitude")
        api = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
        r = requests.get(api)
        return r.json()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
