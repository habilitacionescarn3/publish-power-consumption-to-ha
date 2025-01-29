import csv
import logging
import os
import requests

import boto3
from smart_open import open


log = logging.getLogger()
log.setLevel(logging.INFO)

HA_BASE_URL = os.environ["HA_BASE_URL"]
HA_TOKEN = os.environ["HA_TOKEN"]
MONTHS = int(os.environ["MONTHS"])


def publish_to_ha(bucket: str, key: str) -> bool:
    """Publishes power consumption to Home Assistant"""
    rows = read_csv(bucket, key)

    if rows:
        log.info(f"Sending last {MONTHS} rows to HA")

        headers = {
            "Authorization": f"Bearer {HA_TOKEN}",
            "content-type": "application/json",
        }
        var_name = "monthly_energy"
        state = "1"  # Dummy state
        data = {
            "state": str(state),
            "attributes": {
                "entries": rows,
            },
        }

        try:
            endpoint = f"api/states/variable.{var_name}"
            url = f"{HA_BASE_URL}/{endpoint}"
            r = requests.post(url=url, headers=headers, json=data)
            r.raise_for_status()
            log.info(r.json())
            return True
        except requests.exceptions.ConnectionError as e:
            log.error(e)
            return False
    else:
        log.error(f"An error occurred while reading s3://{bucket}/{key}")
        return False


def read_csv(bucket: str, key: str) -> list:
    """Reads the last MONTHS rows of a CSV file"""
    log.info(f"Reading file s3://{bucket}/{key}")
    s3_client = boto3.client("s3", region_name="eu-west-3")
    list_dict_rows = []
    with open(
        f"s3://{bucket}/{key}", "r", transport_params={"client": s3_client}
    ) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        list_dict_rows = [dict(d) for d in csv_reader][-MONTHS:]
        list_dict_rows.reverse()  # We want the last row at the top
    return list_dict_rows
