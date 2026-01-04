import os
from datetime import datetime, timedelta, timezone

import boto3


def get_boto3_session():
    region = os.getenv("AWS_REGION", "us-east-1")
    return boto3.Session(region_name=region)


def fetch_aws_costs(start_date: datetime, end_date: datetime):
    session = get_boto3_session()
    ce = session.client("ce")
    response = ce.get_cost_and_usage(
        TimePeriod={
            "Start": start_date.strftime("%Y-%m-%d"),
            "End": end_date.strftime("%Y-%m-%d"),
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    rows = []
    for result in response.get("ResultsByTime", []):
        day = result["TimePeriod"]["Start"]
        for group in result.get("Groups", []):
            service = group["Keys"][0]
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            rows.append({
                "date": day,
                "service": service,
                "cost": amount,
            })
    return rows


def fetch_aws_ec2_cpu(instance_id: str, hours: int = 168):
    session = get_boto3_session()
    cw = session.client("cloudwatch")
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    response = cw.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=start,
        EndTime=end,
        Period=3600,
        Statistics=["Average"],
    )
    points = []
    for p in sorted(response.get("Datapoints", []), key=lambda x: x["Timestamp"]):
        points.append({
            "timestamp": p["Timestamp"].isoformat(),
            "value": float(p["Average"]),
        })
    return points
