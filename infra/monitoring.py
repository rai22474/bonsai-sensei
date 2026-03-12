import json
import pulumi
import pulumi_gcp as gcp

_VERTEX_RESOURCE_TYPE = "aiplatform.googleapis.com/PublisherModel"
_CLOUDRUN_RESOURCE_TYPE = "cloud_run_revision"
_ALIGNMENT_PERIOD = "60s"


def _dataset(
    metric_type: str,
    resource_type: str,
    aligner: str = "ALIGN_RATE",
    reducer: str = "REDUCE_SUM",
    group_by: list | None = None,
    plot_type: str = "LINE",
    legend: str = "",
) -> dict:
    return {
        "timeSeriesQuery": {
            "timeSeriesFilter": {
                "filter": f'metric.type="{metric_type}" resource.type="{resource_type}"',
                "aggregation": {
                    "alignmentPeriod": _ALIGNMENT_PERIOD,
                    "perSeriesAligner": aligner,
                    "crossSeriesReducer": reducer,
                    "groupByFields": group_by or [],
                },
            },
        },
        "plotType": plot_type,
        "legendTemplate": legend,
        "minAlignmentPeriod": _ALIGNMENT_PERIOD,
    }


def _tile(x: int, y: int, width: int, height: int, title: str, datasets: list, y_label: str = "") -> dict:
    return {
        "xPos": x,
        "yPos": y,
        "width": width,
        "height": height,
        "widget": {
            "title": title,
            "xyChart": {
                "dataSets": datasets,
                "timeshiftDuration": "0s",
                "yAxis": {"label": y_label, "scale": "LINEAR"},
            },
        },
    }


def create_dashboard(api_deps: list | None = None) -> gcp.monitoring.Dashboard:
    tiles = [
        _tile(
            0, 0, 6, 4,
            title="LLM Calls / min",
            y_label="calls/min",
            datasets=[
                _dataset(
                    "aiplatform.googleapis.com/publisher/online_serving/request_count",
                    _VERTEX_RESOURCE_TYPE,
                    legend="Requests",
                ),
            ],
        ),
        _tile(
            6, 0, 6, 4,
            title="LLM Invocation Latency (ms)",
            y_label="ms",
            datasets=[
                _dataset(
                    "aiplatform.googleapis.com/publisher/online_serving/model_invocation_latencies",
                    _VERTEX_RESOURCE_TYPE,
                    aligner="ALIGN_PERCENTILE_99",
                    reducer="REDUCE_MEAN",
                    legend="p99",
                ),
                _dataset(
                    "aiplatform.googleapis.com/publisher/online_serving/model_invocation_latencies",
                    _VERTEX_RESOURCE_TYPE,
                    aligner="ALIGN_PERCENTILE_50",
                    reducer="REDUCE_MEAN",
                    legend="p50",
                ),
            ],
        ),
        _tile(
            0, 4, 6, 4,
            title="Token Usage / min",
            y_label="tokens/min",
            datasets=[
                _dataset(
                    "aiplatform.googleapis.com/publisher/online_serving/token_count",
                    _VERTEX_RESOURCE_TYPE,
                    group_by=["metric.labels.token_type"],
                    plot_type="STACKED_BAR",
                    legend="${metric.labels.token_type}",
                ),
            ],
        ),
        _tile(
            6, 4, 6, 4,
            title="Time to First Token (ms)",
            y_label="ms",
            datasets=[
                _dataset(
                    "aiplatform.googleapis.com/publisher/online_serving/first_token_latencies",
                    _VERTEX_RESOURCE_TYPE,
                    aligner="ALIGN_PERCENTILE_99",
                    reducer="REDUCE_MEAN",
                    legend="p99",
                ),
                _dataset(
                    "aiplatform.googleapis.com/publisher/online_serving/first_token_latencies",
                    _VERTEX_RESOURCE_TYPE,
                    aligner="ALIGN_PERCENTILE_50",
                    reducer="REDUCE_MEAN",
                    legend="p50",
                ),
            ],
        ),
        _tile(
            0, 8, 6, 4,
            title="Cloud Run Requests / s",
            y_label="req/s",
            datasets=[
                _dataset(
                    "run.googleapis.com/request_count",
                    _CLOUDRUN_RESOURCE_TYPE,
                    legend="Requests",
                ),
            ],
        ),
        _tile(
            6, 8, 6, 4,
            title="Cloud Run Active Instances",
            y_label="instances",
            datasets=[
                _dataset(
                    "run.googleapis.com/container/instance_count",
                    _CLOUDRUN_RESOURCE_TYPE,
                    aligner="ALIGN_MEAN",
                    reducer="REDUCE_SUM",
                    legend="Instances",
                ),
            ],
        ),
    ]

    return gcp.monitoring.Dashboard(
        "bonsai-sensei-dashboard",
        dashboard_json=json.dumps({
            "displayName": "Bonsai Sensei - Model Metrics",
            "mosaicLayout": {
                "columns": 12,
                "tiles": tiles,
            },
        }),
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )
