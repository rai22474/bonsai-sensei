import base64
import json
import pulumi
import pulumi_gcp as gcp

_TIMEZONE = "Europe/Madrid"
_STOP_SCHEDULE = "0 0 * * *"
_START_SCHEDULE = "0 8 * * *"

_STOP_BODY = base64.b64encode(
    json.dumps({"settings": {"activationPolicy": "NEVER"}}).encode()
).decode()

_START_BODY = base64.b64encode(
    json.dumps({"settings": {"activationPolicy": "ALWAYS"}}).encode()
).decode()


def create_db_schedule(
    project: str,
    region: str,
    instance: gcp.sql.DatabaseInstance,
    api_deps: list | None = None,
) -> None:
    scheduler_sa = gcp.serviceaccount.Account(
        "bonsai-sensei-db-scheduler",
        account_id="bonsai-sensei-db-scheduler",
        display_name="Bonsai Sensei DB Scheduler",
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )

    gcp.projects.IAMMember(
        "bonsai-sensei-db-scheduler-editor",
        project=project,
        role="roles/cloudsql.editor",
        member=scheduler_sa.email.apply(lambda email: f"serviceAccount:{email}"),
    )

    instance_url = pulumi.Output.all(project, instance.name).apply(
        lambda args: f"https://sqladmin.googleapis.com/v1/projects/{args[0]}/instances/{args[1]}"
    )

    gcp.cloudscheduler.Job(
        "bonsai-sensei-db-stop",
        name="bonsai-sensei-db-stop",
        region=region,
        schedule=_STOP_SCHEDULE,
        time_zone=_TIMEZONE,
        http_target=gcp.cloudscheduler.JobHttpTargetArgs(
            uri=instance_url,
            http_method="PATCH",
            body=_STOP_BODY,
            headers={"Content-Type": "application/json"},
            oauth_token=gcp.cloudscheduler.JobHttpTargetOauthTokenArgs(
                service_account_email=scheduler_sa.email,
            ),
        ),
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )

    gcp.cloudscheduler.Job(
        "bonsai-sensei-db-start",
        name="bonsai-sensei-db-start",
        region=region,
        schedule=_START_SCHEDULE,
        time_zone=_TIMEZONE,
        http_target=gcp.cloudscheduler.JobHttpTargetArgs(
            uri=instance_url,
            http_method="PATCH",
            body=_START_BODY,
            headers={"Content-Type": "application/json"},
            oauth_token=gcp.cloudscheduler.JobHttpTargetOauthTokenArgs(
                service_account_email=scheduler_sa.email,
            ),
        ),
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )
