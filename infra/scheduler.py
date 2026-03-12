import base64
import json
import pulumi
import pulumi_gcp as gcp

_TIMEZONE = "Europe/Madrid"
_STOP_SCHEDULE = "0 0 * * *"
_START_SCHEDULE = "0 8 * * *"

_DB_STOP_BODY = base64.b64encode(
    json.dumps({"settings": {"activationPolicy": "NEVER"}}).encode()
).decode()

_DB_START_BODY = base64.b64encode(
    json.dumps({"settings": {"activationPolicy": "ALWAYS"}}).encode()
).decode()

_CLOUDRUN_STOP_BODY = base64.b64encode(
    json.dumps({"template": {"scaling": {"minInstanceCount": 0}}}).encode()
).decode()

_CLOUDRUN_START_BODY = base64.b64encode(
    json.dumps({"template": {"scaling": {"minInstanceCount": 1}}}).encode()
).decode()

_CLOUDRUN_SCALE_UPDATE_MASK = "template.scaling.minInstanceCount"


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
            body=_DB_STOP_BODY,
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
            body=_DB_START_BODY,
            headers={"Content-Type": "application/json"},
            oauth_token=gcp.cloudscheduler.JobHttpTargetOauthTokenArgs(
                service_account_email=scheduler_sa.email,
            ),
        ),
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )


def create_cloudrun_schedule(
    project: str,
    region: str,
    service: gcp.cloudrunv2.Service,
    runner_service_account: gcp.serviceaccount.Account,
    api_deps: list | None = None,
) -> None:
    scheduler_sa = gcp.serviceaccount.Account(
        "bonsai-sensei-run-scheduler",
        account_id="bonsai-sensei-run-scheduler",
        display_name="Bonsai Sensei Cloud Run Scheduler",
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )

    gcp.projects.IAMMember(
        "bonsai-sensei-run-scheduler-developer",
        project=project,
        role="roles/run.developer",
        member=scheduler_sa.email.apply(lambda email: f"serviceAccount:{email}"),
    )

    gcp.serviceaccount.IAMMember(
        "bonsai-sensei-run-scheduler-sa-user",
        service_account_id=runner_service_account.name,
        role="roles/iam.serviceAccountUser",
        member=scheduler_sa.email.apply(lambda email: f"serviceAccount:{email}"),
    )

    service_api_url = pulumi.Output.all(project, region, service.name).apply(
        lambda args: (
            f"https://run.googleapis.com/v2/projects/{args[0]}/locations/{args[1]}"
            f"/services/{args[2]}?updateMask={_CLOUDRUN_SCALE_UPDATE_MASK}"
        )
    )

    gcp.cloudscheduler.Job(
        "bonsai-sensei-run-stop",
        name="bonsai-sensei-run-stop",
        region=region,
        schedule=_STOP_SCHEDULE,
        time_zone=_TIMEZONE,
        http_target=gcp.cloudscheduler.JobHttpTargetArgs(
            uri=service_api_url,
            http_method="PATCH",
            body=_CLOUDRUN_STOP_BODY,
            headers={"Content-Type": "application/json"},
            oauth_token=gcp.cloudscheduler.JobHttpTargetOauthTokenArgs(
                service_account_email=scheduler_sa.email,
            ),
        ),
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )

    gcp.cloudscheduler.Job(
        "bonsai-sensei-run-start",
        name="bonsai-sensei-run-start",
        region=region,
        schedule=_START_SCHEDULE,
        time_zone=_TIMEZONE,
        http_target=gcp.cloudscheduler.JobHttpTargetArgs(
            uri=service_api_url,
            http_method="PATCH",
            body=_CLOUDRUN_START_BODY,
            headers={"Content-Type": "application/json"},
            oauth_token=gcp.cloudscheduler.JobHttpTargetOauthTokenArgs(
                service_account_email=scheduler_sa.email,
            ),
        ),
        opts=pulumi.ResourceOptions(depends_on=api_deps or []),
    )
